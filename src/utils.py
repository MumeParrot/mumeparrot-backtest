import csv
import matplotlib

import matplotlib.pyplot as plt

from datetime import datetime, timedelta

from typing import List, Dict
from .const import StockRow, State

matplotlib.use("TkAgg")

INIT = "init"
FIN = "fin"
TICKERS = {"TQQQ": "QQQ", "SOXL": "SOXX", "SPXL": "SPY"}


def read_chart(ticker: str, start: str, end: str) -> List[StockRow]:
    ticker = ticker.upper()
    if ticker not in TICKERS.keys():
        raise Exception(f"'{ticker}' is not supported")

    with open(f"charts/{ticker}-SIM.csv", "r") as fd:
        reader = csv.reader(fd)
        history = [StockRow(d, float(p), float(cp)) for d, p, cp in reader]

    sidx = 0
    if start != INIT:
        matching = [d.startswith(start) for d, _, _ in history]
        sidx = matching.index(True)

    eidx = len(history)
    if end != FIN:
        matching = [d.startswith(end) for d, _, _ in history]
        eidx = len(matching) - list(reversed(matching)).index(True)

    return history[sidx:eidx]


def read_base_chart(ticker: str, start: str, end: str) -> List[StockRow]:
    ticker = ticker.upper()
    if ticker not in TICKERS.keys():
        raise Exception(f"'{ticker}' is not supported")

    base_ticker = TICKERS[ticker]

    with open(f"charts/{base_ticker}.csv", "r") as fd:
        reader = csv.reader(fd)
        history = [
            StockRow(d, float(p), float(cp))
            for d, p, _, _, _, cp, _ in list(reader)[1:]
        ]

    sidx = 0
    if start != INIT:
        matching = [d.startswith(start) for d, _, _ in history]
        sidx = matching.index(True)

    eidx = len(history)
    if end != FIN:
        matching = [d.startswith(end) for d, _, _ in history]
        eidx = len(matching) - list(reversed(matching)).index(True)

    return history[sidx:eidx]


def read_aaii(chart: List[StockRow]) -> Dict[str, float]:
    def convert_date(date: str) -> str:
        month, day, year = date.split("-")
        if len(month) == 1:
            month = "0" + month

        if year[0] in ["8", "9"]:
            year = "19" + year
        else:
            year = "20" + year

        return f"{year}-{month}-{day}"

    def compute_score(bullish: float, bearish: float) -> float:
        return bullish / (bullish + bearish)

    with open(f"indices/aaii.csv", "r") as fd:
        reader = csv.reader(fd)
        history = [
            (convert_date(d), compute_score(float(bu[:-1]), float(be[:-1])))
            for d, bu, _, be in reader
        ]

    deltas = [
        (h2[0], (h2[1] - h1[1]) * 100)
        for h1, h2 in zip(history[:-1], history[1:])
    ]

    aaii: Dict[str, float] = {}
    for date, delta in deltas:
        dt = datetime.strptime(date, "%Y-%m-%d")

        for i in range(8):
            idx = dt + timedelta(days=i)
            aaii[idx.strftime("%Y-%m-%d")] = delta

    last_delta = aaii[chart[0].date]
    for d, _, _ in chart:
        if d in aaii.keys():
            last_delta = aaii[d]

        else:
            aaii[d] = last_delta

    return aaii


def read_sahm() -> Dict[str, float]:
    class MonthlyDict(Dict):
        def __getitem__(self, idx):
            return super().__getitem__(f"{idx[0:7]}-01")

    with open(f"indices/sahm.csv", "r") as fd:
        history = list(csv.reader(fd))
        sahm = MonthlyDict({l[0]: float(l[1]) for l in history[1:]})

    return sahm


def moving_average(chart: List[StockRow], term: int) -> Dict[str, float]:
    avg_history = {}

    prices = []
    for date, p, cp in chart:
        avg_history[date] = sum(prices) / len(prices) if prices else p

        prices += [p]

        if len(prices) > term:
            prices.pop(0)

    return avg_history


def plot(ticker: str, histories: Dict[str, List[State]]):
    dates = [s.date for s in list(histories.values())[0]]

    fig = plt.figure(figsize=(20, 8))
    ax = fig.add_subplot(111)

    for l, h in histories.items():
        rors = [s.ror for s in h]

        ax.plot(rors, label=l)

    xticks = []
    xticklabels = []

    last_year = ""
    for i, d in enumerate(dates):
        year, m = d.split("-")[0:2]

        if year != last_year and m == "01":
            xticks.append(i)
            xticklabels.append(d[0:4])
            last_year = year

        # elif last_m == "01" and m == "07":
        #     xticks.append(i)
        #     xticklabels.append(d)
        #     last_m = "07"

    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels)

    ax.set_title(ticker + " from " + dates[0][:4])
    ax.legend()

    ax.grid(axis="y")

    plt.show()
