from typing import List
from datetime import datetime, timedelta

from .configs import Config
from .const import SeedExhausted, State, Status
from .data import (
    read_chart,
    read_base_chart,
    compute_urates,
    compute_rsi,
    compute_volatility,
)
from .sim import oneday
from .env import TICKERS, CYCLE_DAYS, SEED, MAX_CYCLES


def full(
    ticker: str,
    config: Config,
    start: str,
    end: str,
) -> List[State]:
    base_ticker = TICKERS[ticker]

    full_chart = read_chart(ticker, "", "")
    chart = read_chart(ticker, start, end)
    base_chart = read_base_chart(base_ticker, start, end)

    URATE = compute_urates(full_chart, 50, config.term)
    RSI = compute_rsi(full_chart, 5)
    VOLATILITY = compute_volatility(full_chart, 5)

    s: State = State.init(SEED, MAX_CYCLES - 1)
    s.complete()

    history: List[State] = []
    for c in chart:
        try:
            s = oneday(c, s, config, RSI, VOLATILITY, URATE)
            history.append(s)
        except SeedExhausted:
            print(f"[{ticker}] Seed exhausted on {s.date}")
            break

    n_days = (
        datetime.strptime(history[-1].date, "%Y-%m-%d")
        - datetime.strptime(history[0].date, "%Y-%m-%d")
    ).days
    avg_ir = (1 + s.ror) ** (365 / n_days) - 1

    base_end = [c for c in base_chart if c.date == history[-1].date][0]
    base_start = [c for c in base_chart if c.date == history[0].date][0]

    base_ror = (base_end.close_price / base_start.close_price) - 1
    base_avg_ir = (1 + base_ror) ** (365 / n_days) - 1

    n_exhausted = len([s for s in history if s.status == Status.Exhausted and s.cycle != 0])
    n_failed = len([s for s in history if s.status == Status.Exhausted and s.cycle == 0])
    n_sold = len([s for s in history if s.status == Status.Sold])
    n_tot = n_exhausted + n_failed + n_sold

    exhaust_rate = n_exhausted / n_tot if n_tot else 0
    fail_rate = n_failed / n_tot if n_tot else 0

    print(f"[{ticker} ({base_ticker})] {history[0].date} ~ {history[-1].date}")
    print(f"Final RoR: {s.ror * 100:.1f}% ({avg_ir * 100:.1f}%)")
    print(f"Base RoR: {base_ror * 100:.1f}% ({base_avg_ir * 100:.1f}%)")
    print(f"Exhaust Rate: {exhaust_rate * 100:.1f}%, Fail Rate: {fail_rate * 100:.1f}%")

    return history
