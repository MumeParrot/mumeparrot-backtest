#pragma once

#include "configs.h"
#include <string>
#include <unordered_map>

extern std::string START;
extern std::string END;
extern int MARKET_DAYS_PER_YEAR;

extern std::string TICKER_FILE;
extern std::string CONFIGS_FILE;

extern std::unordered_map<std::string, std::string> TICKERS;
extern std::unordered_map<std::string, Config> BEST_CONFIGS;

extern bool DEBUG;
extern bool VERBOSE;

extern int CYCLE_DAYS;
extern int SEED;
extern int MAX_CYCLES;

extern int FAIL_PENALTY;
extern double FAIL_LIMIT;

extern double COMMISSION_RATE;

extern bool GRAPH;
extern bool BOXX;

extern double BOXX_UNIT;
extern double BOXX_IR;

extern bool TEST_MODE;

void init_env();
void print_env();