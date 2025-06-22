from typing import List
from copy import deepcopy
from enum import Enum
from dataclasses import dataclass, astuple

from datetime import datetime

from .env import MARKET_DAYS_PER_YEAR, COMMISSION_RATE, BOXX, BOXX_UNIT, BOXX_IR


class SeedExhausted(Exception):
    pass


class Status(Enum):
    Buying = 0
    Sold = 1
    Exhausted = 2

    def is_sold(self) -> bool:
        return self == Status.Sold

    def is_exhausted(self) -> bool:
        return self == Status.Exhausted


@dataclass
class StockRow:
    date: str
    price: float
    close_price: float

    def __iter__(self):
        return iter(astuple(self))


@dataclass
class State:
    date: str
    elapsed: int
    principal: float
    price: float
    close_price: float
    max_cycle: int

    seed: float
    invested_seed: float
    remaining_seed: float
    stock_qty: float
    commission: float

    status: Status
    cycle: int

    # BOXX related fields (these should not affect simulation)
    # balance + boxx_seed = remaining_seed
    balance: float  # should be within BOXX_UNIT * seed ~ 2 * BOXX_UNIT * seed
    boxx_seed: float
    boxx_eval: float

    # Auto filled fields
    avg_price: float = None
    stock_eval: float = None
    ror: float = None

    @classmethod
    def init(cls, seed: float, max_cycle: int) -> "State":
        return State(
            date=None,
            elapsed=0,
            principal=seed,
            price=None,
            close_price=None,
            seed=seed,
            invested_seed=0,
            remaining_seed=seed,
            stock_qty=0,
            commission=0,
            status=Status.Buying,
            cycle=0,
            max_cycle=max_cycle,
            balance=seed,
            boxx_seed=0,
            boxx_eval=0,
        )

    @classmethod
    def from_(cls, s: "State", c: StockRow) -> "State":
        new_s = deepcopy(s)

        new_s.date = c.date
        new_s.elapsed += 1
        new_s.price = c.price
        new_s.close_price = c.close_price

        return new_s

    def __str__(self):
        if not self.date:
            return ""

        price = (
            (self.close_price - self.avg_price) / self.avg_price
            if self.avg_price
            else 0
        )

        s = ""
        pfx = (
            f"[{self.date} ({self.elapsed:02})] [{self.cycle}] "
            + f"seed={self.seed:>6.0f}({self.invested_seed:.0f}+{self.remaining_seed:.0f}) "
        )
        s = f"{pfx:<51}"

        pfx = f"eval={self.stock_qty * self.close_price:.2f}({self.stock_qty}*{self.close_price:.2f}) "
        s += f"{pfx:<32}"

        pfx = f"price={price * 100:.1f}%({self.close_price:.1f}/{self.avg_price:.1f}) "
        s += f"{pfx:<26}"

        pfx = f"ror={self.ror * 100:.1f}% [{self.status.name}]"
        s += f"{pfx:<25}"

        return s

    def __iter__(self):
        return iter(astuple(self))

    def cycle_left(self) -> bool:
        return self.cycle < self.max_cycle

    def cycle_done(self) -> bool:
        # self.cycle roll back to 0 when all cycles are used
        return self.cycle == 0

    def sell(self, qty: int, sell_price: float, sold: bool = False):
        all_cycle_used = not sold and self.cycle == self.max_cycle
        if all_cycle_used:
            assert qty == self.stock_qty

        commission = qty * sell_price * COMMISSION_RATE

        self.invested_seed -= qty * self.avg_price
        self.remaining_seed += qty * sell_price - commission
        self.seed = self.remaining_seed if sold else self.seed  # TODO
        self.stock_qty -= qty
        self.commission += commission

        self.balance += qty * sell_price - commission
        if BOXX and self.balance > 2 * BOXX_UNIT * self.seed:
            boxx_buy = self.balance - 2 * BOXX_UNIT * self.seed
            boxx_commission = boxx_buy * COMMISSION_RATE

            self.balance -= boxx_buy
            self.boxx_seed += boxx_buy
            self.boxx_eval += boxx_buy - boxx_commission

        self.status = Status.Sold if sold else Status.Exhausted
        self.cycle = 0 if sold or all_cycle_used else self.cycle + 1

    def buy(self, qty: int, buy_price: float):
        commission = qty * buy_price * COMMISSION_RATE

        self.invested_seed += qty * buy_price
        self.remaining_seed -= qty * buy_price + commission
        self.commission += commission

        self.balance -= qty * buy_price + commission
        if (
            BOXX
            and self.balance < BOXX_UNIT * self.seed
            and self.boxx_seed >= BOXX_UNIT * self.seed
        ):
            boxx_sell = BOXX_UNIT * self.seed
            boxx_commission = boxx_sell * COMMISSION_RATE

            self.balance += boxx_sell
            self.boxx_seed -= boxx_sell
            self.boxx_eval -= boxx_sell + boxx_commission

            # if self.boxx_eval < 0:
            #     print(f"[{self.date}] boxx={self.boxx_eval}")

        self.stock_qty += qty
        self.status = Status.Buying

    def complete(self):
        self.avg_price = (
            self.invested_seed / self.stock_qty if self.stock_qty > 0 else 0
        )
        self.stock_eval = (
            self.stock_qty * self.close_price if self.stock_qty > 0 else 0
        )

        if self.boxx_eval > 0:
            self.boxx_eval *= 1 + (BOXX_IR / MARKET_DAYS_PER_YEAR)
        boxx_profit = self.boxx_eval - self.boxx_seed

        self.ror = (
            self.remaining_seed + self.stock_eval + boxx_profit
        ) / self.principal - 1


class History(List[State]):
    def append(self, s: State):
        assert isinstance(s, State)

        super().append(s)

    def __str__(self):
        return "\n".join(str(s) for s in self)


@dataclass
class Result:
    start: str
    end: str

    sold: bool
    ror: float

    @property
    def days(self) -> int:
        start: datetime = datetime.strptime(self.start, "%Y-%m-%d")
        end: datetime = datetime.strptime(self.end, "%Y-%m-%d")

        return (end - start).days
