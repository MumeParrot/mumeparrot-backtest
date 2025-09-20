#pragma once

#include "const.h"
#include "configs.h"
#include <unordered_map>

State oneday(
    const StockRow& c,
    const State& s,
    const Config& config,
    const std::unordered_map<std::string, double>& RSI,
    const std::unordered_map<std::string, double>& VOLATILITY,
    const std::unordered_map<std::string, double>& URATE
);