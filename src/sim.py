from typing import Dict

from .configs import Config
from .const import SeedExhausted, StockRow, State, Status


def oneday(
    c: StockRow,
    s: State,
    config: Config,
    CYCLE_DAYS: int,
    RSI: Dict[str, float],
    VOLATILITY: Dict[str, float],
    URATE: Dict[str, float],
) -> State:
    margin = config.margin
    rsi = RSI[c.date]
    vol = VOLATILITY[c.date]
    urate = URATE[c.date]

    daily_seed: float = s.seed / CYCLE_DAYS
    new_s = State.from_(s, c)

    if s.stock_qty > 0 and c.close_price > s.avg_price * (1 + margin):
        new_s.sell(qty=s.stock_qty, sell_price=c.close_price, sold=True)

    else:
        dqtyD = float(daily_seed / c.close_price)
        rate = float(1)

        if dqtyD < 1:
            raise SeedExhausted

        if rsi > config.bullish_rsi:
            rate = 0

        if (
            urate < config.bullish_u50
            and vol < 0
            and abs(vol) > config.burst_vol
        ):
            rate *= (
                1
                + config.burst_scale
                * (abs(vol) - config.burst_vol)
                / config.burst_vol
            )

        dqty = int(dqtyD * rate)
        if s.remaining_seed >= dqty * c.close_price:
            new_s.buy(qty=dqty, buy_price=c.close_price)

        elif s.remaining_seed >= c.close_price:
            dqty = int(s.remaining_seed / c.close_price)
            new_s.buy(qty=dqty, buy_price=c.close_price)

        else:
            assert s.status != Status.Sold

            if new_s.cycle_left():  # cycles left # TODO: consider RSI?
                sell_qty = int(max(s.stock_qty / 4, s.stock_qty * urate))
                new_s.sell(qty=sell_qty, sell_price=c.close_price)

            else:  # exhausted
                new_s.sell(qty=s.stock_qty, sell_price=c.close_price)

    new_s.complete()

    return new_s
