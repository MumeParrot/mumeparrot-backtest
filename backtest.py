#!/bin/env python3

import os
import copy
import sys

from typing import Any, Type
from dataclasses import asdict
from src.run import test
from src.utils import TICKERS, plot_graph
from src.configs import Config, best_configs, print_config

MAX_CYCLES = 2

stop = [False]


def sigint_handler(sig, frame):
    print("stop = True")
    stop[0] = True


def get_arg(name: str, default: Any = None, tpe: Type = None) -> Any:
    # assert default is not None or tpe is not None
    if stop[0]:
        return

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
        return

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
    verbose = os.environ.get("VERBOSE", 0)

    while True:
        stop[0] = False

        plot = get_arg("plot", tpe=bool, default=False)
        ticker = get_arg("ticker", tpe=str, default="all")
        config = get_arg("config", tpe=str, default="best")

        if stop[0] is True:
            print("")
            continue

        args = {}

        if plot:
            plot_graph(ticker, start, end)
            continue

        if config != "best":
            for field, value in asdict(Config()).items():
                args[field] = get_arg(field, tpe=type(value), default=None)

        if ticker != "all":
            config = copy.deepcopy(best_configs[ticker])
            for k, v in args.items():
                if v is not None:
                    setattr(config, k, v)

        if stop[0]:
            print("")
            continue

        if ticker != "all":
            print_config(config)
            test(ticker, 2, config, start, end)

        else:
            for ticker in TICKERS.keys():
                if config == "best":
                    c = best_configs[ticker]
                else:
                    c = copy.deepcopy(best_configs[ticker])
                    for k, v in args.items():
                        if v is not None:
                            setattr(c, k, v)

                print_config(c)
                test(ticker, MAX_CYCLES, c, start, end)


if __name__ == "__main__":
    main()
