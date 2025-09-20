#include "env.h"
#include <fstream>
#include <iostream>
#include <cstdlib>
#include <stdexcept>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

std::string START;
std::string END;
int MARKET_DAYS_PER_YEAR = 260;

std::string TICKER_FILE = "tickers.json";
std::string CONFIGS_FILE = "configs.json";

std::unordered_map<std::string, std::string> TICKERS;
std::unordered_map<std::string, Config> BEST_CONFIGS;

bool DEBUG = false;
bool VERBOSE = false;

int CYCLE_DAYS = 60;
int SEED = 1000000;
int MAX_CYCLES = 2;

int FAIL_PENALTY = 2;
double FAIL_LIMIT = 0.1;

double COMMISSION_RATE = 0.0;

bool GRAPH = false;
bool BOXX = false;

double BOXX_UNIT = 0.125;
double BOXX_IR = 0.045;

bool TEST_MODE = false;

std::string get_env_var(const std::string& name, const std::string& default_val = "") {
    const char* val = std::getenv(name.c_str());
    return val ? std::string(val) : default_val;
}

int get_env_int(const std::string& name, int default_val = 0) {
    const char* val = std::getenv(name.c_str());
    return val ? std::atoi(val) : default_val;
}

double get_env_double(const std::string& name, double default_val = 0.0) {
    const char* val = std::getenv(name.c_str());
    return val ? std::atof(val) : default_val;
}

bool get_env_bool(const std::string& name, bool default_val = false) {
    const char* val = std::getenv(name.c_str());
    return val ? (std::atoi(val) != 0) : default_val;
}

void init_env() {
    START = get_env_var("START");
    END = get_env_var("END");
    
    TICKER_FILE = get_env_var("TICKER_FILE", "tickers.json");
    CONFIGS_FILE = get_env_var("CONFIGS_FILE", "configs.json");
    
    // Load tickers
    std::ifstream ticker_file(TICKER_FILE);
    if (!ticker_file.is_open()) {
        throw std::runtime_error("Could not open " + TICKER_FILE);
    }
    
    json ticker_json;
    ticker_file >> ticker_json;
    
    for (auto& [key, value] : ticker_json.items()) {
        TICKERS[key] = value["base"];
    }
    
    // Load configs
    std::ifstream config_file(CONFIGS_FILE);
    if (!config_file.is_open()) {
        throw std::runtime_error("Could not open " + CONFIGS_FILE);
    }
    
    json config_json;
    config_file >> config_json;
    
    for (const auto& ticker : TICKERS) {
        if (config_json.contains(ticker.first)) {
            std::unordered_map<std::string, double> config_map;
            for (auto& [key, value] : config_json[ticker.first].items()) {
                config_map[key] = value;
            }
            BEST_CONFIGS[ticker.first] = Config::from_map(config_map);
        }
    }
    
    DEBUG = get_env_bool("DEBUG");
    VERBOSE = get_env_bool("VERBOSE");
    
    CYCLE_DAYS = get_env_int("CYCLE_DAYS", 60);
    SEED = get_env_int("SEED", 1000000);
    MAX_CYCLES = get_env_int("MAX_CYCLES", 2);
    
    FAIL_PENALTY = get_env_int("FAIL_PENALTY", 2);
    FAIL_LIMIT = get_env_double("FAIL_LIMIT", 0.1);
    
    COMMISSION_RATE = get_env_double("COMMISSION_RATE", 0.0);
    if (COMMISSION_RATE >= 0.01) {
        throw std::runtime_error("Commission rate cannot exceed 0.01");
    }
    
    GRAPH = get_env_bool("GRAPH");
    BOXX = get_env_bool("BOXX");
    
    BOXX_UNIT = get_env_double("BOXX_UNIT", 0.125);
    BOXX_IR = get_env_double("BOXX_IR", 0.045);
    
    TEST_MODE = get_env_bool("TEST_MODE");
}

void print_env() {
    std::cout << "Environment variables:" << std::endl;
    std::cout << "START: " << START << std::endl;
    std::cout << "END: " << END << std::endl;
    std::cout << "MARKET_DAYS_PER_YEAR: " << MARKET_DAYS_PER_YEAR << std::endl;
    std::cout << "TICKER_FILE: " << TICKER_FILE << std::endl;
    std::cout << "CONFIGS_FILE: " << CONFIGS_FILE << std::endl;
    std::cout << "DEBUG: " << DEBUG << std::endl;
    std::cout << "VERBOSE: " << VERBOSE << std::endl;
    std::cout << "CYCLE_DAYS: " << CYCLE_DAYS << std::endl;
    std::cout << "SEED: " << SEED << std::endl;
    std::cout << "MAX_CYCLES: " << MAX_CYCLES << std::endl;
    std::cout << "FAIL_PENALTY: " << FAIL_PENALTY << std::endl;
    std::cout << "FAIL_LIMIT: " << FAIL_LIMIT << std::endl;
    std::cout << "COMMISSION_RATE: " << COMMISSION_RATE << std::endl;
    std::cout << "GRAPH: " << GRAPH << std::endl;
    std::cout << "BOXX: " << BOXX << std::endl;
    std::cout << "BOXX_UNIT: " << BOXX_UNIT << std::endl;
    std::cout << "BOXX_IR: " << BOXX_IR << std::endl;
    std::cout << "TEST_MODE: " << TEST_MODE << std::endl;
    
    std::cout << "BEST_CONFIGS:" << std::endl;
    for (const auto& [ticker, config] : BEST_CONFIGS) {
        std::cout << "  " << ticker << ": " << config.to_string() << std::endl;
    }
    std::cout << std::endl;
}