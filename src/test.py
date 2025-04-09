import sys
from typing import List, Dict, Tuple

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

NUM_SIMULATED = 0
NUM_RETIRED = 0


def compute_weighted_results(
    results: Dict[int, List[Result]],
) -> Dict[str, Tuple[float, Result]]:
    date_results: Dict[str, Result] = {}
    for c in range(MAX_CYCLES - 1):
        for r in results[c]:
            if r.sold:
                date_results[r.start] = r

    for r in results[MAX_CYCLES - 1]:
        date_results[r.start] = r

    weighted_results: Dict[str, float] = {}
    sorted_dates = sorted(list(date_results.keys()))
    date_idx = {d: i for i, d in enumerate(sorted_dates)}

    for i, start in enumerate(sorted_dates):
        last_cycle_dates = sorted_dates[max(i - CYCLE_DAYS, 0) : i]

        end_in_start: Dict[str, int] = {}
        for d in reversed(last_cycle_dates):
            res = date_results[d]

            e = date_idx.get(res.end, sys.maxsize)
            s = date_idx.get(start)

            end_in_start[d] = int(abs(e - s) <= 1) or end_in_start.get(
                res.end, 0
            )

        weight = (
            sum(end_in_start.values()) / len(end_in_start)
            if end_in_start
            else 0.5
        )

        weighted_results[start] = (weight, date_results[start])

    return weighted_results


def compute_fail_rate(results: Dict[int, List[Result]]) -> float:
    weighted_results = compute_weighted_results(results)

    n_failed = sum([w for w, r in weighted_results.values() if not r.sold])
    n_total = sum([w for w, _ in weighted_results.values()])

    return n_failed / n_total


def compute_avg_ror(results: Dict[int, List[Result]]):
    weighted_results = compute_weighted_results(results)

    tot_ror = 0
    tot_days = 0

    for s, wr in weighted_results.items():
        weight, result = wr

        tot_ror += weight * result.ror
        tot_days += weight * result.days

    return tot_ror / tot_days * MARKET_DAYS_PER_YEAR


def simulate(
    chart: List[StockRow],
    max_cycle: int,
    config: Config,
    URATE: Dict[str, float],
    RSI: Dict[str, float],
    VOLATILITY: Dict[str, float],
) -> List[State]:
    global NUM_SIMULATED, NUM_RETIRED

    s: State = State.init(SEED, max_cycle)
    s.complete()

    history: List[State] = []
    for c in chart:
        s = oneday(c, s, config, RSI, VOLATILITY, URATE)
        history.append(s)

        if s.status.is_sold():
            break

        elif s.status.is_exhausted() and s.cycle_done():
            break

    NUM_SIMULATED += 1
    if not s.status.is_sold() and not s.status.is_exhausted():
        NUM_RETIRED += 1

    return history


def test(
    ticker: str,
    config: Config,
    start: str,
    end: str,
) -> float:
    global NUM_SIMULATED, NUM_RETIRED
    NUM_SIMULATED = 0
    NUM_RETIRED = 0

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

    if NUM_RETIRED > 0.05 * NUM_SIMULATED:
        print(
            f"[warning] {NUM_RETIRED / NUM_SIMULATED * 100:.1f}% simulations retired"
        )

    sys.stdout.flush()
    return score
