from dataclasses import dataclass, asdict

from src.utils import TICKERS


@dataclass
class Config:
    margin: float = 0.1
    min_bearish_rate: float = 1.0
    burst_rate: float = 0
    sahm_threshold: float = 1.0


best_configs = {ticker: Config() for ticker, _ in TICKERS.items()}

best_configs["SOXL"] = Config(margin=0.1, burst_rate=1.1)
best_configs["UPRO"] = Config(margin=0.06, burst_rate=1.2, min_bearish_rate=0.2)
best_configs["SPXL"] = Config(margin=0.06, burst_rate=1.2, min_bearish_rate=0.2)
best_configs["TQQQ"] = Config(margin=0.09, burst_rate=1.3, min_bearish_rate=0.2)
best_configs["TECL"] = Config(margin=0.08, burst_rate=1.6, min_bearish_rate=0.2)
best_configs["NAIL"] = Config(margin=0.09, min_bearish_rate=0.6)
best_configs["RETL"] = Config(margin=0.06, min_bearish_rate=0.4)
best_configs["WEBL"] = Config(margin=0.09, burst_rate=1.2, min_bearish_rate=0.4)


def print_config(config: Config, ticker=""):
    d = asdict(config)
    s = f"Config("
    for k, v in d.items():
        s += f"{k}: {str(v)}, "
    s = (f"{ticker} " if ticker else "") + s[:-2] + ")"

    print(s)
