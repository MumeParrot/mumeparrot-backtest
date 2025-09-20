#!/usr/bin/env python3

import os
import sys
import time
import json
import random
import click
import gspread

import pandas as pd
import matplotlib.pyplot as plt

from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

OLDEST = "1980-01-01"

gc: gspread.Client = None


@click.command()
@click.option(
    "--input",
    "-i",
    help="json file containing key, value map of 3-times ticker and 1-times base ticker (default: tickers.json)",
    default="tickers.json",
)
@click.option("--graph", "-g", is_flag=True, help="Draw graph for each ticker")
def main(input, graph):
    try:
        gc = gspread.service_account(filename="bot.json")
    except Exception as e:
        print(f"Error getting gspread service account\n${e}")
        sys.exit(0)
    finally:
        if not gc:
            print(f"Error getting gspread service account")
            sys.exit(0)

    os.makedirs("charts", exist_ok=True)

    tickers: Dict[str, Dict[str, str]] = None
    try:
        with open(input, "r") as fd:
            tickers = json.loads(fd.read())
    except:
        print(f"Error loading {input}")
        sys.exit(0)

    for ticker, value in tickers.items():
        base = value["base"]

        print(f"Processing {ticker} ({base})...")

        try:
            chart = pd.read_csv(f"charts/{ticker}.csv")
            base_chart = pd.read_csv(f"charts/{base}.csv")

            new_chart = fetch(gc, ticker, chart.iloc[-1].Date)
            if new_chart is not None:
                chart = pd.concat([chart, new_chart])

            new_base_chart = fetch(gc, base, base_chart.iloc[-1].Date)
            if new_base_chart is not None:
                base_chart = pd.concat([base_chart, new_base_chart])

            if chart.iloc[-1].Date != base_chart.iloc[-1].Date:
                print(
                    f"Chart data deviate: {ticker}[{new_chart.iloc[-1].Date}] vs. {base}[{new_base_chart.iloc[-1].Date}]"
                )

        except FileNotFoundError:
            chart = fetch(gc, ticker, OLDEST)
            base_chart = fetch(gc, base, OLDEST)

        except KeyError as e:
            raise e

        chart.to_csv(f"charts/{ticker}.csv", index=False)
        base_chart.to_csv(f"charts/{base}.csv", index=False)

        merged, generated = process(chart, base_chart)

        if graph:
            plot(ticker, merged, generated)

        merged_to_csv = [f"{i[0]},{i[1][0]},{i[1][1]}\n" for i in merged]
        with open(f"charts/{ticker}-GEN.csv", "w") as fd:
            fd.writelines(merged_to_csv)

        value["start-year"] = int(merged[0][0][:4])
        value["end-year"] = int(merged[-1][0][:4])

        time.sleep(10)  # sleep 10 every fetch to avoid rate limit

    with open(input, "w") as fd:
        fd.write(json.dumps(tickers, indent=2))


def fetch(
    gc: gspread.Client, ticker: str, latest: str
) -> Optional[pd.DataFrame]:
    start = datetime.strptime(latest, "%Y-%m-%d")
    start += timedelta(days=1)

    end = datetime.now()

    if end < start:
        return None

    tmp = f"{ticker}-{random.randint(0, 10000)}"
    start = f"DATE({start.year}, {start.month}, {start.day})"
    end = f"DATE({end.year}, {end.month}, {end.day})"

    file = gc.open("mumeparrot-backtest-notepad")
    sheet = file.add_worksheet(title=tmp, rows=1, cols=1)
    sheet.update(
        [[f'=GOOGLEFINANCE("{ticker}", "all", {start}, {end}, "DAILY")']],
        "A1",
        value_input_option="USER_ENTERED",
    )

    import time

    wait = 5
    while True:
        time.sleep(1)
        if sheet.acell("A1").value == "#N/A":
            wait -= 1
            if wait > 0:
                continue

            print(f"No data fetched for {start} ~ {end}")
            return None

        else:
            break

    df = pd.DataFrame(sheet.get_all_records())

    for i in range(len(df)):
        d = df.loc[i, "Date"].split(" ")
        y = d[0].strip().strip(".")
        m = d[1].strip().strip(".")
        d = d[2].strip().strip(".")

        m = f"0{m}" if len(m) == 1 else m
        d = f"0{d}" if len(d) == 1 else d

        df.loc[i, "Date"] = f"{y}-{m}-{d}"

    file.del_worksheet(sheet)

    # XRT (base of RETL) has strange row, just remove it
    if ticker == "XRT" and latest == OLDEST:
        tmp = df.iloc[2319]
        df.iloc[2319] = df.iloc[2318]
        df.iloc[2319]["Date"] = tmp["Date"]

    return df


def process(triple: pd.DataFrame, base: pd.DataFrame) -> Tuple[List]:

    init = base.iloc[0]
    date, o_price, c_price = (
        init["Date"],
        init["Open"],
        init["Close"],
    )

    rates: List[Tuple[str, Tuple[float]]] = [
        (date, (0, 3 * (c_price - o_price) / o_price))
    ]
    for i in range(1, len(base)):
        prev_c_price = base.iloc[i - 1]["Close"]

        today = base.iloc[i]
        date, o_price, c_price = (
            today["Date"],
            today["Open"],
            today["Close"],
        )

        o_rate = (o_price - prev_c_price) / prev_c_price
        c_rate = (c_price - o_price) / o_price

        rates.append((date, (3 * o_rate, 3 * c_rate)))

    ref_init = triple.iloc[0]
    ref_init_date, ref_o_price = (
        ref_init["Date"],
        ref_init["Open"],
    )

    index: int = None
    try:
        index = [i[0] for i in rates].index(ref_init_date)
    except:
        print(f'Cannot find "{ref_init_date}" from base chart')
        sys.exit(0)

    match_o_price = ref_o_price
    match_c_price = match_o_price * (1 + rates[index][1][1])

    gen_prices = [(ref_init_date, (match_o_price, match_c_price))]
    for r in rates[index + 1 :]:
        date, (o_rate, c_rate) = r

        last_c_price = gen_prices[-1][1][1]
        o_price = last_c_price * (1 + o_rate)
        c_price = o_price * (1 + c_rate)

        gen_prices.append((date, (o_price, c_price)))

    last_o_rate = rates[index][1][0]
    prev_c_price = match_o_price * (1 / (1 + last_o_rate))
    for r in rates[index - 1 :: -1]:
        date, (o_rate, c_rate) = r

        prev_o_price = prev_c_price * (1 / (1 + c_rate))
        gen_prices.insert(0, (date, (prev_o_price, prev_c_price)))

        prev_c_price = prev_o_price * (1 / (1 + o_rate))

    ref_prices = []
    for i in range(len(triple)):
        r = triple.iloc[i]

        ref_prices.append((r["Date"], (r["Open"], r["Close"])))

    merged_prices = gen_prices[:index] + ref_prices

    return merged_prices, gen_prices


def plot(ticker: str, merged: List, generated: List):
    fig = plt.figure(figsize=(20, 8))
    ax = fig.add_subplot(111)

    dates = [i[0] for i in merged]
    merged_prices = [i[1][1] for i in merged]
    gen_prices = [i[1][1] for i in generated]

    ax.plot(merged_prices, label="merged")
    ax.plot(gen_prices, label="generated")

    xticks = []
    xticklabels = []

    last_year = ""
    for i, d in enumerate(dates):
        year, m = d.split("-")[0:2]

        if year != last_year and m == "01":
            xticks.append(i)
            xticklabels.append(d[0:4])
            last_year = year

    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels)

    ax.set_title(ticker)
    ax.legend()

    ax.grid(axis="y")

    plt.show()


if __name__ == "__main__":
    main()
