import os
import re
import matplotlib
from typing import List, Tuple
from enum import Enum

import matplotlib.pyplot as plt

from .const import Status, State
from .data import (read_chart,
        compute_urates,
        compute_quad_var
)
from .env import CYCLE_DAYS

# matplotlib.use("TkAgg")


class Granul(Enum):
    Month = 0
    Month6 = 1
    Year = 2
    Year2 = 3 


def get_ticks(dates: List[str], granul: Granul = Granul.Year):
    xticks = []
    xticklabels = []

    last_year = ""
    last_month = ""
    for i, d in enumerate(dates):
        year, month = d.split("-")[0:2]

        label = d[:4] if (granul == Granul.Year or granul == Granul.Year2) else d[:7]
        
        if granul == Granul.Year2:
            if year != last_year and int(year) % 2 == 0:        
                xticks.append(i)
                xticklabels.append(label)
                last_year = year
                last_month = month

        elif year != last_year:
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

    fig = plt.figure(figsize=(20, 8))
    ax1 = fig.add_subplot(111)

    ax1.plot([c.close_price for c in chart], color="black", label="price")

    xticks, xticklabels = get_ticks(dates, granul=Granul.Year)
    ax1.set_xticks(xticks)
    ax1.set_xticklabels(xticklabels)

    ax1.set_title(f"{ticker} ({dates[0]} ~ {dates[-1]}) ")
    ax1.legend()

    ax1.grid(axis="both")
    plt.show()


def plot_sim(ticker: str, start: str, end: str, history: List[State]):
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
    plt.show()
    # plt.savefig(
    #     f"figures/{ticker}:{history[0].date}-{history[-1].date}.png",
    #     bbox_inches="tight",
    # )
