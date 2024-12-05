#!/bin/env python3

import os
import signal
import sys
from threading import Thread

from typing import Any, Type
# from src.sim import run
from src.run import test

arg_str = ""

stop = [False]

TICKERS = sorted([i[:-4].split('-')[0] for i in os.listdir('charts')
                  if 'SIM-RSI' in i])

def sigint_handler(sig, frame):
    print("stop = True")
    stop[0] = True


def restart(sig, frame):
    print("Restart")


def get_arg(name: str, default: Any = None, tpe: Type = None) -> Any:
    global arg_str

    assert default is not None or tpe is not None

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
        arg_str = ""
        stop[0] = True
        return

    try:
        if tpe is bool:
            if arg:
                var = True if arg == "y" else False
            else:
                var = default
        else:
            var = tpe(arg or default) if default is not None else tpe(arg)
    except TypeError as e:
        print(f"Invalid argument '{arg}' for {name}")
        sys.exit(0)

    arg_str += f"{name + ':':<20}{str(var).upper()}\n"

    return var


def print_args():
    global arg_str
    print(
        f"""
===========================================================
{arg_str}
===========================================================
"""
    )

    arg_str = ""


def main():
    while True:
        stop[0] = False

        ticker = get_arg("ticker", tpe=str, default='all')
        term = get_arg("term", tpe=int, default=40)
        seed = get_arg("seed", tpe=int, default=100000)
        margin = get_arg("margin", tpe=float, default=0.05)
        max_cycles = get_arg("max_cycles", tpe=int, default=2)
        rsi_threshold = get_arg("rsi_threshold", tpe=int, default=80)
        burst_threshold = get_arg("burst_threshold", tpe=int, default=40)
        burst_rate = get_arg("burst_rate", tpe=float, default=1.5)
        margin_window = get_arg("margin_window", tpe=float, default=0.1)
        base_margin_lose = get_arg("base_margin_lose", tpe=float, default=0.05)
        sahm_threshold = get_arg("sahm_threshold", tpe=float, default=1)

        # principal = get_arg("principal", default=10000)
        # start = get_arg("start", default="init")
        # end = get_arg("end", default="fin")

        if stop[0]:
            print("")
            continue

        print_args()

        if ticker != 'all':
            test(ticker, term, seed, margin ,max_cycles, 
                rsi_threshold, burst_threshold, burst_rate, margin_window,
                base_margin_lose, sahm_threshold)

        else:
            for ticker in TICKERS:
                test(ticker, term, seed, margin , max_cycles, 
                     rsi_threshold, burst_threshold, burst_rate, margin_window,
                     base_margin_lose, sahm_threshold)


if __name__ == "__main__":
    main()
