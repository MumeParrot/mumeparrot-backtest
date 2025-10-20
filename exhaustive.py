#!/usr/bin/env python3

import os
import sys
import click
import itertools

import numpy as np
from typing import Dict, List, Union

from dataclasses import asdict
from scipy.optimize import differential_evolution

from src.test import test
from src.full import full
from src.utils import analyze_result

from src.configs import Bounds, Precisions, Config
from src.env import TICKERS, BEST_CONFIGS, START, END, print_env


@click.command()
@click.option(
    "--ticker",
    "-t",
    required=False,
    default="SOXL",
    type=click.Choice(list(TICKERS.keys())),
)
@click.option(
    "--fixed",
    "-f",
    required=False,
    default="",
    type=str,
    help="Fixed config parameters",
)
def exhaust(ticker, fixed):
    print_env()

    if ticker not in TICKERS.keys():
        raise RuntimeError(f"Unknown ticker: {ticker}")

    fixed = [t.split(":") for t in fixed.split(",")] if fixed else []
    try:
        fixed = {t[0]: t[1] for t in fixed}
    except:
        raise RuntimeError(f"Invalid format for fixed")

    config = BEST_CONFIGS[ticker]
    bounds = Bounds()
    precisions = Precisions()

    variables: Dict[str, List[Union[int, float]]] = {}
    for k, v in asdict(config).items():
        if k in fixed:
            tpe = type(v)
            variables[k] = [tpe(fixed[k])]

        else:
            start, end = getattr(bounds, k)
            precision = getattr(precisions, k)

            variables[k] = [
                start + i * precision
                for i in range(0, int((end - start) / precision) + 1)
            ]

    combinations = list(itertools.product(*variables.values()))

    configs = []
    for c in combinations:
        conf = Config._from(dict(zip(variables.keys(), c)))
        configs.append(conf)

    for config in configs:
        _, _, score = test(ticker, config, START, END)


if __name__ == "__main__":
    exhaust()
