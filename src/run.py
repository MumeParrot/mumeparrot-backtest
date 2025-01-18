import os

from typing import List, Dict
from .const import StockRow, Result, Stat
from .utils import (
    read_chart,
    read_base_chart,
    moving_average,
    read_sahm,
    plot_with_rsi
)
from .configs import Config

from datetime import datetime, timedelta

MARKET_DAYS_PER_YEAR = 260

TERM = 40
SEED = 100000

AVG50_HISTORY = None
U50_RATES = None

CONFIG = None

def plot_graph(ticker: str):
    start = os.environ.get('START', '')
    end = os.environ.get('END', '')
    verbose = os.environ.get('VERBOSE', 0)

    chart = read_chart(ticker, start, end)
    plot_with_rsi(ticker, chart, 80, 40)
   

def test(ticker: str, 
         max_cycles: int,
         config: Config,
        ):

    start = os.environ.get('START', '')
    end = os.environ.get('END', '')
    verbose = os.environ.get('VERBOSE', 0)

    global CONFIG
    CONFIG = config

    chart = read_chart(ticker, start, end)
    no_base_chart = False
    try:
        base_chart = read_base_chart(ticker, start, end)
    except:
        base_chart = chart
        no_base_chart = True

    global AVG50_HISTORY
    AVG50_HISTORY = moving_average(chart, 50)
    sahm = read_sahm()

    global U50_RATES
    U50_RATES = compute_u50_rates(chart)

    # Split all-time chart to a number of fractions
    charts = [chart[i : i + TERM] 
              for i in range(len(chart) - TERM)]
    base_charts = [base_chart[i : i + TERM] 
                   for i in range(len(base_chart) - TERM)]

    _charts = charts
    _base_charts = base_charts

    stats: List[Stat] = []
    results: Dict[int, List[Result]] = {}

    print(f"======== Result for {ticker} ========")

    for c in range(max_cycles):
        results[c] = []

        # Simulate Mumae for all fractions of chart
        for chart, base_chart in zip(_charts, _base_charts):
            if (CONFIG.sahm_threshold != 0 
                and sahm[chart[0].date] > CONFIG.sahm_threshold):
                continue

            res = simulate(chart, base_chart, c, no_base_chart)
            results[c].append(res)

        # Rebuild fractions by extending the fractions that have failed
        _charts = []
        _base_charts = []
        for res in results[c]:
            if not res.sold:
                idx = [c[0].date for c in charts].index(res.start)

                # Check boundary condition
                if idx + (c + 1) * TERM >= len(charts):
                    continue

                extended_chart = []
                extended_base_chart = []

                for i in range(c + 2):
                    extended_chart += charts[idx + i * TERM]
                    extended_base_chart += base_charts[idx + i * TERM]

                _charts.append(extended_chart)
                _base_charts.append(extended_base_chart)

        total = len(results[c])

        # Compute the number of
        #  1) better than base & sold
        #  2) worse than base & sold
        #  3) better than base & not sold
        #  4) worse than base & not sold

        btb_s = len([r for r in results[c] if r.sold and r.ror > r.base_ror])
        wtb_s = len([r for r in results[c] if r.sold and r.ror <= r.base_ror])
        btb_ns = len([r for r in results[c] if not r.sold and r.ror > r.base_ror])
        wtb_ns = len([r for r in results[c] if not r.sold and r.ror <= r.base_ror])

        rate_of_better_sold = btb_s / total if total != 0 else 0
        rate_of_sold = (btb_s + wtb_s) / total if total != 0 else 0
        
        avg_days_of_sold = sum([r.days for r in results[c] if r.sold]) / (btb_s + wtb_s) if btb_s + wtb_s > 0 else 0
        avg_ror_of_sold = sum([r.ror for r in results[c] if r.sold]) / (btb_s + wtb_s) if btb_s + wtb_s > 0 else 0

        if btb_ns + wtb_ns > 0:
            avg_ror_of_not_sold = sum([r.ror for r in results[c] if not r.sold]) / (btb_ns + wtb_ns)
        else:
            avg_ror_of_not_sold = 0

        stat = Stat(
            rate_of_better_sold,
            rate_of_sold,
            avg_days_of_sold,
            avg_ror_of_sold,
            avg_ror_of_not_sold if c == max_cycles - 1 else 0
        )

        stats.append(stat)

        if verbose:
           print(f"""[Cycle {c}]
rate_of_better_sold: {rate_of_better_sold * 100:.2f}%\trate_of_sold:    {rate_of_sold * 100:.2f}%
avg_days_of_sold:    {avg_days_of_sold:.0f}\tavg_ror_of_sold: {avg_ror_of_sold * 100:.2f}%"""
                 + (f"\n avg_ror_of_not_sold: {avg_ror_of_not_sold * 100:.2f}%" if c == max_cycles - 1 else ""))

    fail_rate = compute_fail_rate(stats, max_cycles)
    avg_ror_per_year = compute_avg_ror(results, max_cycles)

    print(f'Fail rate: {fail_rate * 100:.2f}%')
    print(f'Average RoR per year: {avg_ror_per_year * 100:.2f}%')

    return results

def simulate(chart: List[StockRow], base_chart: List[StockRow],
             cycle: int, no_base_chart=False) -> Result:
    daily_seed = SEED / TERM
    base_start_price = base_chart[0].close_price

    remaining_seed = SEED
    invested_seed = 0
    stock_qty = 0
    avg_price = 0

    sold = False
    days = 0
    exhaust_cnt = 0

    decline_score = 0

    stop_loss = False

    for c, b in zip(chart, base_chart):
        u50_rate = U50_RATES[c.date]

        margin = CONFIG.margin 
        margin_lose = CONFIG.margin_lose * max(u50_rate - 0.5, 0) / 0.5
        margin -= margin_lose

        margin_window = CONFIG.margin_window * (remaining_seed / SEED)
        margin += margin_window

        if stock_qty > 0 and c.close_price > avg_price * (1 + margin):
            base_end_price = b.close_price
            sell_price = avg_price * (1 + margin)
            sold = True

            break

        dqty = (int(daily_seed / c.close_price) if remaining_seed > daily_seed
                else int(remaining_seed / c.close_price))
        burst_threshold = CONFIG.burst_threshold * (1 - 0.8 * u50_rate)

        if (remaining_seed > CONFIG.burst_rate * daily_seed 
            and c.rsi < burst_threshold):
            dqty *= CONFIG.burst_rate

        rsi_threshold = CONFIG.rsi_threshold

        if dqty > 0 and c.rsi <= rsi_threshold:
            invested_seed += dqty * c.close_price
            remaining_seed -= dqty * c.close_price

            stock_qty += dqty
            avg_price = invested_seed / stock_qty

        elif dqty == 0:
            if cycle > exhaust_cnt:
                exhaust_cnt += 1

                sell_qty = max(stock_qty // 4, int(stock_qty * u50_rate))
                invested_seed -= sell_qty * avg_price
                remaining_seed += sell_qty * c.close_price
            
                stock_qty -= sell_qty

            else:
                base_end_price = b.close_price
                sell_price = c.close_price

                break

        base_end_price = b.close_price
        sell_price = c.close_price

        days += 1

        # decline_score *= days - 1
        # if (invested_seed / SEED) >= 0.4:
        #     decline_score += int(c.close_price <= avg_price)
        # else:
        #     decline_score += int(c.close_price > avg_price)
        # decline_score /= days

        # if (CONFIG.stoploss_threshold != 0 and not stop_loss
        #     and decline_score > CONFIG.stoploss_threshold):
        #     sell_qty = stock_qty // 2

        #     invested_seed -= sell_qty * avg_price
        #     remaining_seed += sell_qty * c.close_price
            
        #     stock_qty -= sell_qty

        #     stop_loss = True

    base_invested_seed = SEED * min(days, TERM) / TERM
    base_remaining_seed = SEED - base_invested_seed
    base_invest_ror = base_end_price / base_start_price
    base_ror = (base_invest_ror * base_invested_seed + base_remaining_seed) / SEED - 1

    ror = (sell_price * stock_qty + remaining_seed) / SEED - 1

    if no_base_chart:
        base_ror = ror

    return Result(chart[0].date, days, sold, ror, base_ror, u50_rate)

def compute_u50_rates(chart: List[StockRow]):
    u50_rates = {}
    
    u50_counters = []
    for c in chart:
        u50_counters.append(int(c.close_price < AVG50_HISTORY[c.date]))
        if len(u50_counters) > TERM:
            u50_counters.pop(0)

        u50_rates[c.date] = sum(u50_counters) / len(u50_counters)

    return u50_rates

def compute_avg_ror(results: Dict[int, List[Result]], max_cycles: int):
    tot_ror = 0
    tot_days = 0

    for c in range(max_cycles - 1):
        tot_ror += sum([r.ror for r in results[c] if r.sold])
        tot_days += sum([r.days for r in results[c] if r.sold])

    tot_ror += sum([r.ror for r in results[max_cycles - 1]]) 
    tot_days += sum([r.days if r.sold else max_cycles * TERM for r in results[max_cycles - 1]])

    return tot_ror / tot_days * MARKET_DAYS_PER_YEAR

def compute_fail_rate(stats: List[Stat], max_cycles: int) -> float:
    fail_rate = 1

    for s in stats:
        fail_rate *= (1 - s.rate_of_sold)

    return fail_rate

def get_ratio(chart: List[StockRow], filter):
    tot = len(chart)
    cnt = len([c for c in chart if filter(c)])

    return cnt / tot
