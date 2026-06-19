#!/usr/bin/env python3

import copy
import json
import click


@click.command()
@click.option(
    "--introduced",
    "-i",
    help="json file of new tickers introduced in MumeParrot app (List<Ticker>)",
    required=True,
)
@click.option(
    "--output",
    "-o",
    help="json file to update with new tickers (Dict<Ticker, Dict<String, String>>)",
    default="./tickers.json",
)
def main(introduced, output):
    with open(output, "r") as fd:
        old_tickers = {k.replace("_", "."): v for k, v in json.load(fd).items()}

    with open(introduced, "r") as fd:
        updated_tickers = [t.replace("_", ".") for t in json.load(fd)]

    new_tickers = copy.deepcopy(old_tickers)
    for t in updated_tickers:
        if t not in old_tickers:
            print(f"Tell the base of {t}: ")
            base = input()
            print(f"Tell the leverage of {t}: ")
            leverage = int(input() or "1")
            new_tickers[t] = {
                "base": base or t,
                "leverage": leverage,
                "start-year": 1900,
                "end-year": 1900,
            }

    with open(output, "w") as fd:
        json.dump(new_tickers, fd, indent=4, sort_keys=True, ensure_ascii=False)


if __name__ == "__main__":
    main()
