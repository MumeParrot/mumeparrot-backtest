#!/bin/env python3

import os
import copy
import sys
import numpy as np

from typing import Any, Type
from dataclasses import asdict

from src.test import test
from src.full import full
from src.plot import plot_chart, plot_sim

from src.configs import Config, Description
from src.env import TICKERS, BEST_CONFIGS, GRAPH

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
        print(f"Invalid argument '{arg}' for {name}")
        sys.exit(0)

    return var


def main():
    start = os.environ.get("START", "")
    end = os.environ.get("END", "")

    while True:
        stop[0] = False

        config_fields = {}

        try:
            mode: str = get_arg("mode", tpe=str, default="p")
            if mode.startswith("p"):  # plot
                ticker = get_arg("ticker", tpe=str, default="all")
                plot_chart(ticker, start, end)

            elif mode.startswith("t"):  # test
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

                    test(ticker, config, start, end)

                else:
                    for ticker in TICKERS.keys():
                        config = copy.deepcopy(BEST_CONFIGS[ticker])
                        for k, v in config_fields.items():
                            if v is not None:
                                setattr(config, k, v)

                        test(ticker, config, start, end)

            elif mode.startswith("f"):
                ticker = get_arg("ticker", tpe=str, default="SOXL")
                config: str = get_arg("config", tpe=str, default="best")

                if config != "best":
                    for field, value in asdict(Config()).items():
                        config_fields[field] = get_arg(
                            field, tpe=type(value), default=None
                        )

                config = copy.deepcopy(BEST_CONFIGS[ticker])
                for k, v in config_fields.items():
                    if v is not None:
                        setattr(config, k, v)

                history = full(ticker, config, start, end)
                if GRAPH:
                    plot_sim(ticker, start, end, history)

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
