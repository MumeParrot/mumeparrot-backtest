#!/bin/env python3

import os
import signal
import sys
from threading import Thread

from typing import Any, Type
from src.run import test
from src.configs import Config, best_configs

arg_str = ""

stop = [False]

# TICKERS = sorted([i[:-4].split('-')[0] for i in os.listdir('charts')
#                   if 'SIM-RSI' in i])
TICKERS = ['SOXL', 'TQQQ', 'SPXL', 'NAIL', 'TECL']

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
        max_cycles = get_arg("max_cycles", tpe=int, default=1)
        config = get_arg("config", tpe=str, default='best')
        if config != 'best':
            margin = get_arg("margin", tpe=float, default=0.05)
            margin_lose = get_arg("margin_lose", tpe=float, default=0.05)
            rsi_threshold = get_arg("rsi_threshold", tpe=int, default=80)
            burst_threshold = get_arg("burst_threshold", tpe=int, default=40)
            burst_rate = get_arg("burst_rate", tpe=float, default=1.5)
            margin_window = get_arg("margin_window", tpe=float, default=0.1)
            stoploss_threshold = get_arg("stoploss_threshold", tpe=float, default=0.4)
            sahm_threshold = get_arg("sahm_threshold", tpe=float, default=1)

            config = Config(margin, margin_lose, rsi_threshold, burst_threshold, 
                            burst_rate, margin_window, stoploss_threshold, sahm_threshold)
        
        else:
            config = best_configs[ticker]

        if stop[0]:
            print("")
            continue

        print_args()

        if ticker != 'all':
            test(ticker, max_cycles, config)

        else:
            for ticker in TICKERS:
                test(ticker, max_cycles, config)

if __name__ == "__main__":
    main()
