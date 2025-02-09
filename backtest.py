#!/bin/env python3

import os
import copy
import sys
import numpy as np

from typing import Any, Type
from dataclasses import asdict
from scipy.optimize import minimize, differential_evolution
from src.run import test
from src.utils import TICKERS, plot_graph
from src.configs import Bounds, Precisions, Config, best_configs

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
    max_cycles = int(os.environ.get("MAX_CYCLES", 2))
    start = os.environ.get("START", "")
    end = os.environ.get("END", "")
    verbose = os.environ.get("VERBOSE", 0)

    while True:
        stop[0] = False

        config_fields = {}

        try:
            mode: str = get_arg("mode", tpe=str, default="p")
            if mode.startswith("p"):  # plot
                ticker = get_arg("ticker", tpe=str, default="all")
                plot_graph(ticker, start, end)

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

                    test(ticker, max_cycles, config, start, end, verbose)

                else:
                    for ticker in TICKERS.keys():
                        config = copy.deepcopy(best_configs[ticker])
                        for k, v in config_fields.items():
                            if v is not None:
                                setattr(config, k, v)

                        test(ticker, max_cycles, config, start, end, verbose)

            elif mode.startswith("o"):
                ticker = get_arg("ticker", tpe=str, default=None)
                if ticker is None:
                    raise RuntimeError()

                config = best_configs[ticker]
                _bounds = Bounds()
                _precisions = Precisions()

                variables = []
                fixed = {}
                bounds = []

                for field, value in asdict(Config()).items():
                    config_fields[field] = get_arg(
                        field, tpe=type(value), default=None
                    )

                for k, v in config_fields.items():
                    if v is not None:
                        variables.append(v)
                        bounds.append(getattr(_bounds, k))

                    else:
                        fixed[k] = getattr(config, k)

                def _test(vars: np.ndarray):
                    vars = vars.tolist()

                    _config = {}
                    for k in asdict(Config()).keys():
                        if k in fixed:
                            _config[k] = fixed[k]
                        else:
                            _config[k] = vars.pop(0)

                    for k, v in _config.items():
                        p = getattr(_precisions, k)
                        _config[k] = int(v / p) * p

                    return -test(
                        ticker,
                        max_cycles,
                        Config(**_config),
                        start,
                        end,
                        verbose,
                    )

                opt = differential_evolution(
                    _test,
                    bounds=bounds,
                    # method="L-BFGS-B",
                    # options={"eps": 0.01},
                )
                print(f"result: {opt.fun}, best: {opt.x}")

        except RuntimeError:
            continue


if __name__ == "__main__":
    main()
