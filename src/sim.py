import math

from typing import List, Dict

from .const import StockRow, State
from .utils import read_chart, read_base_chart, read_sahm, plot, moving_average

TERM = 40
MARGIN = 0.1


def run(ticker: str, principal: float, start: str, end: str):
    chart = read_chart(ticker, start, end)
    base_chart = read_base_chart(ticker, start, end)
    sahm = read_sahm()

    mume_avg_history1 = mume_avg(
        chart,
        principal,
        sahm,
        adjust_buy=True,
        adjust_good=True,
        adjust_sell=True,
        adjust_margin=True,
        consider_sahm=False,
    )
    mume_avg_history2 = mume_avg(
        chart,
        principal,
        sahm,
        adjust_buy=True,
        adjust_good=True,
        adjust_sell=True,
        adjust_margin=True,
        consider_sahm=True,
    )

    buy_history = just_buy(base_chart, principal)

    plot(
        ticker,
        {
            "just-buy": buy_history,
            "mumeparrot": mume_avg_history1,
            "mumeparrot-sahm": mume_avg_history2,
        },
    )


def just_buy(chart: List[StockRow], principal: float):
    history = []

    seed = principal
    ror = 1

    stock_qty = principal // chart[0].price
    stock_eval = 0

    invested_seed = stock_qty * chart[0].price
    stock_avg = 0
    remaining_seed = seed - invested_seed

    for date, price, close_price in chart:
        stock_avg = invested_seed / stock_qty if stock_qty != 0 else 0
        stock_eval = stock_qty * close_price
        ror = (remaining_seed + stock_eval) / principal

        state = State(
            date,
            principal,
            seed,
            ror,
            close_price,
            stock_qty,
            stock_qty * price,
            invested_seed,
            stock_avg,
            remaining_seed,
        )

        history.append(state)

    return history


def v1(chart: List[StockRow], principal: float):
    history = []

    seed = principal
    ror = 1

    stock_qty = 0
    stock_eval = 0

    invested_seed = 0
    stock_avg = 0
    remaining_seed = seed

    for date, price, close_price in chart:

        dqty = seed // (TERM * price)
        if dqty < 1:
            raise RuntimeError(f"dqty for '{date}' is '{dqty}'")

        dqty_high, dcost_high = 0, 0
        dqty_low, dcost_low = 0, 0
        if stock_avg != 0 and price > stock_avg:
            if close_price > price:
                if (stock_avg * (1 + MARGIN)) > close_price:
                    dqty_high = dqty // 2
                    dcost_high = dqty_high * close_price

            else:
                dqty_low = dqty // 2
                dcost_low = dqty_low * close_price

                if (stock_avg * (1 + MARGIN)) > close_price:
                    dqty_high = dqty - dqty_low
                    dcost_high = dqty_high * close_price

        else:
            dqty_high = dqty // 2
            dcost_high = dqty_high * price

            dqty_low = dqty - dqty_high
            dcost_low = dqty_low * price

        # Actual orders
        sold_now = stock_qty != 0 and price > stock_avg * (1 + MARGIN)
        sold_later = stock_qty != 0 and close_price > stock_avg * (1 + MARGIN)
        all_seed_used = remaining_seed < dcost_high + dcost_low

        if sold_now or sold_later or all_seed_used:
            sell_price = (
                price
                if sold_now
                else (stock_avg * (1 + MARGIN)) if sold_later else price
            )
            sell_qty = stock_qty
            profit = sell_qty * (sell_price - stock_avg)
            stock_qty -= sell_qty
            seed += profit
            invested_seed -= sell_qty * stock_avg
            remaining_seed += sell_qty * sell_price

        else:  # remaining_seed > dcost_high + dcost_low
            stock_qty += dqty_high + dqty_low
            invested_seed += dcost_high + dcost_low
            remaining_seed -= dcost_high + dcost_low

        stock_avg = invested_seed / stock_qty if stock_qty != 0 else 0
        stock_eval = stock_qty * close_price
        ror = (remaining_seed + stock_eval) / principal

        state = State(
            date,
            principal,
            seed,
            ror,
            close_price,
            stock_qty,
            stock_eval,
            invested_seed,
            stock_avg,
            remaining_seed,
        )

        history.append(state)

    return history


def mume_avg(
    chart: List[StockRow],
    principal: float,
    sahm: Dict[str, float],
    adjust_buy=False,
    adjust_margin=False,
    adjust_good=False,
    adjust_sell=False,
    consider_sahm=False,
) -> List[State]:
    avg200_history = moving_average(chart, 200)
    avg100_history = moving_average(chart, 100)
    avg5_history = moving_average(chart, 5)
    avg10_history = moving_average(chart, 10)
    avg3_history = moving_average(chart, 3)
    history = []

    seed = principal
    ror = 1

    stock_qty = 0
    stock_eval = 0

    invested_seed = 0
    stock_avg = 0
    remaining_seed = seed

    onoff = False
    good = False
    happy = False

    prev_5_prices = []

    cnt_make_profit = 0
    cnt_all_used = 0

    total_days = 0
    for date, price, close_price in chart:
        term = TERM
        margin = MARGIN

        max_margin = MARGIN
        if adjust_margin:
            max_margin = MARGIN + (remaining_seed / seed) * MARGIN / 2

        dqty = seed // (term * price)
        if dqty < 1:
            raise RuntimeError(f"dqty for '{date}' is '{dqty}'")

        prev_5_prices.append(price)
        if len(prev_5_prices) > 5:
            prev_5_prices.pop(0)

        if (
            prev_5_prices[0] < avg100_history[date]
            and price > avg100_history[date]
        ):
            happy = True
        else:
            happy = False

        if adjust_buy and happy:
            dqty *= 2

        dqty_high, dcost_high = 0, 0
        dqty_low, dcost_low = 0, 0

        if not onoff:
            if consider_sahm:
                if sahm[date] > 0.5:
                    if (
                        price > avg100_history[date]
                        and price > avg5_history[date]
                    ):
                        onoff = True
                else:
                    if price > avg5_history[date]:
                        onoff = True

            elif price > avg5_history[date]:
                onoff = True

        if adjust_good:
            good = price > avg100_history[date] or price > avg3_history[date]
        else:
            good = True

        if stock_avg != 0 and price > stock_avg:
            if close_price > price:
                if (stock_avg * (1 + margin)) > close_price:
                    dqty_high = dqty // 2
                    dcost_high = dqty_high * close_price

            else:
                dqty_low = dqty // 2
                dcost_low = dqty_low * close_price

                if (stock_avg * (1 + margin)) > close_price:
                    dqty_high = dqty - dqty_low
                    dcost_high = dqty_high * close_price

        else:
            dqty_high = dqty // 2
            dcost_high = dqty_high * price

            dqty_low = dqty - dqty_high
            dcost_low = dqty_low * price

        # Actual orders
        sell_all = sell_half = sell_all_later = sell_half_later = False
        if stock_qty > 0:
            if price > stock_avg * (1 + max_margin):
                sell_all = True
            elif price > stock_avg * (1 + margin):
                sell_half = True

                if close_price > stock_avg * (1 + max_margin):
                    sell_all_later = True

            elif close_price > stock_avg * (1 + max_margin):
                sell_all_later = True
            elif close_price > stock_avg * (1 + margin):
                sell_half_later = True

        make_profit = sell_all or sell_half or sell_all_later or sell_half_later
        all_seed_used = remaining_seed < dcost_high + dcost_low

        if make_profit or all_seed_used:
            sell_price = price
            if sell_all_later:
                sell_price = stock_avg * (1 + (margin + max_margin) / 2)
            elif sell_half_later:
                sell_price = stock_avg * (1 + margin)

            if all_seed_used:
                if adjust_sell:
                    sell_qty = (
                        stock_qty
                        if (price < avg200_history[date])
                        else (stock_qty // 4)
                    )
                else:
                    sell_qty = stock_qty
            else:
                sell_qty = (
                    stock_qty
                    if (sell_all or sell_all_later)
                    else stock_qty // 2
                )

            profit = sell_qty * (sell_price - stock_avg)
            stock_qty -= sell_qty
            seed += profit
            invested_seed -= sell_qty * stock_avg
            remaining_seed += sell_qty * sell_price

            if stock_qty == 0:
                onoff = False

            if make_profit:
                cnt_make_profit += 1
            if all_seed_used:
                # print(
                #     f"[{date}] {avg3_history[date]:.1f}\t{avg5_history[date]:.1f}\t{avg100_history[date]:.1f}\t{avg200_history[date]:.1f}\t{price:.1f}"
                # )
                cnt_all_used += 1

        elif onoff and good:
            stock_qty += dqty_high + dqty_low
            invested_seed += dcost_high + dcost_low
            remaining_seed -= dcost_high + dcost_low

        stock_avg = invested_seed / stock_qty if stock_qty != 0 else 0
        stock_eval = stock_qty * close_price
        ror = (remaining_seed + stock_eval) / principal

        state = State(
            date,
            principal,
            seed,
            ror,
            close_price,
            stock_qty,
            stock_eval,
            invested_seed,
            stock_avg,
            remaining_seed,
        )

        history.append(state)
        total_days += 1

    print(f"total_days: {total_days}")
    print(f"cnt_make_profit: {cnt_make_profit}")
    print(f"cnt_all_used: {cnt_all_used}")

    return history
