import os
import re

from typing import Tuple


def analyze_result(directory: str, ticker: str):
    files = [
        f"{directory}/{f}"
        for f in os.listdir(directory)
        if f.startswith(ticker)
    ]

    from .configs import Config

    def parse_line(line: str) -> Tuple[Config, float]:
        line = line.replace(f"{ticker}: ", "")

        conf, res = line.split(" | ")
        m = re.match(r"(.+?) \((.+)%?, (.+)%?\)\n", res)
        score, ror_per_year, fail_rate = m.groups()

        score = float(score)

        conf = [c.split(": ") for c in conf.split(", ")]
        conf = {k: float(v) for k, v in conf}

        config = Config(**conf)

        return ((config, (ror_per_year, fail_rate)), score)

    final_results = {}
    for f in files:
        results = {}

        with open(f, "r") as fd:
            lines = fd.readlines()

        for l in lines:
            try:
                config_and_result, score = parse_line(l)
                results[config_and_result] = score
            except Exception as e:
                pass

        sorted_results = sorted(results.items(), key=lambda item: item[1])

        for s in sorted_results[-2:]:
            final_results[s[0]] = s[1]

    final_results = sorted(final_results.items(), key=lambda item: -item[1])

    for cr, score in final_results:
        print(f"{score} {cr[1]}: {cr[0]}")
