#include "full.h"
#include "sim.h"
#include "data.h"
#include "env.h"
#include <iostream>
#include <fstream>
#include <chrono>
#include <cmath>

History full_backtest(
    const Config& config,
    const std::vector<StockRow>& chart,
    const std::unordered_map<std::string, double>& urates,
    const std::unordered_map<std::string, double>& rsis,
    const std::unordered_map<std::string, double>& volatilities,
    std::ostream* log_stream,
    const std::vector<StockRow>& base_chart
) {
    State s = State::init(SEED, MAX_CYCLES - 1);
    s.complete();

    double initial_base_price = base_chart.empty() ? 0 : base_chart[0].close_price;
    std::unordered_map<std::string, double> base_price;
    for (const auto& row : base_chart) {
        base_price[row.date] = row.close_price;
    }

    History history;
    double prev_base_price = 0;
    
    for (const auto& c : chart) {
        try {
            s = oneday(c, s, config, rsis, volatilities, urates);
        } catch (const SeedExhausted&) {
            s = State::from(s, c);
            s.complete();
        }

        if (initial_base_price > 0) {
            auto bp_it = base_price.find(s.date);
            if (bp_it != base_price.end()) {
                s.base_ror = (bp_it->second / initial_base_price) - 1;
                prev_base_price = bp_it->second;
            } else {
                s.base_ror = (prev_base_price / initial_base_price) - 1;
            }
        }

        history.push_back(s);

        if (log_stream) {
            auto rsi_it = rsis.find(c.date);
            auto urate_it = urates.find(c.date);
            auto vol_it = volatilities.find(c.date);
            
            if (rsi_it != rsis.end() && urate_it != urates.end() && vol_it != volatilities.end()) {
                *log_stream << s.to_string() << " ||| "
                           << "rsi=" << static_cast<int>(rsi_it->second) 
                           << ", urate=" << static_cast<int>(urate_it->second * 100) << "%, "
                           << "vol=" << static_cast<int>(vol_it->second) << std::endl;
            }
            
            if (s.boxx_eval < 0) {
                *log_stream << "[" << s.date << "] boxx exhausted (" << s.boxx_eval << ")" << std::endl;
            }
        }
    }

    return history;
}

std::tuple<History, double> full(
    const std::string& ticker,
    const Config& config,
    const std::string& start,
    const std::string& end,
    bool test_mode
) {
    auto ticker_it = TICKERS.find(ticker);
    if (ticker_it == TICKERS.end()) {
        throw std::runtime_error("Ticker not found: " + ticker);
    }
    
    std::string base_ticker = ticker_it->second;

    std::ostream* log_stream = nullptr;
    std::ofstream log_file;
    
    if (DEBUG) {
        // Create logs/full directory if needed
        system("mkdir -p logs/full");
        log_file.open("logs/full/" + ticker + ":" + start + "-" + end + ".log");
        log_stream = &log_file;
    } else if (VERBOSE) {
        log_stream = &std::cout;
    }

    auto full_chart = read_chart(ticker, "", "", test_mode);
    auto chart = read_chart(ticker, start, end, test_mode);
    auto base_chart = read_base_chart(base_ticker, start, end);

    auto URATE = compute_urates(full_chart, 50, config.term);
    auto RSI = compute_rsi(full_chart, 5);
    auto VOLATILITY = compute_volatility(full_chart, 5);

    auto history = full_backtest(config, chart, URATE, RSI, VOLATILITY, log_stream, base_chart);

    // Calculate average interest rate
    std::tm start_tm = {}, end_tm = {};
    std::istringstream start_ss(history.back().date);
    std::istringstream end_ss(history[0].date);
    
    start_ss >> std::get_time(&start_tm, "%Y-%m-%d");
    end_ss >> std::get_time(&end_tm, "%Y-%m-%d");
    
    auto start_time = std::mktime(&start_tm);
    auto end_time = std::mktime(&end_tm);
    
    int n_days = static_cast<int>((start_time - end_time) / (24 * 60 * 60));
    double avg_ir = std::pow(1 + history.back().ror, 365.0 / n_days) - 1;

    // Calculate base returns
    StockRow base_end, base_start;
    bool found_end = false, found_start = false;
    
    for (const auto& c : base_chart) {
        if (c.date == history.back().date) {
            base_end = c;
            found_end = true;
        }
        if (c.date == history[0].date) {
            base_start = c;
            found_start = true;
        }
    }
    
    double base_ror = 0, base_avg_ir = 0;
    if (found_end && found_start) {
        base_ror = (base_end.close_price / base_start.close_price) - 1;
        base_avg_ir = std::pow(1 + base_ror, 365.0 / n_days) - 1;
    }

    // Calculate statistics
    int n_exhausted = 0, n_failed = 0, n_sold = 0;
    for (const auto& s : history) {
        if (s.status == Status::Exhausted && s.cycle != 0) n_exhausted++;
        else if (s.status == Status::Exhausted && s.cycle == 0) n_failed++;
        else if (s.status == Status::Sold) n_sold++;
    }
    
    int n_tot = n_exhausted + n_failed + n_sold;
    double exhaust_rate = n_tot ? static_cast<double>(n_exhausted) / n_tot : 0;
    double fail_rate = n_tot ? static_cast<double>(n_failed) / n_tot : 0;

    if (test_mode) {
        std::cout << ticker << ": " << config.to_string() << " | " 
                  << std::fixed << std::setprecision(2) << avg_ir << std::endl;
    } else {
        std::cout << "[" << ticker << " (" << base_ticker << ")] " 
                  << history[0].date << " ~ " << history.back().date << std::endl;
        std::cout << "\tFinal RoR: " << std::fixed << std::setprecision(1) 
                  << (history.back().ror * 100) << "% (" << (avg_ir * 100) << "%)" << std::endl;
        std::cout << "\tBase RoR: " << (base_ror * 100) << "% (" << (base_avg_ir * 100) << "%)" << std::endl;
        std::cout << "\tExhaust Rate: " << (exhaust_rate * 100) << "%, Fail Rate: " 
                  << (fail_rate * 100) << "%" << std::endl;

        if (BOXX) {
            double boxx_ror = (history.back().boxx_eval - history.back().boxx_seed) / history.back().principal;
            std::cout << "\tBOXX Profit: " << (boxx_ror * 100) << "%" << std::endl;
        }
    }

    return std::make_tuple(history, avg_ir);
}