#include "src/env.h"
#include "src/test.h"
#include "src/full.h"
#include "src/configs.h"
#include <iostream>
#include <vector>
#include <random>
#include <algorithm>
#include <functional>
#include <sstream>

// Simple differential evolution implementation
class DifferentialEvolution {
public:
    using ObjectiveFunction = std::function<double(const std::vector<double>&)>;
    
    struct Bounds {
        double min, max;
    };
    
private:
    ObjectiveFunction objective;
    std::vector<Bounds> bounds;
    int population_size;
    double F = 0.5;  // mutation factor
    double CR = 0.9; // crossover probability
    int max_generations = 1000;
    std::mt19937 rng;
    
public:
    DifferentialEvolution(ObjectiveFunction obj, std::vector<Bounds> b, int pop_size = 50)
        : objective(obj), bounds(b), population_size(pop_size), rng(std::random_device{}()) {}
    
    std::vector<double> optimize() {
        int dimensions = bounds.size();
        std::uniform_real_distribution<double> uniform(0.0, 1.0);
        
        // Initialize population
        std::vector<std::vector<double>> population(population_size);
        std::vector<double> fitness(population_size);
        
        for (int i = 0; i < population_size; ++i) {
            population[i].resize(dimensions);
            for (int j = 0; j < dimensions; ++j) {
                population[i][j] = bounds[j].min + uniform(rng) * (bounds[j].max - bounds[j].min);
            }
            fitness[i] = objective(population[i]);
        }
        
        // Evolution loop
        for (int gen = 0; gen < max_generations; ++gen) {
            for (int i = 0; i < population_size; ++i) {
                // Select three random individuals different from current
                std::vector<int> indices;
                for (int k = 0; k < population_size; ++k) {
                    if (k != i) indices.push_back(k);
                }
                std::shuffle(indices.begin(), indices.end(), rng);
                
                int a = indices[0], b = indices[1], c = indices[2];
                
                // Mutation and crossover
                std::vector<double> trial = population[i];
                int jrand = std::uniform_int_distribution<int>(0, dimensions - 1)(rng);
                
                for (int j = 0; j < dimensions; ++j) {
                    if (uniform(rng) < CR || j == jrand) {
                        trial[j] = population[a][j] + F * (population[b][j] - population[c][j]);
                        // Bounds checking
                        trial[j] = std::max(bounds[j].min, std::min(bounds[j].max, trial[j]));
                    }
                }
                
                // Selection
                double trial_fitness = objective(trial);
                if (trial_fitness < fitness[i]) {
                    population[i] = trial;
                    fitness[i] = trial_fitness;
                }
            }
            
            // Print best fitness periodically
            if (gen % 100 == 0) {
                auto best_it = std::min_element(fitness.begin(), fitness.end());
                std::cout << "Generation " << gen << ": Best fitness = " << *best_it << std::endl;
            }
        }
        
        // Return best solution
        auto best_it = std::min_element(fitness.begin(), fitness.end());
        int best_idx = std::distance(fitness.begin(), best_it);
        return population[best_idx];
    }
};

void print_usage() {
    std::cout << "Usage: optimize [OPTIONS]" << std::endl;
    std::cout << "Options:" << std::endl;
    std::cout << "  -m, --mode [t|f|a]     Test-mode optimize, full-mode optimize or analyze" << std::endl;
    std::cout << "  -t, --ticker TICKER     Ticker symbol to optimize" << std::endl;
    std::cout << "  -f, --fixed PARAMS      Fixed config parameters (format: key1:val1,key2:val2)" << std::endl;
    std::cout << "  -h, --help              Show this help message" << std::endl;
}

std::unordered_map<std::string, double> parse_fixed_params(const std::string& fixed_str) {
    std::unordered_map<std::string, double> fixed;
    
    if (fixed_str.empty()) return fixed;
    
    std::stringstream ss(fixed_str);
    std::string param;
    
    while (std::getline(ss, param, ',')) {
        size_t colon_pos = param.find(':');
        if (colon_pos != std::string::npos) {
            std::string key = param.substr(0, colon_pos);
            std::string value_str = param.substr(colon_pos + 1);
            try {
                double value = std::stod(value_str);
                fixed[key] = value;
            } catch (const std::exception&) {
                throw std::runtime_error("Invalid format for fixed parameter: " + param);
            }
        }
    }
    
    return fixed;
}

int main(int argc, char* argv[]) {
    std::string mode = "t";
    std::string ticker;
    std::string fixed_str;
    
    // Simple command line parsing
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        
        if (arg == "-h" || arg == "--help") {
            print_usage();
            return 0;
        } else if (arg == "-m" || arg == "--mode") {
            if (i + 1 < argc) {
                mode = argv[++i];
                if (mode != "t" && mode != "f" && mode != "a") {
                    std::cerr << "Invalid mode. Must be t, f, or a." << std::endl;
                    return 1;
                }
            }
        } else if (arg == "-t" || arg == "--ticker") {
            if (i + 1 < argc) {
                ticker = argv[++i];
            }
        } else if (arg == "-f" || arg == "--fixed") {
            if (i + 1 < argc) {
                fixed_str = argv[++i];
            }
        }
    }
    
    try {
        init_env();
    } catch (const std::exception& e) {
        std::cerr << "Error initializing environment: " << e.what() << std::endl;
        return 1;
    }
    
    print_env();
    
    if (mode == "a") {
        // Analyze mode - would need to implement result analysis
        std::cout << "Analysis mode not yet implemented" << std::endl;
        return 0;
    }
    
    if (ticker.empty() || TICKERS.find(ticker) == TICKERS.end()) {
        std::cerr << "Valid ticker required. Available tickers: ";
        for (const auto& [t, base] : TICKERS) {
            std::cout << t << " ";
        }
        std::cout << std::endl;
        return 1;
    }
    
    auto fixed = parse_fixed_params(fixed_str);
    Config base_config = BEST_CONFIGS[ticker];
    Bounds opt_bounds;
    
    // Set up optimization variables and bounds
    std::vector<std::string> variable_names;
    std::vector<DifferentialEvolution::Bounds> bounds;
    
    if (fixed.find("term") == fixed.end()) {
        variable_names.push_back("term");
        bounds.push_back({static_cast<double>(std::get<0>(opt_bounds.term)), 
                         static_cast<double>(std::get<1>(opt_bounds.term))});
    }
    if (fixed.find("margin") == fixed.end()) {
        variable_names.push_back("margin");
        bounds.push_back({std::get<0>(opt_bounds.margin), std::get<1>(opt_bounds.margin)});
    }
    // Add other parameters similarly...
    
    auto objective = [&](const std::vector<double>& vars) -> double {
        Config config = base_config;
        
        // Apply fixed parameters
        for (const auto& [key, value] : fixed) {
            if (key == "term") config.term = static_cast<int>(value);
            else if (key == "margin") config.margin = value;
            else if (key == "bullish_rsi") config.bullish_rsi = static_cast<int>(value);
            else if (key == "burst_urate") config.burst_urate = value;
            else if (key == "burst_scale") config.burst_scale = value;
            else if (key == "burst_vol") config.burst_vol = static_cast<int>(value);
            else if (key == "sell_base") config.sell_base = value;
            else if (key == "sell_limit") config.sell_limit = value;
            else if (key == "sahm_threshold") config.sahm_threshold = value;
        }
        
        // Apply optimization variables
        for (size_t i = 0; i < vars.size(); ++i) {
            const std::string& var_name = variable_names[i];
            double value = vars[i];
            
            if (var_name == "term") config.term = static_cast<int>(value);
            else if (var_name == "margin") config.margin = value;
            // Add other parameters...
        }
        
        try {
            if (mode == "t") {
                auto [results, histories, score] = test(ticker, config, START, END);
                return -score; // Negative because we want to maximize
            } else { // mode == "f"
                auto [history, avg_ir] = full(ticker, config, START, END, true);
                return -avg_ir; // Negative because we want to maximize
            }
        } catch (const std::exception& e) {
            return 1e6; // Large penalty for failed evaluations
        }
    };
    
    if (bounds.empty()) {
        std::cout << "No parameters to optimize (all are fixed)" << std::endl;
        return 0;
    }
    
    DifferentialEvolution optimizer(objective, bounds);
    auto result = optimizer.optimize();
    
    std::cout << "Optimization complete!" << std::endl;
    std::cout << "Best parameters:" << std::endl;
    for (size_t i = 0; i < result.size(); ++i) {
        std::cout << "  " << variable_names[i] << ": " << result[i] << std::endl;
    }
    std::cout << "Best objective value: " << -objective(result) << std::endl;
    
    return 0;
}