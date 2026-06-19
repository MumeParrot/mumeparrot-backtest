#pragma once

#include "const.h"
#include "configs.h"
#include <vector>
#include <unordered_map>
#include <string>

std::unordered_map<std::string, double> compute_dca_rsi(const std::vector<StockRow>& full_chart);

std::vector<State> run_dca_backtest(
    const std::vector<StockRow>& chart,
    const std::unordered_map<std::string, double>& rsi_dict,
    const Config& config
);
