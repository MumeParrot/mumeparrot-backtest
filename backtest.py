#!/bin/env python3

import os
import copy
import sys
import numpy as np

from typing import Any, Type
from dataclasses import asdict

from src.test import test
from src.full import full
from src.plot import plot_chart, plot_full

from src.configs import Config, Description
from src.env import (
    START,
    END,
    TICKERS,
    BEST_CONFIGS,
    GRAPH,
    BOXX,
    TEST_MODE,
    print_env,
    LEVERAGES,
)

stop = [False]


def sigint_handler(sig, frame):
    stop[0] = True


def get_arg(
    name: str, default: Any = None, tpe: Type = None, explain: str = None
) -> Any:
    # assert default is not None or tpe is not None
    default_var = (
        "y" if default is True else "n" if default is False else default
    )
    default_str = f" [default={default_var}]" if default is not None else ""
    tpe = tpe or type(default)

    explain_text = f"({explain})" if explain else ""

    print(f"{name}{default_str}{explain_text}: ", end="")

    try:
        arg = input()
    except KeyboardInterrupt:
        stop[0] = True
        print("")
        raise RuntimeError("stop = True")

    try:
        if tpe is bool:
            if arg:
                var = True if arg == "y" else False
            else:
                var = default
        else:
            var = (
                tpe(arg or default)
                if default is not None
                else tpe(arg) if arg else None
            )
    except TypeError as e:
        print(f"[-] Invalid argument '{arg}' for {name}")
        sys.exit(0)

    return var


def main():
    print_env()

    while True:
        stop[0] = False

        config_fields = {}

        try:
            mode: str = get_arg("mode", tpe=str, default="p")
            if mode.startswith("p"):  # plot
                ticker = get_arg("ticker", tpe=str, default="all")
                plot_chart(ticker, START, END)

            elif mode.startswith("t"):  # test
                if BOXX:
                    print("[-] Test mode not supported with BOXX")
                    sys.exit(0)

                ticker = get_arg("ticker", tpe=str, default="all")
                config: str = get_arg(
                    "config",
                    tpe=str,
                    default="best",
                    explain="type 'n' to manually set",
                )

                if config != "best":
                    for field, value in asdict(Config()).items():
                        default_val = (
                            None
                            if ticker == "all"
                            else getattr(BEST_CONFIGS[ticker], field)
                        )
                        config_fields[field] = get_arg(
                            field, tpe=type(value), default=default_val
                        )

                if ticker != "all":
                    config = copy.deepcopy(BEST_CONFIGS[ticker])
                    for k, v in config_fields.items():
                        if v is not None:
                            setattr(config, k, v)

                    test(ticker, config, START, END)

                else:
                    for ticker in TICKERS.keys():
                        config = copy.deepcopy(BEST_CONFIGS[ticker])
                        for k, v in config_fields.items():
                            if v is not None:
                                setattr(config, k, v)

                        test(ticker, config, START, END)

            elif mode.startswith("f"):
                ticker = get_arg("ticker", tpe=str, default="SOXL")

                is_dca = LEVERAGES.get(ticker) < 3

                if is_dca:
                    start_date = get_arg(
                        "start_date", tpe=str, default=START or "2020-01-01"
                    )
                    end_date = get_arg(
                        "end_date", tpe=str, default=END or "2026-01-01"
                    )
                    rsi_threshold = get_arg(
                        "rsi_threshold", tpe=float, default=50.0
                    )
                    buy_splits = get_arg(
                        "buy_splits",
                        tpe=int,
                        default=5,
                        explain="how to split remaining seed for buying stock at a time",
                    )
                    monthly_wage = get_arg(
                        "monthly_wage", tpe=float, default=1000.0
                    )
                    inflation_rate = get_arg(
                        "inflation_rate", tpe=float, default=0.03
                    )

                    from datetime import datetime
                    from src.data import read_chart
                    from src.dca import compute_dca_rsi, run_dca_backtest
                    from src.plot import plot_dca

                    full_chart = read_chart(ticker, "", "", test_mode=TEST_MODE)
                    chart = [c for c in full_chart if start_date <= c.date <= end_date]

                    if not chart:
                        print(
                            f"[-] No stock data found for ticker '{ticker}' in range {start_date} ~ {end_date}"
                        )
                        continue

                    rsi_dict = compute_dca_rsi(full_chart)
                    strat_history, base_history = run_dca_backtest(
                        chart,
                        rsi_dict,
                        rsi_threshold,
                        buy_splits,
                        monthly_wage,
                        inflation_rate,
                    )

                    n_days = (
                        datetime.strptime(chart[-1].date, "%Y-%m-%d")
                        - datetime.strptime(chart[0].date, "%Y-%m-%d")
                    ).days
                    if n_days <= 0:
                        n_days = 1

                    strat_avg_ir = (1.0 + strat_history[-1].ror) ** (
                        365.0 / n_days
                    ) - 1.0
                    base_avg_ir = (1.0 + base_history[-1].ror) ** (
                        365.0 / n_days
                    ) - 1.0

                    print(f"[{ticker}] {chart[0].date} ~ {chart[-1].date}")
                    print(
                        f"\tTotal Invested Capital (inflation-adjusted): {strat_history[-1].invested:.2f}"
                    )
                    print(
                        f"\tStrategy Final Value: {strat_history[-1].value:.2f}"
                    )
                    strat_twr_ann = (1.0 + strat_history[-1].twr) ** (365.0 / n_days) - 1.0
                    base_twr_ann = (1.0 + base_history[-1].twr) ** (365.0 / n_days) - 1.0

                    print(
                        f"\tStrategy RoR (Money-Weighted): {strat_history[-1].ror * 100:.2f}% ({strat_avg_ir * 100:.2f}% annualized)"
                    )
                    print(
                        f"\tStrategy TWR (Time-Weighted): {strat_history[-1].twr * 100:.2f}% ({strat_twr_ann * 100:.2f}% annualized)"
                    )
                    n_bought = sum(1 for s in strat_history if s.bought)
                    bought_pct = (n_bought / len(strat_history)) * 100.0 if strat_history else 0.0
                    print(
                        f"\tStrategy Bought Days: {n_bought}/{len(strat_history)} ({bought_pct:.2f}%)"
                    )
                    print(
                        f"\tBaseline Final Value: {base_history[-1].value:.2f}"
                    )
                    print(
                        f"\tBaseline RoR (Money-Weighted): {base_history[-1].ror * 100:.2f}% ({base_avg_ir * 100:.2f}% annualized)"
                    )
                    print(
                        f"\tBaseline TWR (Time-Weighted): {base_history[-1].twr * 100:.2f}% ({base_twr_ann * 100:.2f}% annualized)"
                    )

                    if GRAPH:
                        plot_dca(
                            ticker,
                            start_date,
                            end_date,
                            strat_history,
                            base_history,
                        )

                else:
                    config: str = get_arg("config", tpe=str, default="best")

                    if config != "best":
                        for field, value in asdict(Config()).items():
                            default_val = getattr(BEST_CONFIGS[ticker], field)
                            config_fields[field] = get_arg(
                                field, tpe=type(value), default=default_val
                            )

                    config = copy.deepcopy(BEST_CONFIGS[ticker])
                    for k, v in config_fields.items():
                        if v is not None:
                            setattr(config, k, v)

                    history, _ = full(
                        ticker, config, START, END, test_mode=TEST_MODE
                    )
                    if GRAPH:
                        plot_full(ticker, START, END, history)

            elif mode.startswith("h"):
                tickers = ""
                for i, ticker in enumerate(TICKERS.keys()):
                    tickers += f"{ticker}, "
                    if i % 5 == 4:
                        tickers += "\n   "
                tickers = tickers[:-2]

                print("=== MumeParrot backtest ===")
                print("Usage: python3 backtest.py")
                print(" Modes:")
                print("  -h) print this help message")
                print("  -t) sliding window test")
                print("  -f) full simulation")
                print(" Tickers:")
                print("   all, " + tickers)
                print(" Config:")
                for field, value in asdict(Description()).items():
                    print(f"  {field}: {value}")
                print("(Environment variables)")
                print(
                    " TICKER_FILE: path to ticker file (default: tickers.json)"
                )
                print(
                    " CONFIGS_FILE: path to best configs file (default: configs.json)"
                )
                print(
                    " START: start date in 'yyyy-mm-dd' format, either 'yyyy' or 'yyyy-mm' are allowed also (default: empty)"
                )
                print(
                    " END: end date in 'yyyy-mm-dd' format, either 'yyyy' or 'yyyy-mm' are allowed also (default: empty)"
                )
                print(
                    " CYCLE_DAYS: number of days to simulate per each cycle (default: 60)"
                )
                print(" SEED: amount of seed (default: 1000000)")
                print(" MAX_CYCLES: maximum cycles (default: 2)")
                print(
                    " FAIL_PENALTY: penalty for cycle failure when optimization (default: 2)"
                )
                print(
                    " FAIL_LIMIT: limit for cycle failure when optimization (default: 0.1)"
                )
                print(
                    " DEBUG: set to log history under 'logs/test (default: 0)"
                )
                print(" VERBOSE: set to print history (default: 0)")
                print(" GRAPH: print graph when full simulation (default: 0)")

        except RuntimeError:
            continue


if __name__ == "__main__":
    main()
