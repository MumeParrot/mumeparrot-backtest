from typing import Tuple
from dataclasses import dataclass, asdict

from src.utils import TICKERS


@dataclass
class Bounds:
    margin: Tuple[float] = (0.05, 0.15)
    bullish_rsi: Tuple[int] = (60, 100)
    bearish_rsi: Tuple[int] = (0, 40)
    min_bearish_rate: Tuple[float] = (1.0, 1.0)
    bullish_u50: Tuple[float] = (0.3, 0.8)
    burst_scale: Tuple[float] = (0.0, 3.0)
    burst_vol: Tuple[int] = (25, 50)
    sahm_threshold: Tuple[float] = (1.0, 1.0)


@dataclass
class Precisions:
    margin: float = 0.01
    bullish_rsi: int = 5
    bearish_rsi: int = 5
    min_bearish_rate: float = 0.1
    bullish_u50: float = 0.1
    burst_scale: float = 0.5
    burst_vol: int = 5
    sahm_threshold: float = 0.5


@dataclass
class Config:
    margin: float = 0.1  # [0.05:0.15:0.01] : 11
    bullish_rsi: int = 80  # [40:100:5] : 13
    bearish_rsi: int = 0  # [0:40:5] : 9
    min_bearish_rate: float = 1.0
    bullish_u50: float = 0.5
    burst_scale: float = 0.0
    burst_vol: int = 30
    sahm_threshold: float = 1.0

    def __str__(self):
        l = []
        for k, v in asdict(self).items():
            vs = f"{v:.2f}" if isinstance(v, float) else f"{v}"
            l.append(f"{k}: {vs}")

        return ", ".join(l)


best_configs = {ticker: Config() for ticker, _ in TICKERS.items()}

# best_configs["SOXL"] = Config(margin=0.1, burst_scale=1.1)
# best_configs["UPRO"] = Config(
#     margin=0.06, burst_scale=1.2, min_bearish_rate=0.2
# )
# best_configs["SPXL"] = Config(
#     margin=0.06, burst_scale=1.2, min_bearish_rate=0.2
# )
# best_configs["TQQQ"] = Config(
#     margin=0.09, burst_scale=1.3, min_bearish_rate=0.2
# )
# best_configs["TECL"] = Config(
#     margin=0.08, burst_scale=1.6, min_bearish_rate=0.2
# )
# best_configs["NAIL"] = Config(margin=0.09, min_bearish_rate=0.6)
# best_configs["RETL"] = Config(margin=0.06, min_bearish_rate=0.4)
# best_configs["WEBL"] = Config(
#     margin=0.09, burst_scale=1.2, min_bearish_rate=0.4
# )


def print_config(config: Config, ticker=""):
    d = asdict(config)
    s = f"Config("
    for k, v in d.items():
        s += f"{k}: {str(v)}, "
    s = (f"{ticker} " if ticker else "") + s[:-2] + ")"

    print(s)
