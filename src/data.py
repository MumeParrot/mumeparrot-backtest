import csv

from typing import List, Dict
from random import random
from statistics import mean

from .const import StockRow
from .env import TICKERS

CHARTS_PATH = "charts"
INDICES_PATH = "indices"


def read_chart(
    ticker: str, start: str, end: str, test_mode: bool = False
) -> List[StockRow]:
    ticker = ticker.upper()
    if ticker not in TICKERS.keys():
        raise Exception(f"'{ticker}' is not supported")

    history: List[StockRow] = []
    with open(f"{CHARTS_PATH}/{ticker}-GEN.csv", "r") as fd:
        reader = csv.reader(fd)
        hist = [(d, float(p), float(cp)) for d, p, cp in reader]

        mean_flucs = mean(abs((cp - p) / p) for _, p, cp in hist)
        for d, p, cp in hist:
            p = (
                (1 - (mean_flucs / 2) + random() * mean_flucs) * float(p)
                if test_mode
                else float(p)
            )
            cp = (
                (1 - (mean_flucs / 2) + random() * mean_flucs) * float(cp)
                if test_mode
                else float(cp)
            )

            history.append(StockRow(d, p, cp))

    sidx = 0
    if start != "":
        matching = [d.startswith(start) for d, _, _ in history]
        try:
            sidx = matching.index(True)
        except:
            pass

    eidx = len(history)
    if end != "":
        matching = [d.startswith(end) for d, _, _ in history]
        try:
            eidx = len(matching) - list(reversed(matching)).index(True)
        except:
            pass

    return history[sidx:eidx]


def read_base_chart(ticker: str, start: str, end: str) -> List[StockRow]:
    ticker = ticker.upper()
    if ticker not in TICKERS.values():
        raise Exception(f"'{ticker}' is not supported")

    with open(f"{CHARTS_PATH}/{ticker}.csv", "r") as fd:
        reader = list(csv.reader(fd))
        history = [
            StockRow(d, float(p), float(cp)) for d, p, _, _, cp, _ in reader[1:]
        ]

    sidx = 0
    if start != "":
        matching = [d.startswith(start) for d, _, _ in history]
        try:
            sidx = matching.index(True)
        except:
            pass

    eidx = len(history)
    if end != "":
        matching = [d.startswith(end) for d, _, _ in history]
        try:
            eidx = len(matching) - list(reversed(matching)).index(True)
        except:
            pass

    return history[sidx:eidx]


def read_sahm() -> Dict[str, float]:
    class MonthlyDict(Dict):
        def __getitem__(self, idx):
            return super().__getitem__(f"{idx[0:7]}-01")

    with open(f"{INDICES_PATH}/sahm.csv", "r") as fd:
        history = list(csv.reader(fd))
        sahm = MonthlyDict({l[0]: float(l[1]) for l in history[1:]})

    return sahm


def compute_rsi(chart: List[StockRow], term: int) -> Dict[str, tuple]:
    rsis = {}

    def compute(ps: List[float]):
        if len(ps) <= term:
            return 50

        diffs = [n - p for p, n in zip(ps[:-1], ps[1:])]

        tot_change = sum([d if d > 0 else -d for d in diffs])
        upgoing = sum([d for d in diffs if d > 0])

        return 100 * upgoing / tot_change if tot_change > 0 else 50

    prices = []
    for date, _, cp in chart:
        prices += [cp]
        if len(prices) > term + 1:
            prices.pop(0)

        rsis[date] = compute(prices)

    return rsis


def compute_volatility(chart: List[StockRow], term: int) -> Dict[str, float]:
    volatility = {}

    def compute(ps: List[float]):
        if len(ps) <= term:
            return 0

        diffs = [n - p for p, n in zip(ps[:-1], ps[1:])]

        tot_change = sum([abs(d) for d in diffs])
        last_change = diffs[-1]

        return 100 * last_change / tot_change

    prices = []
    for date, _, cp in chart:
        prices += [cp]
        if len(prices) > term + 1:
            prices.pop(0)

        volatility[date] = compute(prices)

    return volatility


def compute_moving_average(
    chart: List[StockRow], term: int
) -> Dict[str, float]:
    avg_history = {}

    prices = []
    for date, p, cp in chart:
        prices += [cp]
        if len(prices) > term:
            prices.pop(0)

        avg_history[date] = sum(prices) / len(prices) if prices else p

    return avg_history


def compute_urates(chart: List[StockRow], avg: int, term: int):
    avg_history = compute_moving_average(chart, avg)
    u_rates = {}

    u_counters = []
    for c in chart:
        u_counters.append(int(c.close_price < avg_history[c.date]))
        if len(u_counters) > term:
            u_counters.pop(0)

        u_rates[c.date] = sum(u_counters) / len(u_counters)

    return u_rates
