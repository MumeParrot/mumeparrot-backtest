from typing import Dict

from .configs import Config

import os
import json

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
FAIL_LIMIT: float = float(os.environ.get("FAIL_LIMIT", 0.05))
