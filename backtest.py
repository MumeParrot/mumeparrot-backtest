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

from src.configs import best_configs, Config
from src.env import TICKERS

stop = [False]


def sigint_handler(sig, frame):
    stop[0] = True


def get_arg(name: str, default: Any = None, tpe: Type = None) -> Any:
    # assert default is not None or tpe is not None
    default_var = (
        "y" if default is True else "n" if default is False else default
    )
    default_str = f" [default={default_var}]" if default is not None else ""
    tpe = tpe or type(default)

    print(f"{name}{default_str}: ", end="")

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
                config: str = get_arg("config", tpe=str, default="best")

                if config != "best":
                    for field, value in asdict(Config()).items():
                        config_fields[field] = get_arg(
                            field, tpe=type(value), default=None
                        )

                if ticker != "all":
                    config = copy.deepcopy(best_configs[ticker])
                    for k, v in config_fields.items():
                        if v is not None:
                            setattr(config, k, v)

                    test(ticker, config, start, end)

                else:
                    for ticker in TICKERS.keys():
                        config = copy.deepcopy(best_configs[ticker])
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

                config = copy.deepcopy(best_configs[ticker])
                for k, v in config_fields.items():
                    if v is not None:
                        setattr(config, k, v)

                history = full(ticker, config, start, end)
                plot_sim(ticker, start, end, history)

        except RuntimeError:
            continue


if __name__ == "__main__":
    main()
