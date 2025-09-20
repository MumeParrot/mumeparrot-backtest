#pragma once

#include "const.h"
#include "configs.h"
#include <unordered_map>
#include <vector>
#include <tuple>

extern int NUM_SIMULATED;
extern int NUM_RETIRED;

std::unordered_map<std::string, std::tuple<double, Result>> compute_weighted_results(
    const std::unordered_map<int, std::vector<Result>>& results
);

double compute_fail_rate(const std::unordered_map<int, std::vector<Result>>& results);

double compute_avg_ror(const std::unordered_map<int, std::vector<Result>>& results);

History simulate(
    const std::vector<StockRow>& chart,
    int max_cycle,
    const Config& config,
    const std::unordered_map<std::string, double>& URATE,
    const std::unordered_map<std::string, double>& RSI,
    const std::unordered_map<std::string, double>& VOLATILITY
);

std::tuple<std::unordered_map<int, std::vector<Result>>, 
          std::unordered_map<int, std::vector<History>>, 
          double> test(
    const std::string& ticker,
    const Config& config,
    const std::string& start,
    const std::string& end
);