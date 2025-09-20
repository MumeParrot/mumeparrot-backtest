#include "src/env.h"
#include "src/test.h"
#include "src/full.h"
#include "src/configs.h"
#include <iostream>
#include <string>
#include <csignal>

bool stop_flag = false;

void sigint_handler(int sig) {
    stop_flag = true;
}

template<typename T>
T get_arg(const std::string& name, T default_val = T{}, const std::string& explain = "") {
    std::string default_str = "";
    if constexpr (std::is_same_v<T, bool>) {
        default_str = default_val ? " [default=y]" : " [default=n]";
    } else if constexpr (std::is_same_v<T, std::string>) {
        default_str = " [default=" + default_val + "]";
    } else {
        default_str = " [default=" + std::to_string(default_val) + "]";
    }
    
    std::string explain_text = explain.empty() ? "" : "(" + explain + ")";
    
    std::cout << name << default_str << explain_text << ": ";
    
    std::string input;
    std::getline(std::cin, input);
    
    if (std::cin.eof() || std::cin.fail()) {
        std::cout << std::endl;
        exit(0);  // Exit cleanly on EOF (Ctrl+D)
    }
    
    if constexpr (std::is_same_v<T, bool>) {
        if (!input.empty()) {
            return input == "y";
        }
        return default_val;
    } else if constexpr (std::is_same_v<T, std::string>) {
        return input.empty() ? default_val : input;
    } else {
        if (input.empty()) {
            return default_val;
        }
        if constexpr (std::is_same_v<T, int>) {
            return std::stoi(input);
        } else if constexpr (std::is_same_v<T, double>) {
            return std::stod(input);
        }
    }
    
    return default_val;
}

int main() {
    signal(SIGINT, sigint_handler);
    
    try {
        init_env();
    } catch (const std::exception& e) {
        std::cerr << "Error initializing environment: " << e.what() << std::endl;
        return 1;
    }
    
    print_env();

    while (true) {
        stop_flag = false;

        try {
            std::string mode = get_arg<std::string>("mode", "p");
            
            if (mode.substr(0, 1) == "p") {  // plot
                std::string ticker = get_arg<std::string>("ticker", "all");
                // plot_chart(ticker, START, END); // TODO: implement plotting
                std::cout << "Plotting not implemented yet" << std::endl;

            } else if (mode.substr(0, 1) == "t") {  // test
                if (BOXX) {
                    std::cout << "[-] Test mode not supported with BOXX" << std::endl;
                    return 1;
                }

                std::string ticker = get_arg<std::string>("ticker", "all");
                std::string config_mode = get_arg<std::string>("config", "best", "type 'n' to manually set");

                Config config;
                if (config_mode != "best") {
                    config.term = get_arg<int>("term", ticker == "all" ? 0 : BEST_CONFIGS[ticker].term);
                    config.margin = get_arg<double>("margin", ticker == "all" ? 0.0 : BEST_CONFIGS[ticker].margin);
                    config.bullish_rsi = get_arg<int>("bullish_rsi", ticker == "all" ? 0 : BEST_CONFIGS[ticker].bullish_rsi);
                    config.burst_urate = get_arg<double>("burst_urate", ticker == "all" ? 0.0 : BEST_CONFIGS[ticker].burst_urate);
                    config.burst_scale = get_arg<double>("burst_scale", ticker == "all" ? 0.0 : BEST_CONFIGS[ticker].burst_scale);
                    config.burst_vol = get_arg<int>("burst_vol", ticker == "all" ? 0 : BEST_CONFIGS[ticker].burst_vol);
                    config.sell_base = get_arg<double>("sell_base", ticker == "all" ? 0.0 : BEST_CONFIGS[ticker].sell_base);
                    config.sell_limit = get_arg<double>("sell_limit", ticker == "all" ? 0.0 : BEST_CONFIGS[ticker].sell_limit);
                    config.sahm_threshold = get_arg<double>("sahm_threshold", ticker == "all" ? 0.0 : BEST_CONFIGS[ticker].sahm_threshold);
                }

                if (ticker != "all") {
                    if (config_mode == "best") {
                        config = BEST_CONFIGS[ticker];
                    }
                    test(ticker, config, START, END);
                } else {
                    for (const auto& [t, base] : TICKERS) {
                        Config test_config = BEST_CONFIGS[t];
                        if (config_mode != "best") {
                            test_config = config;
                        }
                        test(t, test_config, START, END);
                    }
                }

            } else if (mode.substr(0, 1) == "f") {  // full
                std::string ticker = get_arg<std::string>("ticker", "SOXL");
                std::string config_mode = get_arg<std::string>("config", "best");

                Config config = BEST_CONFIGS[ticker];
                if (config_mode != "best") {
                    config.term = get_arg<int>("term", BEST_CONFIGS[ticker].term);
                    config.margin = get_arg<double>("margin", BEST_CONFIGS[ticker].margin);
                    config.bullish_rsi = get_arg<int>("bullish_rsi", BEST_CONFIGS[ticker].bullish_rsi);
                    config.burst_urate = get_arg<double>("burst_urate", BEST_CONFIGS[ticker].burst_urate);
                    config.burst_scale = get_arg<double>("burst_scale", BEST_CONFIGS[ticker].burst_scale);
                    config.burst_vol = get_arg<int>("burst_vol", BEST_CONFIGS[ticker].burst_vol);
                    config.sell_base = get_arg<double>("sell_base", BEST_CONFIGS[ticker].sell_base);
                    config.sell_limit = get_arg<double>("sell_limit", BEST_CONFIGS[ticker].sell_limit);
                    config.sahm_threshold = get_arg<double>("sahm_threshold", BEST_CONFIGS[ticker].sahm_threshold);
                }

                auto [history, avg_ir] = full(ticker, config, START, END, TEST_MODE);
                if (GRAPH) {
                    // plot_full(ticker, START, END, history); // TODO: implement plotting
                    std::cout << "Plotting not implemented yet" << std::endl;
                }

            } else if (mode.substr(0, 1) == "h") {  // help
                std::cout << "=== MumeParrot backtest ===" << std::endl;
                std::cout << "Usage: ./backtest" << std::endl;
                std::cout << " Modes:" << std::endl;
                std::cout << "  -h) print this help message" << std::endl;
                std::cout << "  -t) sliding window test" << std::endl;
                std::cout << "  -f) full simulation" << std::endl;
                std::cout << " Tickers:" << std::endl;
                std::cout << "   all";
                int count = 0;
                for (const auto& [ticker, base] : TICKERS) {
                    std::cout << ", " << ticker;
                    if (++count % 5 == 0) {
                        std::cout << std::endl << "   ";
                    }
                }
                std::cout << std::endl;
                
                std::cout << " Config:" << std::endl;
                Description desc;
                std::cout << "  term: " << desc.term << std::endl;
                std::cout << "  margin: " << desc.margin << std::endl;
                std::cout << "  bullish_rsi: " << desc.bullish_rsi << std::endl;
                std::cout << "  burst_urate: " << desc.burst_urate << std::endl;
                std::cout << "  burst_scale: " << desc.burst_scale << std::endl;
                std::cout << "  burst_vol: " << desc.burst_vol << std::endl;
                std::cout << "  sell_base: " << desc.sell_base << std::endl;
                std::cout << "  sell_limit: " << desc.sell_limit << std::endl;
                std::cout << "  sahm_threshold: " << desc.sahm_threshold << std::endl;
                
                std::cout << "(Environment variables)" << std::endl;
                std::cout << " TICKER_FILE: path to ticker file (default: tickers.json)" << std::endl;
                std::cout << " CONFIGS_FILE: path to best configs file (default: configs.json)" << std::endl;
                std::cout << " START: start date in 'yyyy-mm-dd' format (default: empty)" << std::endl;
                std::cout << " END: end date in 'yyyy-mm-dd' format (default: empty)" << std::endl;
                std::cout << " CYCLE_DAYS: number of days to simulate per cycle (default: 60)" << std::endl;
                std::cout << " SEED: amount of seed (default: 1000000)" << std::endl;
                std::cout << " MAX_CYCLES: maximum cycles (default: 2)" << std::endl;
                std::cout << " FAIL_PENALTY: penalty for cycle failure (default: 2)" << std::endl;
                std::cout << " FAIL_LIMIT: limit for cycle failure (default: 0.1)" << std::endl;
                std::cout << " DEBUG: set to log history under 'logs/test (default: 0)" << std::endl;
                std::cout << " VERBOSE: set to print history (default: 0)" << std::endl;
                std::cout << " GRAPH: print graph when full simulation (default: 0)" << std::endl;
            }

        } catch (const std::runtime_error& e) {
            if (std::string(e.what()) == "stop = true") {
                continue;
            }
            std::cerr << "Error: " << e.what() << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "Error: " << e.what() << std::endl;
        }
    }

    return 0;
}