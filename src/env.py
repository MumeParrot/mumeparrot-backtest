from typing import Dict

from .configs import Config

import os
import json

START: str = os.environ.get("START", "")
END: str = os.environ.get("END", "")
MARKET_DAYS_PER_YEAR = 260

TICKER_FILE = os.environ.get("TICKER_FILE", "tickers.json")
CONFIGS_FILE = os.environ.get("CONFIGS", "configs.json")

with open(TICKER_FILE, "r") as fd:
    TICKERS: Dict[str, str] = json.load(fd)

with open("configs.json", "r") as fd:
    configs_json = json.load(fd)

    BEST_CONFIGS = {k: Config._from(configs_json[k]) for k in TICKERS.keys()}

DEBUG: bool = bool(int(os.environ.get("DEBUG", 0)))
VERBOSE: bool = bool(int(os.environ.get("VERBOSE", 0)))

CYCLE_DAYS: int = int(os.environ.get("CYCLE_DAYS", 60))
SEED: int = int(os.environ.get("SEED", 1000000))
MAX_CYCLES: int = int(os.environ.get("MAX_CYCLES", 2))

FAIL_PANELTY: int = int(os.environ.get("FAIL_PENALTY", 2))
FAIL_LIMIT: float = float(os.environ.get("FAIL_LIMIT", 0.1))

COMMISSION_RATE: float = float(os.environ.get("COMMISSION_RATE", 0))
assert COMMISSION_RATE < 0.01, "commission rate cannot exceed 0.01"

GRAPH: bool = bool(int(os.environ.get("GRAPH", 0)))
BOXX: bool = bool(int(os.environ.get("BOXX", 0)))

# BOXX_UNIT has two purposes
# 1. it determines the minimum threshold of remaining balance
# 2. it determines the unit amount of buying power for BOXX
# i.e., 0.125 (= 1/8) means one week of seed
BOXX_UNIT: float = float(os.environ.get("BOXX_UNIT", 0.125))
BOXX_IR: float = float(os.environ.get("BOXX_IR", 0.045))
