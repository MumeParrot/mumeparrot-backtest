from dataclasses import dataclass

@dataclass
class Config:
    margin: float
    margin_lose: float = 0
    rsi_threshold: int = 80
    burst_threshold: int = 40
    burst_rate: float = 1
    margin_window: float = 0
    stoploss_threshold: float = 0 # TODO
    sahm_threshold: float = 1

best_configs = {
    'SOXL': Config(margin=0.1),
    'SPXL': Config(margin=0.06),
    'TQQQ': Config(margin=0.09),
    'TECL': Config(margin=0.08),
    'NAIL': Config(margin=0.09),
    'RETL': Config(margin=0.06),
    'WEBL': Config(margin=0.09),
}
