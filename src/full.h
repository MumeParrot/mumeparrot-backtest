#pragma once

#include "const.h"
#include "configs.h"
#include <unordered_map>
#include <vector>
#include <tuple>

History full_backtest(
    const Config& config,
    const std::vector<StockRow>& chart,
    const std::unordered_map<std::string, double>& urates,
    const std::unordered_map<std::string, double>& rsis,
    const std::unordered_map<std::string, double>& volatilities,
    std::ostream* log_stream = nullptr,
    const std::vector<StockRow>& base_chart = {}
);

std::tuple<History, double> full(
    const std::string& ticker,
    const Config& config,
    const std::string& start,
    const std::string& end,
    bool test_mode = false
);