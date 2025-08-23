import json

from typing import Tuple, Dict, Union
from dataclasses import dataclass, asdict


@dataclass
class Description:
    term: str = "number of days to split the seed and buy the stock"
    margin: str = "margin to sell the stock"
    bullish_rsi: str = "rsi threshold to buy the stock"
    bullish_u50: str = (
        "rate of market days under 50 moving average to determine burst buy and "
    )
    burst_scale: str = "scale of burst buy when the market fluctuates"
    burst_vol: str = "volatility threshold to determine burst buy"
    sell_base: str = "base sell rate when all seed is exhausted"
    sell_limit: str = "sell limit when all seed is exhausted"
    sahm_threshold: str = "sahm threshold to exclude when sliding window test"

    split: str = "number to split the seed"
    buy_rsi: str = "rsi threshold to buy the stock"
    sell_rsi: str = "rsi threshold to sell the stock"


@dataclass
class Bounds:
    term: Tuple[int] = (40, 40)
    margin: Tuple[float] = (0.05, 0.15)
    bullish_rsi: Tuple[int] = (60, 100)
    bullish_u50: Tuple[float] = (0.3, 0.8)
    burst_scale: Tuple[float] = (0.0, 3.0)
    burst_vol: Tuple[int] = (25, 50)
    sell_base: Tuple[float] = (0, 0.5)
    sell_limit: Tuple[float] = (0.5, 1.0)
    sahm_threshold: Tuple[float] = (1.0, 1.0)
    split: Tuple[int] = (10, 20)
    buy_rsi: Tuple[int] = (20, 50)
    sell_rsi: Tuple[int] = (70, 100)


@dataclass
class Precisions:
    term: int = 1
    margin: float = 0.01
    bullish_rsi: int = 5
    bullish_u50: float = 0.1
    burst_scale: float = 0.5
    burst_vol: int = 5
    sell_base: float = 0.1
    sell_limit: float = 0.1
    sahm_threshold: float = 0.5
    split: int = 5
    buy_rsi: int = 5
    sell_rsi: int = 5


@dataclass
class Config:
    @classmethod
    def _from(cls, map: Dict[str, Union[float, int]]) -> "Config":
        inst = cls()

        for field, value in map.items():
            if hasattr(inst, field):
                setattr(inst, field, value)

        return inst

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


@dataclass
class V1Config(Config):
    term: int = 40
    margin: float = 0.1  # [0.05:0.15:0.01] : 11
    bullish_rsi: int = 80  # [40:100:5] : 13
    bullish_u50: float = 0.5
    burst_scale: float = 0.0
    burst_vol: int = 30
    sell_base: float = 0
    sell_limit: float = 1
    sahm_threshold: float = 1.0


@dataclass
class V2Config(Config):
    split: int = 10
    buy_rsi: int = 30
    sell_rsi: int = 80
