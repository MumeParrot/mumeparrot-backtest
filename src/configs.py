import json

from typing import Tuple, Dict
from dataclasses import dataclass, asdict


@dataclass
class Bounds:
    term: Tuple[int] = (40, 40)
    margin: Tuple[float] = (0.05, 0.15)
    bullish_rsi: Tuple[int] = (60, 100)
    bullish_u50: Tuple[float] = (0.3, 0.8)
    burst_scale: Tuple[float] = (0.0, 3.0)
    burst_vol: Tuple[int] = (25, 50)
    sell_base: Tuple[float] = (0, 0.5)
    sahm_threshold: Tuple[float] = (1.0, 1.0)


@dataclass
class Precisions:
    term: int = 1
    margin: float = 0.01
    bullish_rsi: int = 5
    bullish_u50: float = 0.1
    burst_scale: float = 0.5
    burst_vol: int = 5
    sell_base: float = 0.1
    sahm_threshold: float = 0.5


@dataclass
class Config:
    term: int = 40
    margin: float = 0.1  # [0.05:0.15:0.01] : 11
    bullish_rsi: int = 80  # [40:100:5] : 13
    bullish_u50: float = 0.5
    burst_scale: float = 0.0
    burst_vol: int = 30
    sell_base: float = 0
    sahm_threshold: float = 1.0

    @classmethod
    def _from(cls, map: Dict[str, Tuple[float, int]]) -> "Config":
        return Config(
            term=map.get("term", cls.term),
            margin=map.get("margin", cls.margin),
            bullish_rsi=map.get("bullish_rsi", cls.bullish_rsi),
            bullish_u50=map.get("bullish_u50", cls.bullish_u50),
            burst_scale=map.get("burst_scale", cls.burst_scale),
            burst_vol=map.get("burst_vol", cls.burst_vol),
            sell_base=map.get("sell_base", cls.sell_base),
            sahm_threshold=map.get("sahm_threshold", cls.sahm_threshold),
        )

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
