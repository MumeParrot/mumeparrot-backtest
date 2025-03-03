import re, os
import csv
import json
import matplotlib

import matplotlib.pyplot as plt

from datetime import datetime, timedelta

from typing import List, Dict, Tuple
from .const import StockRow, State

# matplotlib.use("TkAgg")

with open("tickers.json", "r") as fd:
    TICKERS = json.loads(fd.read())


def read_chart(ticker: str, start: str, end: str) -> List[StockRow]:
    ticker = ticker.upper()
    if ticker not in TICKERS.keys():
        raise Exception(f"'{ticker}' is not supported")

    with open(f"charts/{ticker}-GEN.csv", "r") as fd:
        reader = csv.reader(fd)
        history = [StockRow(d, float(p), float(cp)) for d, p, cp in reader]

    sidx = 0
    if start != "":
        matching = [d.startswith(start) for d, _, _ in history]
        sidx = matching.index(True)

    eidx = len(history)
    if end != "":
        matching = [d.startswith(end) for d, _, _ in history]
        eidx = len(matching) - list(reversed(matching)).index(True)

    return history[sidx:eidx]


def read_base_chart(ticker: str, start: str, end: str) -> List[StockRow]:
    ticker = ticker.upper()
    if ticker not in TICKERS.keys():
        raise Exception(f"'{ticker}' is not supported")

    base_ticker = TICKERS[ticker]

    with open(f"charts/{base_ticker}.csv", "r") as fd:
        data = list(csv.reader(fd))
        history = [
            StockRow(d, float(p), float(cp)) for d, p, _, _, cp, _ in data[1:]
        ]

    sidx = 0
    if start != "":
        matching = [d.startswith(start) for d, _, _ in history]
        sidx = matching.index(True)

    eidx = len(history)
    if end != "":
        matching = [d.startswith(end) for d, _, _ in history]
        eidx = len(matching) - list(reversed(matching)).index(True)

    return history[sidx:eidx]


def read_sahm() -> Dict[str, float]:
    class MonthlyDict(Dict):
        def __getitem__(self, idx):
            return super().__getitem__(f"{idx[0:7]}-01")

    with open(f"indices/sahm.csv", "r") as fd:
        history = list(csv.reader(fd))
        sahm = MonthlyDict({l[0]: float(l[1]) for l in history[1:]})

    return sahm


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


def compute_rsi(chart: List[StockRow], term: int) -> Dict[str, tuple]:
    rsis = {}

    def compute(ps: List[float]):
        if len(ps) <= 1:
            return 50

        diffs = [n - p for p, n in zip(ps[:-1], ps[1:])]

        tot_change = sum([d if d > 0 else -d for d in diffs])
        upgoing = sum([d for d in diffs if d > 0])

        return 100 * upgoing / tot_change

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
        if len(ps) <= 1:
            return 0

        diffs = [n - p for p, n in zip(ps[:-1], ps[1:])]

        tot_change = sum([abs(d) for d in diffs])
        last_change = diffs[-1]

        return 100 * last_change / tot_change

    prices = []
    for date, _, cp in chart:
        volatility[date] = compute(prices)

        prices += [cp]

        if len(prices) > term + 1:
            prices.pop(0)

    return volatility


def get_ticks(dates: List[str]):
    xticks = []
    xticklabels = []

    last_year = ""
    for i, d in enumerate(dates):
        year, m = d.split("-")[0:2]

        if year != last_year and m == "01":
            xticks.append(i)
            xticklabels.append(d[0:4])
            last_year = year

    return xticks, xticklabels


def plot_graph(ticker: str, start: str, end: str):
    chart = read_chart(ticker, start, end)
    avgs = compute_moving_average(chart, 50)
    urates = compute_urates(chart, 50, 40)
    rsis = compute_rsi(chart, 5)

    dates = [s.date for s in chart]

    fig = plt.figure(figsize=(20, 8))
    ax1 = fig.add_subplot(111)
    # ax2 = ax1.twinx()

    ax1.plot([c.close_price for c in chart], color="black", label="price")
    ax1.plot(
        [avgs[c.date] for c in chart], color="green", label="moving-average"
    )

    # ax2.plot([urates[c.date] * 100 for c in chart], color="cyan", label="urate")
    # ax2.plot([rsis[c.date] for c in chart], color="red", label="rsi")

    xticks, xticklabels = get_ticks(dates)
    ax1.set_xticks(xticks)
    ax1.set_xticklabels(xticklabels)

    ax1.set_title(f"{ticker} ({dates[0]} ~ {dates[-1]}) ")
    ax1.legend()
    # ax2.legend()

    ax1.grid(axis="y")
    plt.show()

def analyze_result(directory: str, ticker: str):
    files = [f'{directory}/{f}' for f in os.listdir(directory)
             if f.startswith(ticker)]

    from .configs import Config
    def parse_line(line: str) -> Tuple[Config, float]:
        line = line.replace(f'{ticker}: ', '')

        conf, res = line.split(' | ')
        m = re.match(r'(.+?) \((.+)%?, (.+)%?\)\n', res)
        score, ror_per_year, fail_rate = m.groups()

        score = float(score)

        conf = [c.split(': ') for c in conf.split(', ')]
        conf = {k: float(v) for k, v in conf}

        config = Config(**conf)

        return ((config, (ror_per_year, fail_rate)), score)

    final_results = {}
    for f in files:
        results = {}

        with open(f, 'r') as fd:
            lines = fd.readlines()

        for l in lines:
            try:
                config_and_result, score = parse_line(l)
                results[config_and_result] = score
            except Exception as e:
                pass

        sorted_results = sorted(results.items(), 
                                key=lambda item: item[1])

        for s in sorted_results[-2:]:
            final_results[s[0]] = s[1]

    final_results = sorted(final_results.items(),
                           key=lambda item: -item[1])

    for cr, score in final_results:
        print(f'{score} {cr[1]}: {cr[0]}')
