#include "test.h"
#include "sim.h"
#include "data.h"
#include "env.h"
#include <iostream>
#include <fstream>
#include <algorithm>
#include <numeric>
#include <climits>

int NUM_SIMULATED = 0;
int NUM_RETIRED = 0;

std::unordered_map<std::string, std::tuple<double, Result>> compute_weighted_results(
    const std::unordered_map<int, std::vector<Result>>& results
) {
    std::unordered_map<std::string, Result> date_results;
    
    for (int c = 0; c < MAX_CYCLES - 1; c++) {
        auto it = results.find(c);
        if (it != results.end()) {
            for (const auto& r : it->second) {
                if (r.sold) {
                    date_results[r.start] = r;
                }
            }
        }
    }
    
    auto it = results.find(MAX_CYCLES - 1);
    if (it != results.end()) {
        for (const auto& r : it->second) {
            date_results[r.start] = r;
        }
    }

    std::unordered_map<std::string, std::tuple<double, Result>> weighted_results;
    std::vector<std::string> sorted_dates;
    
    for (const auto& pair : date_results) {
        sorted_dates.push_back(pair.first);
    }
    std::sort(sorted_dates.begin(), sorted_dates.end());
    
    std::unordered_map<std::string, int> date_idx;
    for (size_t i = 0; i < sorted_dates.size(); i++) {
        date_idx[sorted_dates[i]] = static_cast<int>(i);
    }

    for (size_t i = 0; i < sorted_dates.size(); i++) {
        const std::string& start = sorted_dates[i];
        int start_pos = std::max(0, static_cast<int>(i) - CYCLE_DAYS);
        
        std::vector<std::string> last_cycle_dates(
            sorted_dates.begin() + start_pos, 
            sorted_dates.begin() + i
        );
        std::reverse(last_cycle_dates.begin(), last_cycle_dates.end());

        std::unordered_map<std::string, int> end_in_start;
        for (const std::string& d : last_cycle_dates) {
            const Result& res = date_results[d];
            
            auto end_it = date_idx.find(res.end);
            int e = (end_it != date_idx.end()) ? end_it->second : INT_MAX;
            int s = date_idx[start];

            auto prev_it = end_in_start.find(res.end);
            int prev_val = (prev_it != end_in_start.end()) ? prev_it->second : 0;
            
            end_in_start[d] = (std::abs(e - s) <= 1) ? 1 : prev_val;
        }

        double weight = 0.5;
        if (!end_in_start.empty()) {
            int sum = 0;
            for (const auto& pair : end_in_start) {
                sum += pair.second;
            }
            weight = static_cast<double>(sum) / end_in_start.size();
        }

        weighted_results[start] = std::make_tuple(weight, date_results[start]);
    }

    return weighted_results;
}

double compute_fail_rate(const std::unordered_map<int, std::vector<Result>>& results) {
    auto weighted_results = compute_weighted_results(results);

    double n_failed = 0;
    double n_total = 0;

    for (const auto& pair : weighted_results) {
        double weight = std::get<0>(pair.second);
        const Result& result = std::get<1>(pair.second);
        
        if (!result.sold) n_failed += weight;
        n_total += weight;
    }

    return n_total > 0 ? n_failed / n_total : 0;
}

double compute_avg_ror(const std::unordered_map<int, std::vector<Result>>& results) {
    auto weighted_results = compute_weighted_results(results);

    double tot_ror = 0;
    double tot_days = 0;

    for (const auto& pair : weighted_results) {
        double weight = std::get<0>(pair.second);
        const Result& result = std::get<1>(pair.second);
        
        tot_ror += weight * result.ror;
        tot_days += weight * result.days();
    }

    return tot_days > 0 ? (tot_ror / tot_days) * MARKET_DAYS_PER_YEAR : 0;
}

History simulate(
    const std::vector<StockRow>& chart,
    int max_cycle,
    const Config& config,
    const std::unordered_map<std::string, double>& URATE,
    const std::unordered_map<std::string, double>& RSI,
    const std::unordered_map<std::string, double>& VOLATILITY
) {
    std::ostream* log_stream = nullptr;
    std::ofstream log_file;
    
    if (DEBUG) {
        system("mkdir -p logs/test");
        log_file.open("logs/test/" + chart[0].date + "-" + std::to_string(max_cycle) + ".log");
        log_stream = &log_file;
    } else if (VERBOSE) {
        log_stream = &std::cout;
    }

    State s = State::init(SEED, max_cycle);
    s.complete();

    History history;
    for (const auto& c : chart) {
        s = oneday(c, s, config, RSI, VOLATILITY, URATE);
        history.push_back(s);

        if (log_stream) {
            auto rsi_it = RSI.find(c.date);
            auto urate_it = URATE.find(c.date);
            auto vol_it = VOLATILITY.find(c.date);
            
            if (rsi_it != RSI.end() && urate_it != URATE.end() && vol_it != VOLATILITY.end()) {
                *log_stream << s.to_string() << " ||| "
                           << "rsi=" << static_cast<int>(rsi_it->second) 
                           << ", urate=" << static_cast<int>(urate_it->second * 100) << "%, "
                           << "vol=" << static_cast<int>(vol_it->second) << std::endl;
            }
        }

        if (is_sold(s.status)) {
            break;
        } else if (is_exhausted(s.status) && s.cycle_done()) {
            break;
        }
    }

    NUM_SIMULATED++;
    if (!is_sold(s.status) && !is_exhausted(s.status)) {
        NUM_RETIRED++;
    }

    return history;
}

std::tuple<std::unordered_map<int, std::vector<Result>>, 
          std::unordered_map<int, std::vector<History>>, 
          double> test(
    const std::string& ticker,
    const Config& config,
    const std::string& start,
    const std::string& end
) {
    NUM_SIMULATED = 0;
    NUM_RETIRED = 0;

    auto full_chart = read_chart(ticker, "", "");
    auto chart = read_chart(ticker, start, end);

    auto URATE = compute_urates(full_chart, 50, CYCLE_DAYS);
    auto RSI = compute_rsi(full_chart, 5);
    auto VOLATILITY = compute_volatility(full_chart, 5);
    auto SAHM_INDICATOR = read_sahm();

    // Split chart into fractions
    std::vector<std::vector<StockRow>> charts;
    for (size_t i = 0; i + CYCLE_DAYS < chart.size(); i++) {
        std::vector<StockRow> sub_chart(chart.begin() + i, chart.begin() + i + CYCLE_DAYS);
        charts.push_back(sub_chart);
    }

    std::vector<std::vector<StockRow>> current_charts = charts;

    std::unordered_map<int, std::vector<History>> histories;
    std::unordered_map<int, std::vector<Result>> results;

    for (int cycle = 0; cycle < MAX_CYCLES; cycle++) {
        histories[cycle] = {};
        results[cycle] = {};

        for (const auto& sub_chart : current_charts) {
            if (config.sahm_threshold != 0) {
                auto sahm_it = SAHM_INDICATOR.find(sub_chart[0].date);
                if (sahm_it != SAHM_INDICATOR.end() && sahm_it->second > config.sahm_threshold) {
                    continue;
                }
            }

            auto history = simulate(sub_chart, cycle, config, URATE, RSI, VOLATILITY);

            Result result;
            result.start = history[0].date;
            result.end = history.back().date;
            result.sold = is_sold(history.back().status);
            result.ror = history.back().ror;

            histories[cycle].push_back(history);
            results[cycle].push_back(result);
        }

        // Rebuild charts for next cycle
        current_charts.clear();
        for (const auto& res : results[cycle]) {
            if (!res.sold) {
                // Find original chart index
                size_t idx = 0;
                for (size_t i = 0; i < charts.size(); i++) {
                    if (charts[i][0].date == res.start) {
                        idx = i;
                        break;
                    }
                }

                // Check boundary
                if (idx + (cycle + 1) * CYCLE_DAYS >= charts.size()) {
                    continue;
                }

                std::vector<StockRow> extended_chart;
                for (int i = 0; i <= cycle + 1; i++) {
                    size_t chart_idx = idx + i * CYCLE_DAYS;
                    if (chart_idx < charts.size()) {
                        extended_chart.insert(extended_chart.end(), 
                                           charts[chart_idx].begin(), 
                                           charts[chart_idx].end());
                    }
                }

                current_charts.push_back(extended_chart);
            }
        }
    }

    double fail_rate = compute_fail_rate(results);
    double avg_ror_per_year = compute_avg_ror(results);

    double score = 0;
    if (fail_rate < FAIL_LIMIT) {
        score = (1 - FAIL_PENALTY * fail_rate) * avg_ror_per_year * 100;
    }

    std::cout << ticker << ": " << config.to_string() << " | " 
              << std::fixed << std::setprecision(2) << score 
              << " (" << std::setprecision(1) << (avg_ror_per_year * 100) << "%, " 
              << (fail_rate * 100) << "%)" << std::endl;

    if (VERBOSE && NUM_RETIRED > 0.05 * NUM_SIMULATED) {
        std::cout << "[warning] " << std::setprecision(1) 
                  << (static_cast<double>(NUM_RETIRED) / NUM_SIMULATED * 100) 
                  << "% simulations retired" << std::endl;
    }

    std::cout.flush();
    return std::make_tuple(results, histories, score);
}