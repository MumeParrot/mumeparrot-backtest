#!/usr/bin/python3

import csv
import sys
import click
import matplotlib
import matplotlib.pyplot as plt

from pprint import pprint


@click.command()
@click.option(
    "--input", "-i", required=True, help="one-time leverage chart to triplify"
)
@click.option("--output", "-o", required=True, help="output chart name")
def main(input: str, output: str):
    print(f"Triplify {input} to {output}")

    try:
        with open(f"charts/{input}.csv", "r") as fd:
            input_chart = list(csv.reader(fd))
    except FileNotFoundError:
        print(f"[-] charts/{input}.csv does not exist")
        sys.exit(0)

    try:
        with open(f"charts/{output}.csv", "r") as fd:
            ref_chart = list(csv.reader(fd))
    except FileNotFoundError:
        print(f"[-] charts/{output}.csv does not exist")
        sys.exit(0)

    input_prices = [(i[0], (float(i[1]), float(i[4]))) for i in input_chart[1:]]
    ref_prices = [(i[0], (float(i[1]), float(i[4]))) for i in ref_chart[1:]]

    date, (open_price, close_price) = input_prices[0]
    input_rates = [(date, (0, (close_price - open_price) / open_price))]
    for i, t in enumerate(input_prices[1:]):
        prev_close_price = input_prices[i][1][1]
        date, (open_price, close_price) = t

        open_rate = (open_price - prev_close_price) / prev_close_price
        close_rate = (close_price - open_price) / open_price

        input_rates.append((date, (3 * open_rate, 3 * close_rate)))

    print(f"[*] {input} start date: {input_rates[0][0]}")
    print(f"[*] {output} start date: {ref_prices[0][0]}")

    init_date, init_open_price = ref_prices[0][0], ref_prices[0][1][0]
    try:
        index = [i[0] for i in input_rates].index(init_date)
    except ValueError:
        print(f"[-] {input} chart does not contain {init_date}")
        sys.exit(0)

    init_close_rate = input_rates[index][1][1]
    init_close_price = init_open_price * (1 + init_close_rate)

    output_prices = [(init_date, (init_open_price, init_close_price))]
    for t in input_rates[index + 1 :]:
        date, (open_rate, close_rate) = t

        last_close_price = output_prices[-1][1][1]
        open_price = last_close_price * (1 + open_rate)
        close_price = open_price * (1 + close_rate)

        output_prices.append((date, (open_price, close_price)))

    init_open_rate = input_rates[index][1][0]
    prev_close_price = init_open_price * (1 / (1 + init_open_rate))
    for t in input_rates[index - 1 :: -1]:
        date, (open_rate, close_rate) = t

        prev_open_price = prev_close_price * (1 / (1 + close_rate))
        output_prices.insert(0, (date, (prev_open_price, prev_close_price)))

        prev_close_price = prev_open_price * (1 / (1 + open_rate))

    merged_prices = output_prices[:index] + ref_prices

    ref = [0] * 2 * index
    out = []
    mer = []
    for t in ref_prices:
        ref += [t[1][0], t[1][1]]
    for o in output_prices:
        out += [o[1][0], o[1][1]]
    for m in merged_prices:
        mer += [m[1][0], m[1][1]]

    plt.plot(ref)
    plt.plot(out)
    plt.plot(mer)
    plt.show()

    with open(f"charts/{output}-SIM.csv", "w") as fd:
        merged_prices_str = [
            f"{i[0]},{i[1][0]},{i[1][1]}\n" for i in merged_prices
        ]
        fd.writelines(merged_prices_str)


if __name__ == "__main__":
    matplotlib.use("TkAgg")
    main()
