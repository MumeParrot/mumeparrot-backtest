#!/usr/bin/env python3

import os
import sys
import click

import numpy as np

from dataclasses import asdict
from scipy.optimize import differential_evolution

from src.run import test
from src.utils import TICKERS
from src.configs import Bounds, Precisions, Config, best_configs


@click.command()
@click.option("--ticker", "-t", required=True, type=str)
@click.option("--fixed", "-f", required=True, type=str)
def optimize(ticker, fixed):
    max_cycles = int(os.environ.get("MAX_CYCLES", 2))
    start = os.environ.get("START", "")
    end = os.environ.get("END", "")
    verbose = os.environ.get("VERBOSE", 0)

    if ticker not in TICKERS.keys():
        raise RuntimeError(f"Unknown ticker: {ticker}")

    fixed = [t.split(":") for t in fixed.split(",")]
    try:
        fixed = {t[0]: t[1] for t in fixed}
    except:
        raise RuntimeError(f"Invalid format for fixed")

    config = best_configs[ticker]
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

        return -test(ticker, max_cycles, Config(**_config), start, end, verbose)

    opt = differential_evolution(_test, bounds=bounds)
    print(f"Result: {opt.fun}, Best args: {opt.x}")


if __name__ == "__main__":
    optimize()
