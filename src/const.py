from typing import List, Dict
from dataclasses import dataclass, astuple

EXTREME_FEAR = 25
FEAR = 45
NEUTRAL = 55
GREED = 75
EXTREME_GREED = 100

# sigma:    -2  -1.8  -1.6  -1.4 -1.2 -1.0 -0.8 -0.6 -0.4 -0.2 0
# delta: -16.3 -14.6 -13.0 -11.4 -9.8 -8.1 -6.5 -4.9 -3.3 -1.6 0
PANIC = -4.9
EXTREME_PANIC = -11.4
HAPPY = 4.9
EXTREME_HAPPY = 11.4

QUARTER_SELL_RATIO = 1

COMMISSION_RATE = 0.0025
CAPITAL_GAINS_TAX_CRITERION = 2000
CAPITAL_GAINS_TAX_RATE = 0.22


@dataclass
class StockRow:
    date: str
    price: float
    close_price: float
    rsi: float

    def __iter__(self):
        return iter(astuple(self))


@dataclass
class State:
    date: str
    principal: float
    seed: float
    ror: float

    close_price: float
    stock_qty: int
    stock_eval: float

    invested_seed: float
    stock_avg: float
    remaining_seed: float

    # rsi: float
    # fng: float
    # aaii: float

    # tax: float

    def __iter__(self):
        return iter(astuple(self))

@dataclass
class Result:
    start: str
    days: int
    sold: bool
    ror: float
    base_ror: float
    u50_rate: float


@dataclass
class Stat:
    rate_of_better_sold: float
    rate_of_sold: float
    avg_days_of_sold: int
    avg_ror_of_sold: float
    avg_ror_of_not_sold: float