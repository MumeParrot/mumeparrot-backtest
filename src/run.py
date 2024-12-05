from typing import List

from .const import StockRow, Result, Stat
from .utils import (
    read_chart,
    read_base_chart,
    moving_average,
    read_sahm
)

MARKET_DAYS_PER_YEAR = 260

TERM = 40
SEED = 100000
MARGIN = 0.05
RSI_THRESHOLD = 80
BURST_THRESHOLD = 40
BURST_RATE = 1.5 # TODO
MARGIN_WINDOW = 0.1
LOSE_MARGIN = 0.1
BASE_MARGIN_LOSE = 0.05

AVG50_HISTORY = None

def test(ticker: str, 
         term: int, 
         seed: int, 
         margin: float,
         max_cycles: int,
         rsi_threshold: int,
         burst_threshold: int,
         burst_rate: float,
         margin_window: float,
         base_margin_lose: float,
         sahm_threshold: float,
        ):

    global TERM, SEED, MARGIN, RSI_THRESHOLD, BURST_THRESHOLD, BURST_RATE, MARGIN_WINDOW, BASE_MARGIN_LOSE
    TERM = term
    SEED = seed
    MARGIN = margin
    RSI_THRESHOLD = rsi_threshold
    BURST_THRESHOLD = burst_threshold
    BURST_RATE = burst_rate
    MARGIN_WINDOW = margin_window
    BASE_MARGIN_LOSE = base_margin_lose

    chart = read_chart(ticker, "", "")
    no_base_chart = False
    try:
        base_chart = read_base_chart(ticker, "", "")
    except:
        base_chart = chart
        no_base_chart = True

    global AVG50_HISTORY
    AVG50_HISTORY = moving_average(chart, 50)

    u50_rates = {i: [] for i in range(11)}

    # Split all-time chart to a number of fractions
    charts = [chart[i : i + TERM] 
              for i in range(len(chart) - TERM)]
    base_charts = [base_chart[i : i + TERM] 
                   for i in range(len(base_chart) - TERM)]

    sahm = read_sahm()

    _charts = charts
    _base_charts = base_charts

    # r_s_per_cycle = []
    # avg_ror_for_s_per_cycle = []
    # avg_days_for_s_per_cycle = []
    # avg_loss_for_ns_per_cycle = []

    stats: List[Stat] = []

    print(f"======== Result for {ticker} ========")

    for c in range(max_cycles):
        results: List[Result] = []

        # Simulate Mumae for all fractions of chart
        for chart, base_chart in zip(_charts, _base_charts):
            if sahm_threshold != 0 and sahm[chart[0].date] > sahm_threshold:
                continue

            u50_rate = get_ratio(chart,
                                 lambda s: s.close_price < AVG50_HISTORY[s.date])
            res = simulate(chart, base_chart, c, no_base_chart)

            u50_rates[int(u50_rate * 10)].append(res)
            results.append(res)

        # for i in range(0, 11):
        #     n = len(u50_rates[i])
        #     n_ns = len([r for r in u50_rates[i] if not r.sold])
        #     print(f'[{i * 10}%-{min(i, 9) * 10 + 10}%) {n_ns/n * 100:.2f}%')

        # Rebuild fractions by extending the fractions that have failed
        _charts = []
        _base_charts = []
        for res in results:
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

        total = len(results)

        # Compute the number of
        #  1) better than base & sold
        #  2) worse than base & sold
        #  3) better than base & not sold
        #  4) worse than base & not sold

        btb_s = len([r for r in results if r.sold and r.ror > r.base_ror])
        wtb_s = len([r for r in results if r.sold and r.ror <= r.base_ror])
        btb_ns = len([r for r in results if not r.sold and r.ror > r.base_ror])
        wtb_ns = len([r for r in results if not r.sold and r.ror <= r.base_ror])

        rate_of_better_sold = btb_s / total
        rate_of_sold = (btb_s + wtb_s) / total
        
        avg_days_of_sold = sum([r.days for r in results if r.sold]) / (btb_s + wtb_s)
        avg_ror_of_sold = sum([r.ror for r in results if r.sold]) / (btb_s + wtb_s)

        if btb_ns + wtb_ns > 0:
            avg_ror_of_not_sold = sum([r.ror for r in results if not r.sold]) / (btb_ns + wtb_ns)
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

        print(f"""[Cycle {c}]
 rate_of_better_sold: {rate_of_better_sold * 100:.2f}%\trate_of_sold:    {rate_of_sold * 100:.2f}%
 avg_days_of_sold:    {avg_days_of_sold:.0f}\tavg_ror_of_sold: {avg_ror_of_sold * 100:.2f}%"""
              + (f"\n avg_ror_of_not_sold: {avg_ror_of_not_sold * 100:.2f}%" if c == max_cycles - 1 else ""))

        # results_per_year = {}
        # for res in results:
        #     year = res.start.split('-')[0]
        #     results_per_year[year] = results_per_year.get(year, []) + [res]

        # for year, rs in results_per_year.items():
        #     n = len(rs)
        #     n_ns = len([r for r in rs if not r.sold])
        #     print(f'[{year}] {n_ns / n * 100:.2f}%')

        # rs = results_per_year['2021']
        # for r in rs:
        #     if not r.sold:
        #         print(r.start)
            

    avg_ror_per_year = 0
    remaining_days_for_cycle = MARKET_DAYS_PER_YEAR
    for c in range(max_cycles):
        rate_of_sold = stats[c].rate_of_sold
        avg_days_of_sold = stats[c].avg_days_of_sold
        avg_ror_of_sold = stats[c].avg_ror_of_sold

        avg_days_of_not_sold = 0
        prev_rate_of_not_sold = 1
        for s in stats[c + 1:]:
            avg_days_of_not_sold += (prev_rate_of_not_sold * 
                                     s.avg_days_of_sold * s.rate_of_sold)
            prev_rate_of_not_sold = prev_rate_of_not_sold * (1 - s.rate_of_sold)

        # If not sold at last cycle, then just assume selling all stocks at last day
        avg_days_of_not_sold += prev_rate_of_not_sold * (max_cycles * TERM)

        sold_days_in_cycle = (remaining_days_for_cycle * avg_days_of_sold * rate_of_sold /
                             (avg_days_of_sold * rate_of_sold + avg_days_of_not_sold * (1 - rate_of_sold)))

        avg_ror_per_year += sold_days_in_cycle * (avg_ror_of_sold / avg_days_of_sold)

        remaining_days_for_cycle -= sold_days_in_cycle
        if c == max_cycles - 1:
            avg_ror_per_year += remaining_days_for_cycle * (avg_ror_of_not_sold / avg_days_of_not_sold)

    fail_rate = 1
    for s in stats:
        fail_rate *= (1 - s.rate_of_sold)
    print(f'Fail rate: {fail_rate * 100:.2f}%')
    print(f'Average RoR per year: {avg_ror_per_year * 100:.2f}%')


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

    u50_cnt = 0
    u50_rate = 0

    for c, b in zip(chart, base_chart):
        base_margin = (MARGIN - BASE_MARGIN_LOSE * max(u50_rate - 0.5, 0) / 0.5 
                       if days > 10 else MARGIN)
        margin_window = MARGIN_WINDOW * (remaining_seed / SEED)
        margin = base_margin + margin_window

        if stock_qty > 0 and c.close_price > avg_price * (1 + margin):
            base_end_price = b.close_price
            sell_price = avg_price * (1 + margin)
            sold = True

            break

        dqty = (int(daily_seed / c.close_price) if remaining_seed > daily_seed
                else int(remaining_seed / c.close_price))
        burst_threshold = BURST_THRESHOLD * (0.2 + 0.8 * (1 - u50_rate))
        if remaining_seed > BURST_RATE * daily_seed and c.rsi < burst_threshold:
            dqty *= BURST_RATE

        rsi_threshold = RSI_THRESHOLD * (1 - u50_rate * (0.2 if exhaust_cnt == 0 else 0.6))
        if dqty > 0 and c.rsi <= rsi_threshold:
            invested_seed += dqty * c.close_price
            remaining_seed -= dqty * c.close_price

            stock_qty += dqty
            avg_price = invested_seed / stock_qty

        elif dqty == 0:
            if cycle > exhaust_cnt:
                exhaust_cnt += 1

                # sell_qty = stock_qty // 4
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

        u50_cnt += int(c.close_price < AVG50_HISTORY[c.date])
        u50_rate = u50_cnt / days

    base_invested_seed = SEED * min(days, TERM) / TERM
    base_remaining_seed = SEED - base_invested_seed
    base_invest_ror = base_end_price / base_start_price
    base_ror = (base_invest_ror * base_invested_seed + base_remaining_seed) / SEED - 1

    ror = (sell_price * stock_qty + remaining_seed) / SEED - 1

    if no_base_chart:
        base_ror = ror

    return Result(chart[0].date, days, sold, ror, base_ror)

def get_ratio(chart: List[StockRow], filter):
    tot = len(chart)
    cnt = len([c for c in chart if filter(c)])

    return cnt / tot