import sys
from typing import List, Dict

from .const import StockRow, State, Result
from .data import (
    read_chart,
    compute_urates,
    compute_rsi,
    compute_volatility,
    read_sahm,
)
from .configs import Config

from .sim import oneday
from .env import CYCLE_DAYS, SEED, MAX_CYCLES, FAIL_PANELTY, FAIL_LIMIT

MARKET_DAYS_PER_YEAR = 260


def compute_fail_rate(results: Dict[int, List[Result]]) -> float:
    n_total = len(results[0])
    n_failed = len([r for r in results[MAX_CYCLES - 1] if not r.sold])

    return n_failed / n_total


def compute_avg_ror(results: Dict[int, List[Result]]):
    tot_ror = 0
    tot_days = 0

    for c in range(MAX_CYCLES - 1):
        tot_ror += sum([r.ror for r in results[c] if r.sold])
        tot_days += sum([r.days for r in results[c] if r.sold])

    tot_ror += sum([r.ror for r in results[MAX_CYCLES - 1]])
    tot_days += sum(
        [
            r.days if r.sold else MAX_CYCLES * CYCLE_DAYS
            for r in results[MAX_CYCLES - 1]
        ]
    )

    return tot_ror / tot_days * MARKET_DAYS_PER_YEAR


def simulate(
    chart: List[StockRow],
    max_cycle: int,
    config: Config,
    URATE: Dict[str, float],
    RSI: Dict[str, float],
    VOLATILITY: Dict[str, float],
) -> List[State]:

    s: State = State.init(SEED, max_cycle)
    s.complete()

    history: List[State] = []
    for c in chart:
        s = oneday(c, s, config, CYCLE_DAYS, RSI, VOLATILITY, URATE)
        history.append(s)

        if s.status.is_sold():
            break

    return history


def test(
    ticker: str,
    config: Config,
    start: str,
    end: str,
) -> float:

    full_chart = read_chart(ticker, "", "")
    chart = read_chart(ticker, start, end)

    URATE = compute_urates(full_chart, 50, CYCLE_DAYS)
    RSI = compute_rsi(full_chart, 5)
    VOLATILITY = compute_volatility(full_chart, 5)
    SAHM_INDICATOR = read_sahm()

    # Split all-time chart to a number of fractions
    charts = [chart[i : i + CYCLE_DAYS] for i in range(len(chart) - CYCLE_DAYS)]

    _charts = charts

    histories: Dict[int, List[State]] = {}
    results: Dict[int, List[Result]] = {}

    for cycle in range(MAX_CYCLES):
        histories[cycle] = []
        results[cycle] = []

        for chart in _charts:
            if (
                config.sahm_threshold != 0
                and SAHM_INDICATOR[chart[0].date] > config.sahm_threshold
            ):
                continue

            history = simulate(chart, cycle, config, URATE, RSI, VOLATILITY)

            result = Result(
                start=history[0].date,
                end=history[-1].date,
                sold=history[-1].status.is_sold(),
                ror=history[-1].ror,
            )

            histories[cycle].append(history)
            results[cycle].append(result)

        # Rebuild fractions by extending the fractions that have failed
        _charts = []
        for res in results[cycle]:
            if not res.sold:
                idx = [c[0].date for c in charts].index(res.start)

                # Check boundary condition
                if idx + (cycle + 1) * CYCLE_DAYS >= len(charts):
                    continue

                extended_chart = []

                for i in range(cycle + 2):
                    extended_chart += charts[idx + i * CYCLE_DAYS]

                _charts.append(extended_chart)

    fail_rate = compute_fail_rate(results)
    avg_ror_per_year = compute_avg_ror(results)

    score = (
        (1 - FAIL_PANELTY * fail_rate) * avg_ror_per_year * 100
        if fail_rate < FAIL_LIMIT
        else 0
    )

    print(
        f"{ticker}: {config} | {score:.2f} ({avg_ror_per_year * 100:.1f}%, {fail_rate * 100:.1f}%)"
    )

    sys.stdout.flush()
    return score
