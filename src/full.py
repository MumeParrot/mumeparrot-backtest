import os
import sys
from typing import List, Tuple, Dict, Optional
from datetime import datetime, timedelta

from .configs import Config
from .const import SeedExhausted, State, Status, History, StockRow
from .data import (
    read_chart,
    read_base_chart,
    compute_urates,
    compute_rsi,
    compute_volatility,
)
from .sim import oneday
from .env import DEBUG, VERBOSE, TICKERS, SEED, MAX_CYCLES, BOXX


def full_backtest(
    config: Config,
    chart: List[StockRow],
    urates: Dict[str, float],
    rsis: Dict[str, float],
    volatilities: Dict[str, float],
    log_fd: Optional[int] = None,
) -> History:

    s: State = State.init(SEED, MAX_CYCLES - 1)
    s.complete()

    history: List[State] = []
    for c in chart:
        s = oneday(c, s, config, rsis, volatilities, urates)
        history.append(s)

        if log_fd:
            print(
                str(s)
                + " ||| "
                + f"rsi={rsis[c.date]:>2.0f}, urate={urates[c.date] * 100:>2.0f}%, vol={volatilities[c.date]:.0f}",
                file=log_fd,
            )
            if s.boxx_eval < 0:
                print(f"[{s.date}] boxx exhuasted ({s.boxx_eval})", file=log_fd)

    return history


def full(
    ticker: str,
    config: Config,
    start: str,
    end: str,
    test_mode: bool = False,
) -> Tuple[History, float]:

    base_ticker = TICKERS[ticker]

    log_fd = None
    if DEBUG:
        os.makedirs("logs/full", exist_ok=True)
        log_fd = open(f"logs/full/{ticker}:{start}-{end}.log", "w")
    elif VERBOSE:
        log_fd = sys.stdout

    full_chart = read_chart(ticker, "", "", test_mode=test_mode)
    chart = read_chart(ticker, start, end, test_mode=test_mode)
    base_chart = read_base_chart(base_ticker, start, end)

    URATE = compute_urates(full_chart, 50, config.term)
    RSI = compute_rsi(full_chart, 5)
    VOLATILITY = compute_volatility(full_chart, 5)

    history = full_backtest(config, chart, URATE, RSI, VOLATILITY, log_fd)

    n_days = (
        datetime.strptime(history[-1].date, "%Y-%m-%d")
        - datetime.strptime(history[0].date, "%Y-%m-%d")
    ).days
    avg_ir = (1 + history[-1].ror) ** (365 / n_days) - 1

    base_end = [c for c in base_chart if c.date == history[-1].date][0]
    base_start = [c for c in base_chart if c.date == history[0].date][0]

    base_ror = (base_end.close_price / base_start.close_price) - 1
    base_avg_ir = (1 + base_ror) ** (365 / n_days) - 1

    n_exhausted = len(
        [s for s in history if s.status == Status.Exhausted and s.cycle != 0]
    )
    n_failed = len(
        [s for s in history if s.status == Status.Exhausted and s.cycle == 0]
    )
    n_sold = len([s for s in history if s.status == Status.Sold])
    n_tot = n_exhausted + n_failed + n_sold

    exhaust_rate = n_exhausted / n_tot if n_tot else 0
    fail_rate = n_failed / n_tot if n_tot else 0

    if test_mode:
        print(f"{ticker}: {config} | {avg_ir:.2f}")
    else:
        print(
            f"[{ticker} ({base_ticker})] {history[0].date} ~ {history[-1].date}"
        )
        print(
            f"\tFinal RoR: {history[-1].ror * 100:.1f}% ({avg_ir * 100:.1f}%)"
        )
        print(f"\tBase RoR: {base_ror * 100:.1f}% ({base_avg_ir * 100:.1f}%)")
        print(
            f"\tExhaust Rate: {exhaust_rate * 100:.1f}%, Fail Rate: {fail_rate * 100:.1f}%"
        )

        if BOXX:
            boxx_ror = (
                history[-1].boxx_eval - history[-1].boxx_seed
            ) / history[-1].principal

            print(f"\tBOXX Profit: {boxx_ror * 100:.1f}%")

    return history, avg_ir
