from typing import Tuple
from dataclasses import dataclass, asdict


@dataclass
class Bounds:
    term: Tuple[int] = (40, 40)
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
    term: int = 1
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
    term: int = 40
    margin: float = 0.1  # [0.05:0.15:0.01] : 11
    bullish_rsi: int = 80  # [40:100:5] : 13
    bearish_rsi: int = 0  # [0:40:5] : 9
    min_bearish_rate: float = 1.0
    bullish_u50: float = 0.5
    burst_scale: float = 0.0
    burst_vol: int = 30
    sahm_threshold: float = 1.0

    def __hash__(self):
        h = 0
        for k, v in asdict(self).items():
            h = hash((h, k, v))

        return h

    def __str__(self):
        l = []
        for k, v in asdict(self).items():
            vs = f"{v:.2f}" if isinstance(v, float) else f"{v}"
            l.append(f"{k}: {vs}")

        return ", ".join(l)


best_configs = {
    "UPRO": Config(
        margin=0.06,
        bullish_rsi=85,
        bullish_u50=0.5,
        burst_scale=2.5,
        burst_vol=25,
    ),
    "SPXL": Config(
        margin=0.06,
        bullish_rsi=85,
        bullish_u50=0.5,
        burst_scale=2.5,
        burst_vol=25,
    ),
    "CURE": Config(
        margin=0.05,
        bullish_rsi=85,
        bullish_u50=0.4,
        burst_scale=1.5,
        burst_vol=25,
    ),
    "DFEN": Config(
        margin=0.06,
        bullish_rsi=85,
        bullish_u50=0.5,
        burst_scale=1.0,
        burst_vol=45,
    ),
    "FNGA": Config(
        margin=0.07,
        bullish_rsi=90,
        bullish_u50=0.4,
        burst_scale=2.0,
        burst_vol=25,
    ),
    "FAS": Config(
        margin=0.07,
        bullish_rsi=90,
        bullish_u50=0.5,
        burst_scale=2.5,
        burst_vol=45,
    ),
    "HIBL": Config(
        margin=0.05,
        bullish_rsi=65,
        bullish_u50=0.5,
        burst_scale=2.0,
        burst_vol=25,
    ),
    "LABU": Config(
        margin=0.10,
        bullish_rsi=80,
        bullish_u50=0.3,
        burst_scale=2.0,
        burst_vol=40,
    ),
    "MIDU": Config(
        margin=0.05,
        bullish_rsi=90,
        bullish_u50=0.5,
        burst_scale=1.0,
        burst_vol=25,
    ),
    "NAIL": Config(
        margin=0.08,
        bullish_rsi=85,
        bullish_u50=0.6,
        burst_scale=2.5,
        burst_vol=25,
    ),
    "PILL": Config(
        margin=0.05,
        bullish_rsi=95,
        bullish_u50=0.3,
        burst_scale=2.5,
        burst_vol=30,
    ),
    "RETL": Config(
        margin=0.05,
        bullish_rsi=70,
        bullish_u50=0.6,
        burst_scale=2.5,
        burst_vol=30,
    ),
    "SOXL": Config(
        margin=0.08,
        bullish_rsi=85,
        bullish_u50=0.7,
        burst_scale=1.0,
        burst_vol=25,
    ),
    "TECL": Config(
        margin=0.05,
        bullish_rsi=90,
        bullish_u50=0.6,
        burst_scale=0.5,
        burst_vol=25,
    ),
    "TNA": Config(
        margin=0.06,
        bullish_rsi=75,
        bullish_u50=0.4,
        burst_scale=2.0,
        burst_vol=25,
    ),
    "WANT": Config(
        margin=0.06,
        bullish_rsi=65,
        bullish_u50=0.4,
        burst_scale=2.5,
        burst_vol=25,
    ),
    "WEBL": Config(
        margin=0.06,
        bullish_rsi=90,
        bullish_u50=0.7,
        burst_scale=2.5,
        burst_vol=35,
    ),
    "TQQQ": Config(
        margin=0.06,
        bullish_rsi=95,
        bullish_u50=0.4,
        burst_scale=1.0,
        burst_vol=25,
    ),
}


def print_config(config: Config, ticker=""):
    d = asdict(config)
    s = f"Config("
    for k, v in d.items():
        s += f"{k}: {str(v)}, "
    s = (f"{ticker} " if ticker else "") + s[:-2] + ")"

    print(s)
