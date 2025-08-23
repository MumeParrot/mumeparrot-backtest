#!/usr/bin/env python3

import os
import sys
import click

import numpy as np

from dataclasses import asdict
from scipy.optimize import differential_evolution

from src.test import test
from src.utils import analyze_result

from src.configs import Bounds, Precisions, Config
from src.env import TICKERS, BEST_CONFIGS, START, END, print_env


@click.command()
@click.option(
    "--mode",
    "-m",
    default="o",
    type=click.Choice(["o", "a"]),
    help="Optimize or analyze",
)
@click.option(
    "--directory", "-d", required=False, help="Directory to save results"
)
@click.option(
    "--ticker", "-t", required=False, type=click.Choice(list(TICKERS.keys()))
)
@click.option(
    "--fixed", "-f", required=False, type=str, help="Fixed config parameters"
)
def optimize(mode, directory, ticker, fixed):
    print_env()

    if mode == "a":
        for ticker in TICKERS.keys():
            print(f"====== {ticker} ======")
            analyze_result(directory, ticker)
            print(f"======================")

        sys.exit()

    if ticker not in TICKERS.keys():
        raise RuntimeError(f"Unknown ticker: {ticker}")

    fixed = [t.split(":") for t in fixed.split(",")]
    try:
        fixed = {t[0]: t[1] for t in fixed}
    except:
        raise RuntimeError(f"Invalid format for fixed")

    config = BEST_CONFIGS[ticker]
    _bounds = Bounds()

    variables = []
    _fixed = {}
    bounds = []
    _precisions = Precisions()

    for k, v in asdict(config).items():
        if k in fixed:
            tpe = type(v)
            _fixed[k] = tpe(fixed[k])

        else:
            variables.append(v)
            bounds.append(getattr(_bounds, k))

    def _test(vars: np.ndarray):
        vars = vars.tolist()

        _config = {}
        for k in asdict(config).keys():
            if k in _fixed:
                _config[k] = _fixed[k]
            else:
                _config[k] = vars.pop(0)

        for k, v in _config.items():
            p = getattr(_precisions, k)
            _config[k] = int(v / p) * p

        _, _, score = test(ticker, Config(**_config), START, END)
        return -score

    opt = differential_evolution(_test, bounds=bounds)
    print(f"Result: {opt.fun}, Best args: {opt.x}")


if __name__ == "__main__":
    optimize()
