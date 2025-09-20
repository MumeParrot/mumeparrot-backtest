#pragma once

#include <string>
#include <unordered_map>
#include <tuple>

struct Description {
    std::string term = "number of days to split the seed and buy the stock";
    std::string margin = "margin to sell the stock";
    std::string bullish_rsi = "rsi threshold to buy the stock";
    std::string burst_urate = "rate of market days under 50 moving average to determine burst buy and ";
    std::string burst_scale = "scale of burst buy when the market fluctuates";
    std::string burst_vol = "volatility threshold to determine burst buy";
    std::string sell_base = "base sell rate when all seed is exhausted";
    std::string sell_limit = "sell limit when all seed is exhausted";
    std::string sahm_threshold = "sahm threshold to exclude when sliding window test";
};

struct Bounds {
    std::tuple<int, int> term = {40, 40};
    std::tuple<double, double> margin = {0.05, 0.15};
    std::tuple<int, int> bullish_rsi = {60, 100};
    std::tuple<double, double> burst_urate = {0.3, 0.8};
    std::tuple<double, double> burst_scale = {0.0, 3.0};
    std::tuple<int, int> burst_vol = {25, 50};
    std::tuple<double, double> sell_base = {0, 0.5};
    std::tuple<double, double> sell_limit = {0.5, 1.0};
    std::tuple<double, double> sahm_threshold = {1.0, 1.0};
};

struct Precisions {
    int term = 1;
    double margin = 0.01;
    int bullish_rsi = 5;
    double burst_urate = 0.1;
    double burst_scale = 0.5;
    int burst_vol = 5;
    double sell_base = 0.1;
    double sell_limit = 0.1;
    double sahm_threshold = 0.5;
};

struct Config {
    int term = 40;
    double margin = 0.1;
    int bullish_rsi = 80;
    double burst_urate = 0.5;
    double burst_scale = 0.0;
    int burst_vol = 30;
    double sell_base = 0.0;
    double sell_limit = 1.0;
    double sahm_threshold = 1.0;

    static Config from_map(const std::unordered_map<std::string, double>& source);
    
    std::size_t hash() const;
    std::string to_string() const;
    
    bool operator==(const Config& other) const;
};