from typing import List

from .configs import Config
from .const import State
from .data import (
    read_chart,
    compute_urates,
    compute_rsi,
    compute_volatility,
)
from .sim import oneday
from .env import CYCLE_DAYS, SEED, MAX_CYCLES


def full(
    ticker: str,
    config: Config,
    start: str,
    end: str,
) -> List[State]:
    full_chart = read_chart(ticker, "", "")
    chart = read_chart(ticker, start, end)

    URATE = compute_urates(full_chart, 50, MAX_CYCLES)
    RSI = compute_rsi(full_chart, 5)
    VOLATILITY = compute_volatility(full_chart, 5)

    s: State = State.init(SEED, MAX_CYCLES)
    s.complete()

    history: List[State] = []
    for c in chart:
        s = oneday(c, s, config, CYCLE_DAYS, RSI, VOLATILITY, URATE)
        history.append(s)

    print(f"Final RoR: {s.ror * 100:.1f}%")

    return history
