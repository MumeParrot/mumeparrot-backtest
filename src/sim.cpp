#include "sim.h"
#include <stdexcept>
#include <cmath>

State oneday(
    const StockRow& c,
    const State& s,
    const Config& config,
    const std::unordered_map<std::string, double>& RSI,
    const std::unordered_map<std::string, double>& VOLATILITY,
    const std::unordered_map<std::string, double>& URATE
) {
    double margin = config.margin;
    
    auto rsi_it = RSI.find(c.date);
    auto vol_it = VOLATILITY.find(c.date);
    auto urate_it = URATE.find(c.date);
    
    if (rsi_it == RSI.end() || vol_it == VOLATILITY.end() || urate_it == URATE.end()) {
        throw std::runtime_error("Missing data for date: " + c.date);
    }
    
    double rsi = rsi_it->second;
    double vol = vol_it->second;
    double urate = urate_it->second;

    double daily_seed = s.seed / config.term;
    State new_s = State::from(s, c);

    if (s.stock_qty > 0 && c.close_price > s.avg_price * (1 + margin)) {
        new_s.sell(static_cast<int>(s.stock_qty), c.close_price, true);
    } else {
        double dqtyD = daily_seed / c.close_price;
        double rate = 1.0;

        if (dqtyD < 1) {
            throw SeedExhausted();
        }

        if (rsi > config.bullish_rsi) {
            rate = 0;
        }

        if (urate < config.burst_urate && vol < 0 && std::abs(vol) > config.burst_vol) {
            rate *= (1 + config.burst_scale * (std::abs(vol) - config.burst_vol) / config.burst_vol);
        }

        int dqty = static_cast<int>(dqtyD * rate);
        
        if (s.remaining_seed < c.close_price) {
            // assert s.status != Status::Sold

            if (new_s.cycle_left()) {
                double sell_rate = config.sell_base + (config.sell_limit - config.sell_base) * (1 - urate);
                int sell_qty = static_cast<int>(s.stock_qty * sell_rate);
                new_s.sell(sell_qty, c.close_price);
            } else {
                new_s.sell(static_cast<int>(s.stock_qty), c.close_price);
            }
        } else if (s.remaining_seed >= dqty * c.close_price) {
            new_s.buy(dqty, c.close_price);
        } else {
            dqty = static_cast<int>(s.remaining_seed / c.close_price);
            new_s.buy(dqty, c.close_price);
        }
    }

    new_s.complete();
    return new_s;
}