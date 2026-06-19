#include "dca.h"
#include "env.h"
#include <algorithm>
#include <iostream>

std::unordered_map<std::string, double> compute_dca_rsi(const std::vector<StockRow>& full_chart) {
    std::unordered_map<std::string, double> rsi_dict;
    if (full_chart.empty()) return rsi_dict;

    int term = 14;
    int range_val = 50;

    std::vector<double> prices;
    prices.reserve(full_chart.size());
    for (const auto& row : full_chart) {
        prices.push_back(row.close_price);
    }

    std::vector<double> diffs;
    diffs.reserve(prices.size() - 1);
    for (size_t i = 0; i < prices.size() - 1; ++i) {
        diffs.push_back(prices[i + 1] - prices[i]);
    }

    for (size_t i = 0; i < full_chart.size(); ++i) {
        std::string date = full_chart[i].date;
        if (i < static_cast<size_t>(term)) {
            rsi_dict[date] = 50.0;
            continue;
        }

        int start_diff_idx = std::max(static_cast<int>(i) - range_val, 0);
        int d_len = static_cast<int>(i) - start_diff_idx;

        int t = (d_len <= term) ? d_len : term;

        double up_sum = 0.0;
        double down_sum = 0.0;
        for (int j = 0; j < t; ++j) {
            double d = diffs[start_diff_idx + j];
            if (d > 0) up_sum += d;
            else if (d < 0) down_sum -= d;
        }

        double up = up_sum / term;
        double down = down_sum / term;

        for (int j = t; j < d_len; ++j) {
            double d = diffs[start_diff_idx + j];
            up = (up * 13.0 + (d > 0 ? d : 0.0)) / 14.0;
            down = (down * 13.0 + (d < 0 ? -d : 0.0)) / 14.0;
        }

        if (up + down == 0) {
            rsi_dict[date] = 50.0;
        } else {
            rsi_dict[date] = 100.0 * (up / (up + down));
        }
    }

    return rsi_dict;
}

std::vector<State> run_dca_backtest(
    const std::vector<StockRow>& chart,
    const std::unordered_map<std::string, double>& rsi_dict,
    const Config& config
) {
    std::vector<State> history;
    if (chart.empty()) return history;

    // Strategy state
    double strat_cash = SEED;
    double strat_shares = 0.0;
    double strat_invested = SEED;
    double strat_comm = 0.0;

    // Baseline state
    double base_cash = SEED;
    double base_shares = 0.0;
    double base_invested = SEED;
    double base_comm = 0.0;

    double strat_buy_amount = SEED / std::max(1, config.buy_splits);
    int elapsed = 0;

    for (const auto& c : chart) {
        elapsed++;

        // 1. Baseline buys immediately on day 1
        if (elapsed == 1) {
            if (base_cash > 0) {
                double comm = base_cash * COMMISSION_RATE;
                double qty = (base_cash - comm) / c.price;
                base_shares = qty;
                base_cash = 0.0;
                base_comm = comm;
            }
        }

        // 2. Strategy buys if RSI < rsi_threshold
        double rsi_val = 50.0;
        auto rsi_it = rsi_dict.find(c.date);
        if (rsi_it != rsi_dict.end()) {
            rsi_val = rsi_it->second;
        }

        if (rsi_val < config.rsi_threshold && strat_cash > 0) {
            double current_portfolio_val = strat_cash + strat_shares * c.price;
            strat_buy_amount = current_portfolio_val / std::max(1, config.buy_splits);
            double buy_cash = std::min(strat_buy_amount, strat_cash);
            if (buy_cash > 0) {
                double comm = buy_cash * COMMISSION_RATE;
                double qty = (buy_cash - comm) / c.price;
                strat_shares += qty;
                strat_cash -= buy_cash;
                strat_comm += comm;
            }
        }

        // 3. Calculate daily returns (TWR is simple return as there are no external cash flows after day 1)
        double strat_val_daily = strat_cash + strat_shares * c.close_price;
        double strat_twr_daily = (strat_invested > 0) ? (strat_val_daily / strat_invested - 1.0) : 0.0;

        double base_val_daily = base_cash + base_shares * c.close_price;
        double base_twr_daily = (base_invested > 0) ? (base_val_daily / base_invested - 1.0) : 0.0;

        // 4. Record state
        State s;
        s.date = c.date;
        s.elapsed = elapsed;
        s.principal = strat_invested;
        s.price = c.price;
        s.close_price = c.close_price;
        s.max_cycle = 0;
        s.seed = strat_cash;
        s.invested_seed = strat_invested;
        s.remaining_seed = strat_cash;
        s.stock_qty = strat_shares;
        s.commission = strat_comm;
        s.status = Status::Buying;
        s.cycle = 0;
        s.balance = strat_cash;
        s.boxx_seed = 0.0;
        s.boxx_eval = 0.0;
        s.avg_price = (strat_shares > 0) ? (strat_invested / strat_shares) : 0.0;
        s.stock_eval = strat_cash + strat_shares * c.close_price;
        s.ror = strat_twr_daily;
        s.base_ror = base_twr_daily;

        history.push_back(s);
    }

    return history;
}
