import sys

from typing import List, Dict
from .const import StockRow, Result, Stat
from .utils import (
    read_chart,
    read_base_chart,
    compute_urates,
    compute_rsi,
    compute_volatility,
    read_sahm,
)
from .configs import Config

from datetime import datetime, timedelta

MARKET_DAYS_PER_YEAR = 260

# BULLISH_RSI = 80
# BEARISH_RSI = 40
# BEARISH_SCALE = 0.4
# BULLISH_U50 = 0.5
# BEARISH_U50 = 0.6
# BURST_VOL = 30


TERM = 40
SEED = 1000000

U50_RATES = None
D5_RSI = None
D5_VOLATILITY = None
SAHM_INDICATOR = None

CONFIG = None
VERBOSE = False


def vprint(s):
    if VERBOSE:
        print(s)


def test(
    ticker: str,
    max_cycles: int,
    config: Config,
    start: str,
    end: str,
    verbose=False,
) -> float:

    global CONFIG, VERBOSE
    CONFIG = config
    VERBOSE = verbose

    chart = read_chart(ticker, start, end)
    base_chart = chart
    # base_chart = read_base_chart(ticker, start, end)

    global U50_RATES, D5_RSI, D5_VOLATILITY, SAHM_INDICATOR
    U50_RATES = compute_urates(chart, 50, TERM)
    D5_RSI = compute_rsi(chart, 5)
    D5_VOLATILITY = compute_volatility(chart, 5)
    SAHM_INDICATOR = read_sahm()

    # Split all-time chart to a number of fractions
    charts = [chart[i : i + TERM] for i in range(len(chart) - TERM)]
    base_charts = [
        base_chart[i : i + TERM] for i in range(len(base_chart) - TERM)
    ]

    _charts = charts
    _base_charts = base_charts

    stats: List[Stat] = []
    results: Dict[int, List[Result]] = {}

    for c in range(max_cycles):
        results[c] = []

        # Simulate Mumae for all fractions of chart
        for chart, base_chart in zip(_charts, _base_charts):
            if (
                CONFIG.sahm_threshold != 0
                and SAHM_INDICATOR[chart[0].date] > CONFIG.sahm_threshold
            ):
                continue

            res = simulate(chart, base_chart, c)
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
        btb_ns = len(
            [r for r in results[c] if not r.sold and r.ror > r.base_ror]
        )
        wtb_ns = len(
            [r for r in results[c] if not r.sold and r.ror <= r.base_ror]
        )

        rate_of_better_sold = btb_s / total if total != 0 else 0
        rate_of_sold = (btb_s + wtb_s) / total if total != 0 else 0

        avg_days_of_sold = (
            sum([r.days for r in results[c] if r.sold]) / (btb_s + wtb_s)
            if btb_s + wtb_s > 0
            else 0
        )
        avg_ror_of_sold = (
            sum([r.ror for r in results[c] if r.sold]) / (btb_s + wtb_s)
            if btb_s + wtb_s > 0
            else 0
        )

        if btb_ns + wtb_ns > 0:
            avg_ror_of_not_sold = sum(
                [r.ror for r in results[c] if not r.sold]
            ) / (btb_ns + wtb_ns)
        else:
            avg_ror_of_not_sold = 0

        stat = Stat(
            rate_of_better_sold,
            rate_of_sold,
            avg_days_of_sold,
            avg_ror_of_sold,
            avg_ror_of_not_sold if c == max_cycles - 1 else 0,
        )

        stats.append(stat)

    #         if verbose:
    #             print(
    #                 f"""[Cycle {c}] ({total})
    # rate_of_better_sold: {rate_of_better_sold * 100:.2f}%\trate_of_sold:    {rate_of_sold * 100:.2f}% ({btb_s + wtb_s})
    # avg_days_of_sold:    {avg_days_of_sold:.0f}\t\tavg_ror_of_sold: {avg_ror_of_sold * 100:.2f}%"""
    #                 + (
    #                     f"\n avg_ror_of_not_sold: {avg_ror_of_not_sold * 100:.2f}%"
    #                     if c == max_cycles - 1
    #                     else ""
    #                 )
    #             )
    #             print(f"Min RoR: {min(r.ror for r in results[c]) * 100:.2f} %")

    fail_rate = compute_fail_rate(stats)
    avg_ror_per_year = compute_avg_ror(results, max_cycles)

    score = (1 - fail_rate) * avg_ror_per_year * 100 if fail_rate < 0.1 else 0

    # for r in results[1]:
    #     if not r.sold:
    #         print(f"{r.start} ~ {r.end}: {r.ror}")

    print(
        f"{ticker}: {CONFIG} | {score:.2f} ({avg_ror_per_year * 100:.1f}%, {fail_rate * 100:.1f}%)"
    )

    sys.stdout.flush()
    return score


def simulate(
    chart: List[StockRow],
    base_chart: List[StockRow],
    allowed_cycles: int,
) -> Result:
    daily_seed = SEED / TERM
    base_start_price = base_chart[0].close_price

    remaining_seed = SEED
    invested_seed = 0
    stock_qty = 0
    avg_price = 0

    sold = False
    days = 0
    exhaust_cnt = 0

    for c, b in zip(chart, base_chart):
        margin = CONFIG.margin

        if stock_qty > 0 and c.close_price > avg_price * (1 + margin):
            base_end_price = b.close_price
            sell_price = avg_price * (1 + margin)
            sold = True
            break

        dqtyD = float(daily_seed / c.close_price)
        rate = float(1)

        rsi = D5_RSI[c.date]
        vol = D5_VOLATILITY[c.date]
        u50_rate = U50_RATES[c.date]
        bearish_scale = 1 - CONFIG.min_bearish_rate

        if rsi > CONFIG.bullish_rsi:
            rate = 0
        elif rsi < CONFIG.bearish_rsi:
            rate *= float(
                min(
                    1,
                    CONFIG.min_bearish_rate
                    + bearish_scale * rsi / CONFIG.bearish_rsi,
                )
            )

        if (
            u50_rate < CONFIG.bullish_u50
            and vol < 0
            and abs(vol) > CONFIG.burst_vol
        ):
            rate *= (
                1
                + CONFIG.burst_scale
                * (vol - CONFIG.burst_vol)
                / CONFIG.burst_vol
            )

        # elif u50_rate > BEARISH_U50 and vol > 0 and abs(vol) > BURST_VOL:
        #     rate *= 1 / 2

        dqty = int(dqtyD * rate)

        if remaining_seed >= dqty * c.close_price:
            invested_seed += dqty * c.close_price
            remaining_seed -= dqty * c.close_price

            stock_qty += dqty
            avg_price = invested_seed / stock_qty if stock_qty > 0 else 0

        elif remaining_seed >= c.close_price:  # Just buy all
            dqty = int(remaining_seed / c.close_price)

            invested_seed += dqty * c.close_price
            remaining_seed -= dqty * c.close_price

            stock_qty += dqty
            avg_price = invested_seed / stock_qty if stock_qty > 0 else 0

        else:  # All seed used
            if allowed_cycles > exhaust_cnt:
                exhaust_cnt += 1

                sell_qty = int(max(stock_qty / 4, stock_qty * u50_rate))
                invested_seed -= sell_qty * avg_price
                remaining_seed += sell_qty * c.close_price

                stock_qty -= sell_qty

            else:  # Get out of the loop (failed to complete cycle)
                base_end_price = b.close_price
                sell_price = c.close_price

                break

        # Loop may end, so prepare always
        base_end_price = b.close_price
        sell_price = c.close_price

        days += 1

    base_invested_seed = SEED * min(days, TERM) / TERM
    base_remaining_seed = SEED - base_invested_seed
    base_invest_ror = base_end_price / base_start_price
    base_ror = (
        base_invest_ror * base_invested_seed + base_remaining_seed
    ) / SEED - 1

    ror = (sell_price * stock_qty + remaining_seed) / SEED - 1

    return Result(chart[0].date, days, sold, ror, base_ror, c.date)


def compute_avg_ror(results: Dict[int, List[Result]], max_cycles: int):
    tot_ror = 0
    tot_days = 0

    for c in range(max_cycles - 1):
        tot_ror += sum([r.ror for r in results[c] if r.sold])
        tot_days += sum([r.days for r in results[c] if r.sold])

    tot_ror += sum([r.ror for r in results[max_cycles - 1]])
    tot_days += sum(
        [
            r.days if r.sold else max_cycles * TERM
            for r in results[max_cycles - 1]
        ]
    )

    return tot_ror / tot_days * MARKET_DAYS_PER_YEAR


def compute_fail_rate(stats: List[Stat]) -> float:
    fail_rate = 1

    for s in stats:
        fail_rate *= 1 - s.rate_of_sold

    return fail_rate
