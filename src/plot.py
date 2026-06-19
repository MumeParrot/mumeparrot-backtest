import os
import re
import sys
import matplotlib
from typing import List, Tuple
from enum import Enum

# If running headlessly/non-interactively, switch to Agg backend immediately to avoid hanging on GUI display initialization
if not sys.stdout.isatty():
    try:
        matplotlib.use("Agg")
    except Exception:
        pass

import matplotlib.pyplot as plt

from .const import Status, State
from .data import read_chart


class Granul(Enum):
    Month = 0
    Month6 = 1
    Year = 2


def get_ticks(dates: List[str], granul: Granul = Granul.Year):
    xticks = []
    xticklabels = []

    last_year = ""
    last_month = ""
    for i, d in enumerate(dates):
        year, month = d.split("-")[0:2]

        label = d[:4] if granul == Granul.Year else d[:7]

        if year != last_year:
            xticks.append(i)
            xticklabels.append(label)
            last_year = year
            last_month = month

        elif month != last_month:
            if granul == Granul.Month:
                xticks.append(i)
                xticklabels.append(label)

            elif month in ("01", "07") and granul == Granul.Month6:
                xticks.append(i)
                xticklabels.append(label)

            last_month = month

    return xticks, xticklabels


def plot_chart(ticker: str, start: str, end: str):
    chart = read_chart(ticker, start, end)

    dates = [s.date for s in chart]

    try:
        fig = plt.figure(figsize=(20, 8))
    except Exception:
        plt.switch_backend("Agg")
        fig = plt.figure(figsize=(20, 8))
    ax1 = fig.add_subplot(111)

    ax1.plot([c.close_price for c in chart], color="black", label="price")

    xticks, xticklabels = get_ticks(dates, granul=Granul.Year)
    ax1.set_xticks(xticks)
    ax1.set_xticklabels(xticklabels)

    ax1.set_title(f"{ticker} ({dates[0]} ~ {dates[-1]}) ")
    ax1.legend()

    ax1.grid(axis="both")
    
    if matplotlib.get_backend().lower() == "agg":
        os.makedirs("figures", exist_ok=True)
        filepath = f"figures/{ticker}_chart_{start}_{end}.png"
        plt.savefig(filepath, bbox_inches="tight")
        print(f"[+] Saved plot to {filepath}")
    else:
        plt.show()


def plot_full(ticker: str, start: str, end: str, history: List[State]):
    dates = [s.date for s in history]
    exhausted = [
        i
        for i, s in enumerate(history)
        if s.status == Status.Exhausted and s.cycle != 0
    ]
    failed = [
        i
        for i, s in enumerate(history)
        if s.status == Status.Exhausted and s.cycle == 0
    ]
    sold = [i for i, s in enumerate(history) if s.status == Status.Sold]

    ymax = max(s.close_price for s in history)

    try:
        fig = plt.figure(figsize=(20, 8))
    except Exception:
        plt.switch_backend("Agg")
        fig = plt.figure(figsize=(20, 8))
    ax1 = fig.add_subplot(111)
    ax2 = ax1.twinx()

    ax1.plot([s.close_price for s in history], color="black", label="price")
    ax1.plot([s.avg_price for s in history], color="gray", label="avg_price")
    for x in exhausted:
        ax1.axvline(x, 0, ymax, color="tomato")
    for x in failed:
        ax1.axvline(x, 0, ymax, color="red")
    for x in sold:
        ax1.axvline(x, 0, ymax, color="green")

    ax2.plot([s.ror for s in history], color="blue", label="ror")

    xticks, xticklabels = get_ticks(dates, granul=Granul.Month6)
    ax1.set_xticks(xticks)
    ax1.set_xticklabels(xticklabels)

    ax1.set_title(f"{ticker} ({dates[0]} ~ {dates[-1]})")
    ax1.legend()

    ax1.set_ylabel("Stock price ($)")
    ax2.set_ylabel("Rate of return (RoR)")
    ax2.legend(loc="upper right")

    ax1.grid(axis="both")
    
    if matplotlib.get_backend().lower() == "agg":
        os.makedirs("figures", exist_ok=True)
        filepath = f"figures/{ticker}_full_{start}_{end}.png"
        plt.savefig(filepath, bbox_inches="tight")
        print(f"[+] Saved plot to {filepath}")
    else:
        plt.show()


def plot_dca(ticker: str, start: str, end: str, strategy_history: list, baseline_history: list):
    dates = [s.date for s in strategy_history]

    try:
        fig = plt.figure(figsize=(20, 8))
    except Exception:
        plt.switch_backend("Agg")
        fig = plt.figure(figsize=(20, 8))
    ax1 = fig.add_subplot(111)
    ax2 = ax1.twinx()

    # Plot stock price on left axis (ax1)
    ax1.plot([s.close_price for s in strategy_history], color="black", label="Stock Price", alpha=0.5)

    # Plot rates of return on right axis (ax2)
    ax2.plot([s.ror * 100 for s in strategy_history], color="blue", label="Strategy MWR (RoR %)")
    ax2.plot([s.twr * 100 for s in strategy_history], color="indigo", label="Strategy TWR (%)", alpha=0.8)
    ax2.plot([s.ror * 100 for s in baseline_history], color="green", linestyle="--", label="Baseline MWR (RoR %)")
    ax2.plot([s.twr * 100 for s in baseline_history], color="darkgreen", linestyle=":", label="Baseline TWR (%)", alpha=0.8)

    xticks, xticklabels = get_ticks(dates, granul=Granul.Month6)
    ax1.set_xticks(xticks)
    ax1.set_xticklabels(xticklabels)

    ax1.set_title(f"{ticker} DCA Simulation ({dates[0]} ~ {dates[-1]})")
    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")

    ax1.set_ylabel("Stock price ($)")
    ax2.set_ylabel("Rate of return (RoR %)")

    ax1.grid(axis="both")
    
    if matplotlib.get_backend().lower() == "agg":
        os.makedirs("figures", exist_ok=True)
        filepath = f"figures/{ticker}_dca_{start}_{end}.png"
        plt.savefig(filepath, bbox_inches="tight")
        print(f"[+] Saved plot to {filepath}")
    else:
        plt.show()
