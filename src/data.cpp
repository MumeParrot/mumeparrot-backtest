#include "data.h"
#include "env.h"
#include <fstream>
#include <sstream>
#include <random>
#include <numeric>
#include <algorithm>
#include <iostream>

// TICKERS is defined in env.cpp

std::vector<std::string> split(const std::string& str, char delimiter) {
    std::vector<std::string> tokens;
    std::stringstream ss(str);
    std::string token;
    
    while (std::getline(ss, token, delimiter)) {
        tokens.push_back(token);
    }
    
    return tokens;
}

std::vector<StockRow> read_chart(const std::string& ticker, const std::string& start, 
                                const std::string& end, bool test_mode) {
    std::string upper_ticker = ticker;
    std::transform(upper_ticker.begin(), upper_ticker.end(), upper_ticker.begin(), ::toupper);
    
    if (TICKERS.find(upper_ticker) == TICKERS.end()) {
        throw std::runtime_error("'" + upper_ticker + "' is not supported");
    }

    std::vector<StockRow> history;
    std::ifstream file(std::string(CHARTS_PATH) + "/" + upper_ticker + "-GEN.csv");
    
    if (!file.is_open()) {
        throw std::runtime_error("Could not open chart file for " + upper_ticker);
    }

    std::string line;
    std::vector<std::tuple<std::string, double, double>> raw_data;
    
    while (std::getline(file, line)) {
        auto tokens = split(line, ',');
        if (tokens.size() >= 3) {
            std::string date = tokens[0];
            double price = std::stod(tokens[1]);
            double close_price = std::stod(tokens[2]);
            raw_data.emplace_back(date, price, close_price);
        }
    }
    
    if (test_mode && !raw_data.empty()) {
        // Calculate mean fluctuation for test mode
        double total_fluc = 0.0;
        for (const auto& [date, p, cp] : raw_data) {
            total_fluc += std::abs((cp - p) / p);
        }
        double mean_flucs = total_fluc / raw_data.size();
        
        // Random number generator for test mode
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_real_distribution<> dis(0.0, 1.0);
        
        for (const auto& [date, p, cp] : raw_data) {
            double adj_p = (1 - (mean_flucs / 2) + dis(gen) * mean_flucs) * p;
            double adj_cp = (1 - (mean_flucs / 2) + dis(gen) * mean_flucs) * cp;
            history.emplace_back(date, adj_p, adj_cp);
        }
    } else {
        for (const auto& [date, p, cp] : raw_data) {
            history.emplace_back(date, p, cp);
        }
    }

    // Filter by start and end dates
    size_t start_idx = 0;
    size_t end_idx = history.size();
    
    if (!start.empty()) {
        for (size_t i = 0; i < history.size(); ++i) {
            if (history[i].date.substr(0, start.length()) == start) {
                start_idx = i;
                break;
            }
        }
    }
    
    if (!end.empty()) {
        for (int i = static_cast<int>(history.size()) - 1; i >= 0; --i) {
            if (history[i].date.substr(0, end.length()) == end) {
                end_idx = i + 1;
                break;
            }
        }
    }
    
    return std::vector<StockRow>(history.begin() + start_idx, history.begin() + end_idx);
}

std::vector<StockRow> read_base_chart(const std::string& ticker, const std::string& start, 
                                     const std::string& end) {
    std::string upper_ticker = ticker;
    std::transform(upper_ticker.begin(), upper_ticker.end(), upper_ticker.begin(), ::toupper);
    
    // Check if ticker is in the values of TICKERS map
    bool found = false;
    for (const auto& pair : TICKERS) {
        if (pair.second == upper_ticker) {
            found = true;
            break;
        }
    }
    
    if (!found) {
        throw std::runtime_error("'" + upper_ticker + "' is not supported");
    }

    std::vector<StockRow> history;
    std::ifstream file(std::string(CHARTS_PATH) + "/" + upper_ticker + ".csv");
    
    if (!file.is_open()) {
        throw std::runtime_error("Could not open base chart file for " + upper_ticker);
    }

    std::string line;
    std::getline(file, line); // Skip header
    
    while (std::getline(file, line)) {
        auto tokens = split(line, ',');
        if (tokens.size() >= 6) {
            std::string date = tokens[0];
            double open = std::stod(tokens[1]);
            double close = std::stod(tokens[4]);
            history.emplace_back(date, open, close);
        }
    }

    // Filter by start and end dates
    size_t start_idx = 0;
    size_t end_idx = history.size();
    
    if (!start.empty()) {
        for (size_t i = 0; i < history.size(); ++i) {
            if (history[i].date.substr(0, start.length()) == start) {
                start_idx = i;
                break;
            }
        }
    }
    
    if (!end.empty()) {
        for (int i = static_cast<int>(history.size()) - 1; i >= 0; --i) {
            if (history[i].date.substr(0, end.length()) == end) {
                end_idx = i + 1;
                break;
            }
        }
    }
    
    return std::vector<StockRow>(history.begin() + start_idx, history.begin() + end_idx);
}

std::unordered_map<std::string, double> read_sahm() {
    std::unordered_map<std::string, double> sahm;
    std::ifstream file(std::string(INDICES_PATH) + "/sahm.csv");
    
    if (!file.is_open()) {
        return sahm; // Return empty map if file doesn't exist
    }

    std::string line;
    std::getline(file, line); // Skip header
    
    while (std::getline(file, line)) {
        auto tokens = split(line, ',');
        if (tokens.size() >= 2) {
            std::string date = tokens[0];
            double value = std::stod(tokens[1]);
            sahm[date] = value;
        }
    }
    
    return sahm;
}

std::unordered_map<std::string, double> compute_rsi(const std::vector<StockRow>& chart, int term) {
    std::unordered_map<std::string, double> rsis;
    
    auto compute = [term](const std::vector<double>& ps) -> double {
        if (static_cast<int>(ps.size()) <= term) {
            return 50.0;
        }
        
        std::vector<double> diffs;
        for (size_t i = 1; i < ps.size(); ++i) {
            diffs.push_back(ps[i] - ps[i-1]);
        }
        
        double tot_change = 0.0;
        double upgoing = 0.0;
        
        for (double d : diffs) {
            tot_change += std::abs(d);
            if (d > 0) upgoing += d;
        }
        
        return (tot_change > 0) ? 100.0 * upgoing / tot_change : 50.0;
    };
    
    std::vector<double> prices;
    for (const auto& row : chart) {
        prices.push_back(row.close_price);
        if (static_cast<int>(prices.size()) > term + 1) {
            prices.erase(prices.begin());
        }
        
        rsis[row.date] = compute(prices);
    }
    
    return rsis;
}

std::unordered_map<std::string, double> compute_volatility(const std::vector<StockRow>& chart, int term) {
    std::unordered_map<std::string, double> volatility;
    
    auto compute = [term](const std::vector<double>& ps) -> double {
        if (static_cast<int>(ps.size()) <= term) {
            return 0.0;
        }
        
        std::vector<double> diffs;
        for (size_t i = 1; i < ps.size(); ++i) {
            diffs.push_back(ps[i] - ps[i-1]);
        }
        
        double tot_change = 0.0;
        for (double d : diffs) {
            tot_change += std::abs(d);
        }
        
        double last_change = diffs.back();
        return 100.0 * last_change / tot_change;
    };
    
    std::vector<double> prices;
    for (const auto& row : chart) {
        prices.push_back(row.close_price);
        if (static_cast<int>(prices.size()) > term + 1) {
            prices.erase(prices.begin());
        }
        
        volatility[row.date] = compute(prices);
    }
    
    return volatility;
}

std::unordered_map<std::string, double> compute_moving_average(const std::vector<StockRow>& chart, int term) {
    std::unordered_map<std::string, double> avg_history;
    
    std::vector<double> prices;
    for (const auto& row : chart) {
        prices.push_back(row.close_price);
        if (static_cast<int>(prices.size()) > term) {
            prices.erase(prices.begin());
        }
        
        double sum = std::accumulate(prices.begin(), prices.end(), 0.0);
        avg_history[row.date] = prices.empty() ? row.price : sum / prices.size();
    }
    
    return avg_history;
}

std::unordered_map<std::string, double> compute_urates(const std::vector<StockRow>& chart, int avg, int term) {
    auto avg_history = compute_moving_average(chart, avg);
    std::unordered_map<std::string, double> u_rates;
    
    std::vector<int> u_counters;
    for (const auto& row : chart) {
        int under = (row.close_price < avg_history[row.date]) ? 1 : 0;
        u_counters.push_back(under);
        
        if (static_cast<int>(u_counters.size()) > term) {
            u_counters.erase(u_counters.begin());
        }
        
        double sum = std::accumulate(u_counters.begin(), u_counters.end(), 0.0);
        u_rates[row.date] = sum / u_counters.size();
    }
    
    return u_rates;
}