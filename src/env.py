import os
import json

TICKER_FILE = os.environ.get("TICKER_FILE", "tickers.json")

with open(TICKER_FILE, "r") as fd:
    TICKERS = json.loads(fd.read())

CYCLE_DAYS: int = int(os.environ.get("CYCLE_DAYS", 40))
SEED: int = int(os.environ.get("SEED", 1000000))
MAX_CYCLES: int = int(os.environ.get("MAX_CYCLES", 2))

FAIL_PANELTY: int = int(os.environ.get("FAIL_PENALTY", 2))
FAIL_LIMIT: float = float(os.environ.get("FAIL_LIMIT", 0.05))
