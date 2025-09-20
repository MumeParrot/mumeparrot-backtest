#include "configs.h"
#include <sstream>
#include <iomanip>
#include <functional>

Config Config::from_map(const std::unordered_map<std::string, double>& source) {
    Config config;
    
    auto it = source.find("term");
    if (it != source.end()) config.term = static_cast<int>(it->second);
    
    it = source.find("margin");
    if (it != source.end()) config.margin = it->second;
    
    it = source.find("bullish_rsi");
    if (it != source.end()) config.bullish_rsi = static_cast<int>(it->second);
    
    it = source.find("burst_urate");
    if (it != source.end()) config.burst_urate = it->second;
    
    it = source.find("burst_scale");
    if (it != source.end()) config.burst_scale = it->second;
    
    it = source.find("burst_vol");
    if (it != source.end()) config.burst_vol = static_cast<int>(it->second);
    
    it = source.find("sell_base");
    if (it != source.end()) config.sell_base = it->second;
    
    it = source.find("sell_limit");
    if (it != source.end()) config.sell_limit = it->second;
    
    it = source.find("sahm_threshold");
    if (it != source.end()) config.sahm_threshold = it->second;
    
    return config;
}

std::size_t Config::hash() const {
    std::size_t h = 0;
    h = std::hash<int>{}(term) ^ (h << 1);
    h = std::hash<double>{}(margin) ^ (h << 1);
    h = std::hash<int>{}(bullish_rsi) ^ (h << 1);
    h = std::hash<double>{}(burst_urate) ^ (h << 1);
    h = std::hash<double>{}(burst_scale) ^ (h << 1);
    h = std::hash<int>{}(burst_vol) ^ (h << 1);
    h = std::hash<double>{}(sell_base) ^ (h << 1);
    h = std::hash<double>{}(sell_limit) ^ (h << 1);
    h = std::hash<double>{}(sahm_threshold) ^ (h << 1);
    return h;
}

std::string Config::to_string() const {
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(2);
    
    oss << "term: " << term << ", ";
    oss << "margin: " << margin << ", ";
    oss << "bullish_rsi: " << bullish_rsi << ", ";
    oss << "burst_urate: " << burst_urate << ", ";
    oss << "burst_scale: " << burst_scale << ", ";
    oss << "burst_vol: " << burst_vol << ", ";
    oss << "sell_base: " << sell_base << ", ";
    oss << "sell_limit: " << sell_limit << ", ";
    oss << "sahm_threshold: " << sahm_threshold;
    
    return oss.str();
}

bool Config::operator==(const Config& other) const {
    return term == other.term &&
           margin == other.margin &&
           bullish_rsi == other.bullish_rsi &&
           burst_urate == other.burst_urate &&
           burst_scale == other.burst_scale &&
           burst_vol == other.burst_vol &&
           sell_base == other.sell_base &&
           sell_limit == other.sell_limit &&
           sahm_threshold == other.sahm_threshold;
}