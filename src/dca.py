from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional

from .const import StockRow
from .env import COMMISSION_RATE


@dataclass
class DcaDailyState:
    date: str
    price: float
    close_price: float
    rsi: Optional[float]
    cash: float
    shares: float
    invested: float
    value: float
    ror: float
    commission_paid: float
    bought: bool = False


def compute_dca_rsi(full_chart: List[StockRow]) -> Dict[str, float]:
    """
    Computes Welles Wilder RSI(14, 50) exactly matching the logic of price_history.dart:
    - Initial Up/Down is the average over the first 14 differences (or len(diffs) if fewer than 14).
    - Subsequent values are smoothed over the remaining diffs in the last 50 days window.
    """
    prices = [c.close_price for c in full_chart]
    dates = [c.date for c in full_chart]
    
    term = 14
    range_val = 50
    rsi_dict = {}
    
    # Pre-calculate differences
    diffs = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
    
    for i in range(len(full_chart)):
        date = dates[i]
        if i < term:
            rsi_dict[date] = 50.0
            continue
            
        # Last 50 changes leading to today
        start_diff_idx = max(i - range_val, 0)
        d_slice = diffs[start_diff_idx:i]
        
        if len(d_slice) <= term:
            t = len(d_slice)
            initial_slice = d_slice
        else:
            t = term
            initial_slice = d_slice[:term]
            
        up = sum(d for d in initial_slice if d > 0) / term
        down = sum(-d for d in initial_slice if d < 0) / term
        
        for d in d_slice[t:]:
            up = (up * 13 + (d if d > 0 else 0.0)) / 14
            down = (down * 13 + (-d if d < 0 else 0.0)) / 14
            
        if up + down == 0:
            rsi_dict[date] = 50.0
        else:
            rsi_dict[date] = 100.0 * (up / (up + down))
            
    return rsi_dict


def run_dca_backtest(
    chart: List[StockRow],
    rsi_dict: Dict[str, float],
    rsi_threshold: float,
    buy_splits: int,
    monthly_wage: float,
    inflation_rate: float,
) -> Tuple[List[DcaDailyState], List[DcaDailyState]]:
    """
    Runs the DCA backtest simulation for both the RSI Strategy and the Baseline:
    
    - Strategy: Adds monthly wage (inflation-adjusted annually).
                Buys stock only when RSI < rsi_threshold.
                Uses cash / buy_splits to buy at a time.
    
    - Baseline: Adds monthly wage (inflation-adjusted annually).
                Buys stock immediately on the day the wage is added.
    """
    strategy_history: List[DcaDailyState] = []
    baseline_history: List[DcaDailyState] = []
    
    # Strategy state
    strat_cash = 0.0
    strat_shares = 0.0
    strat_invested = 0.0
    strat_comm = 0.0
    
    # Baseline state
    base_cash = 0.0
    base_shares = 0.0
    base_invested = 0.0
    base_comm = 0.0
    
    prev_month = None
    prev_year = None
    current_wage = monthly_wage
    strat_buy_amount = 0.0
    
    for c in chart:
        year, month = c.date.split("-")[0:2]
        
        # Determine if this is a new month
        is_new_month = False
        if prev_month is None:
            is_new_month = True
        elif month != prev_month:
            is_new_month = True
            
        # Annual inflation adjustment when the calendar year changes
        if prev_year is not None and year != prev_year:
            current_wage *= (1.0 + inflation_rate)
            
        # 1. Process wage addition
        if is_new_month:
            strat_invested += current_wage
            strat_cash += current_wage
            
            # Recalculate the fixed buy amount for this month using the new cash balance
            strat_buy_amount = strat_cash / max(1, buy_splits)
            
            base_invested += current_wage
            base_cash += current_wage
            
            # Baseline buys immediately on wage addition
            if base_cash > 0:
                comm = base_cash * COMMISSION_RATE
                qty = (base_cash - comm) / c.price
                base_shares += qty
                base_cash -= base_cash  # spent all
                base_comm += comm
        
        # 2. Strategy buys if RSI < rsi_threshold
        rsi_val = rsi_dict.get(c.date, 50.0)
        strat_bought = False
        if rsi_val < rsi_threshold and strat_cash > 0:
            buy_cash = min(strat_buy_amount, strat_cash)
            if buy_cash > 0:
                comm = buy_cash * COMMISSION_RATE
                qty = (buy_cash - comm) / c.price
                strat_shares += qty
                strat_cash -= buy_cash
                strat_comm += comm
                strat_bought = True
                
        # 3. Record daily states
        strat_val = strat_cash + strat_shares * c.close_price
        strat_ror = (strat_val / strat_invested - 1.0) if strat_invested > 0 else 0.0
        strategy_history.append(DcaDailyState(
            date=c.date,
            price=c.price,
            close_price=c.close_price,
            rsi=rsi_val,
            cash=strat_cash,
            shares=strat_shares,
            invested=strat_invested,
            value=strat_val,
            ror=strat_ror,
            commission_paid=strat_comm,
            bought=strat_bought
        ))
        
        base_val = base_cash + base_shares * c.close_price
        base_ror = (base_val / base_invested - 1.0) if base_invested > 0 else 0.0
        baseline_history.append(DcaDailyState(
            date=c.date,
            price=c.price,
            close_price=c.close_price,
            rsi=rsi_val,
            cash=base_cash,
            shares=base_shares,
            invested=base_invested,
            value=base_val,
            ror=base_ror,
            commission_paid=base_comm
        ))
        
        prev_month = month
        prev_year = year
        
    return strategy_history, baseline_history
