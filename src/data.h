#pragma once

#include "const.h"
#include <vector>
#include <unordered_map>
#include <string>

constexpr const char* CHARTS_PATH = "charts";
constexpr const char* INDICES_PATH = "indices";

std::vector<StockRow> read_chart(const std::string& ticker, const std::string& start, 
                                const std::string& end, bool test_mode = false);

std::vector<StockRow> read_base_chart(const std::string& ticker, const std::string& start, 
                                     const std::string& end);

std::unordered_map<std::string, double> read_sahm();

std::unordered_map<std::string, double> compute_rsi(const std::vector<StockRow>& chart, int term);

std::unordered_map<std::string, double> compute_volatility(const std::vector<StockRow>& chart, int term);

std::unordered_map<std::string, double> compute_moving_average(const std::vector<StockRow>& chart, int term);

std::unordered_map<std::string, double> compute_urates(const std::vector<StockRow>& chart, int avg, int term);

extern std::unordered_map<std::string, std::string> TICKERS;