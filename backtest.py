#!/bin/env python3

import signal
import sys
from threading import Thread

from typing import Any, Type
from src.sim import run

arg_str = ""

stop = [False]


def sigint_handler(sig, frame):
    print("stop = True")
    stop[0] = True


def restart(sig, frame):
    print("Restart")


def get_arg(name: str, default: Any = None, tpe: Type = None) -> Any:
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
        stop[0] = True
        return

    try:
        if tpe is bool:
            if arg:
                var = True if arg == "y" else False
            else:
                var = default
        else:
            var = tpe(arg or default) if default else tpe(arg)
    except TypeError as e:
        print(f"Invalid argument '{arg}' for {name}")
        sys.exit(0)

    global arg_str
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

        ticker = get_arg("ticker", tpe=str)
        principal = get_arg("principal", default=10000)
        start = get_arg("start", default="init")
        end = get_arg("end", default="fin")

        if stop[0]:
            print("")
            continue

        print_args()

        run(ticker, principal, start, end)


if __name__ == "__main__":
    main()
