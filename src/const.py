from copy import deepcopy
from enum import Enum
from dataclasses import dataclass, astuple

from datetime import datetime


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

    status: Status
    cycle: int

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
            status=Status.Buying,
            cycle=0,
            max_cycle=max_cycle,
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

        return (
            f"[{self.date}] "
            + f"seed={self.seed:.0f}({self.invested_seed:.0f}+{self.remaining_seed:.0f}) "
            + f"eval={self.stock_qty * self.close_price:.2f}({self.stock_qty}*{self.close_price:.2f}) "
            + f"ror={self.ror * 100:.1f}% "
            + f"({self.status.name})"
        )

    def __iter__(self):
        return iter(astuple(self))

    def cycle_left(self):
        return self.cycle < self.max_cycle

    def cycle_done(self):
        return self.cycle > self.max_cycle

    def sell(self, qty: int, sell_price: float, sold: bool = False):
        all_cycle_used = not sold and self.cycle == self.max_cycle
        if all_cycle_used:
            assert qty == self.stock_qty

        self.invested_seed -= qty * self.avg_price
        self.remaining_seed += sell_price * qty
        self.seed = self.remaining_seed if sold else self.seed  # TODO
        self.stock_qty -= qty

        self.status = Status.Sold if sold else Status.Exhausted
        self.cycle = 0 if sold or all_cycle_used else self.cycle + 1

    def buy(self, qty: int, buy_price: float):
        self.invested_seed += qty * buy_price
        self.remaining_seed -= qty * buy_price

        self.stock_qty += qty
        self.status = Status.Buying

    def complete(self):
        self.avg_price = (
            self.invested_seed / self.stock_qty if self.stock_qty > 0 else 0
        )
        self.stock_eval = (
            self.stock_qty * self.close_price if self.stock_qty > 0 else 0
        )
        self.ror = (self.remaining_seed + self.stock_eval) / self.principal - 1


@dataclass
class Result:
    start: str
    end: str

    sold: bool
    ror: float

    @property
    def days(self):
        start: datetime = datetime.strptime(self.start, "%Y-%m-%d")
        end: datetime = datetime.strptime(self.end, "%Y-%m-%d")

        return (end - start).days
