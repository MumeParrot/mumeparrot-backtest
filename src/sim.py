from typing import Dict

from .configs import Config
from .const import SeedExhausted, StockRow, State, Status


def oneday(
    c: StockRow,
    s: State,
    config: Config,
    RSI: Dict[str, float],
    VOLATILITY: Dict[str, float],
    URATE: Dict[str, float],
) -> State:
    rsi = RSI[c.date]
    vol = VOLATILITY[c.date]
    urate = URATE[c.date]

    margin = config.margin
    seed_rate = s.remaining_seed / s.seed
    seed_rate = (
        (seed_rate - config.min_seed_rate) / (1 - config.min_seed_rate)
        if config.min_seed_rate < 1
        else 0
    )
    bullish_rsi = config.bullish_rsi + max(seed_rate, 0) * (
        100 - config.bullish_rsi
    )

    daily_seed: float = s.seed / config.term
    new_s = State.from_(s, c)

    if s.stock_qty > 0 and c.close_price > s.avg_price * (1 + margin):
        new_s.sell(qty=s.stock_qty, sell_price=c.close_price, sold=True)

    else:
        dqtyD = float(daily_seed / c.close_price)
        rate = float(1)

        if dqtyD < 1:
            raise SeedExhausted

        if rsi > bullish_rsi:
            rate = 0

        if (
            urate < config.burst_urate
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
        if s.remaining_seed < c.close_price:
            assert s.status != Status.Sold

            if new_s.cycle_left():  # cycles left # TODO: consider RSI?
                rate = config.sell_base + (
                    config.sell_limit - config.sell_base
                ) * (1 - urate)

                sell_qty = int(s.stock_qty * rate)
                new_s.sell(qty=sell_qty, sell_price=c.close_price)

            else:  # exhausted
                new_s.sell(qty=s.stock_qty, sell_price=c.close_price)

        elif s.remaining_seed >= dqty * c.close_price:
            new_s.buy(qty=dqty, buy_price=c.close_price)

        else:  # s.remaining_seed >= c.close_price
            dqty = int(s.remaining_seed / c.close_price)
            new_s.buy(qty=dqty, buy_price=c.close_price)

    new_s.complete()

    return new_s
