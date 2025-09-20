#include "const.h"
#include "env.h"
#include <chrono>
#include <sstream>

// These globals are defined in env.cpp

bool is_sold(Status status) {
    return status == Status::Sold;
}

bool is_exhausted(Status status) {
    return status == Status::Exhausted;
}

State State::init(double seed_val, int max_cycle_val) {
    State state;
    state.date = "";
    state.elapsed = 0;
    state.principal = seed_val;
    state.price = 0;
    state.close_price = 0;
    state.max_cycle = max_cycle_val;
    state.seed = seed_val;
    state.invested_seed = 0;
    state.remaining_seed = seed_val;
    state.stock_qty = 0;
    state.commission = 0;
    state.status = Status::Buying;
    state.cycle = 0;
    state.balance = seed_val;
    state.boxx_seed = 0;
    state.boxx_eval = 0;
    state.avg_price = 0;
    state.stock_eval = 0;
    state.ror = 0;
    state.base_ror = 0;
    return state;
}

State State::from(const State& s, const StockRow& c) {
    State new_s = s;
    new_s.date = c.date;
    new_s.elapsed += 1;
    new_s.price = c.price;
    new_s.close_price = c.close_price;
    return new_s;
}

bool State::cycle_left() const {
    return cycle < max_cycle;
}

bool State::cycle_done() const {
    return cycle == 0;
}

void State::sell(int qty, double sell_price, bool sold) {
    bool all_cycle_used = !sold && cycle == max_cycle;
    if (all_cycle_used) {
        // assert qty == stock_qty
    }

    double commission_cost = qty * sell_price * COMMISSION_RATE;

    invested_seed -= qty * avg_price;
    remaining_seed += qty * sell_price - commission_cost;
    if (sold) seed = remaining_seed;
    stock_qty -= qty;
    commission += commission_cost;

    balance += qty * sell_price - commission_cost;
    if (BOXX && balance > 2 * BOXX_UNIT * seed) {
        double boxx_buy = balance - 2 * BOXX_UNIT * seed;
        double boxx_commission = boxx_buy * COMMISSION_RATE;

        balance -= boxx_buy;
        boxx_seed += boxx_buy;
        boxx_eval += boxx_buy - boxx_commission;
    }

    status = sold ? Status::Sold : Status::Exhausted;
    cycle = (sold || all_cycle_used) ? 0 : cycle + 1;
}

void State::buy(int qty, double buy_price) {
    double commission_cost = qty * buy_price * COMMISSION_RATE;

    invested_seed += qty * buy_price;
    remaining_seed -= qty * buy_price + commission_cost;
    commission += commission_cost;

    balance -= qty * buy_price + commission_cost;
    if (BOXX && balance < BOXX_UNIT * seed && boxx_seed >= BOXX_UNIT * seed) {
        double boxx_sell = BOXX_UNIT * seed;
        double boxx_commission = boxx_sell * COMMISSION_RATE;

        balance += boxx_sell;
        boxx_seed -= boxx_sell;
        boxx_eval -= boxx_sell + boxx_commission;
    }

    stock_qty += qty;
    status = Status::Buying;
}

void State::complete() {
    avg_price = (stock_qty > 0) ? invested_seed / stock_qty : 0;
    stock_eval = (stock_qty > 0) ? stock_qty * close_price : 0;

    if (boxx_eval > 0) {
        boxx_eval *= 1 + (BOXX_IR / MARKET_DAYS_PER_YEAR);
    }
    double boxx_profit = boxx_eval - boxx_seed;

    ror = (remaining_seed + stock_eval + boxx_profit) / principal - 1;
    base_ror = 0;
}

std::string State::to_string() const {
    if (date.empty()) return "";

    double price_pct = (avg_price > 0) ? (close_price - avg_price) / avg_price : 0;

    std::string result;
    std::ostringstream oss;

    // First section: date, cycle, seed info (52 characters, left-aligned)
    oss << std::fixed << std::setfill('0');
    oss << "[" << date << " (" << std::setw(2) << elapsed << ")] [" << cycle << "] ";
    oss << std::setfill(' ') << std::setprecision(0);
    oss << "seed=" << std::setw(6) << std::right << seed 
        << "(" << invested_seed << "+" << remaining_seed << ") ";
    
    std::string section1 = oss.str();
    if (section1.length() < 52) {
        result = section1 + std::string(52 - section1.length(), ' ');
    } else {
        result = section1.substr(0, 52);
    }

    // BOXX section (26 characters, left-aligned)
    if (BOXX) {
        oss.str("");
        oss << std::setprecision(0);
        oss << "boxx=" << balance << "+" << boxx_seed << "(" << (boxx_eval - boxx_seed) << ")";
        std::string boxx_section = oss.str();
        if (boxx_section.length() < 26) {
            result += boxx_section + std::string(26 - boxx_section.length(), ' ');
        } else {
            result += boxx_section.substr(0, 26);
        }
    }

    // Eval section (32 characters, left-aligned)
    oss.str("");
    oss << std::setprecision(2);
    oss << "eval=" << (stock_qty * close_price) << "(" << stock_qty << "*" << close_price << ") ";
    std::string eval_section = oss.str();
    if (eval_section.length() < 32) {
        result += eval_section + std::string(32 - eval_section.length(), ' ');
    } else {
        result += eval_section.substr(0, 32);
    }

    // Price section (26 characters, left-aligned)
    oss.str("");
    oss << std::setprecision(1);
    oss << "price=" << (price_pct * 100) << "%(" << close_price << "/" << avg_price << ") ";
    std::string price_section = oss.str();
    if (price_section.length() < 26) {
        result += price_section + std::string(26 - price_section.length(), ' ');
    } else {
        result += price_section.substr(0, 26);
    }

    // ROR section (25 characters, left-aligned)
    oss.str("");
    oss << std::setprecision(1);
    oss << "ror=" << (ror * 100) << "% [";
    
    switch(status) {
        case Status::Buying: oss << "Buying"; break;
        case Status::Sold: oss << "Sold"; break;
        case Status::Exhausted: oss << "Exhausted"; break;
    }
    oss << "]";
    
    std::string ror_section = oss.str();
    if (ror_section.length() < 25) {
        result += ror_section + std::string(25 - ror_section.length(), ' ');
    } else {
        result += ror_section.substr(0, 25);
    }

    return result;
}

int Result::days() const {
    std::tm start_tm = {};
    std::tm end_tm = {};
    
    std::istringstream start_ss(start);
    std::istringstream end_ss(end);
    
    start_ss >> std::get_time(&start_tm, "%Y-%m-%d");
    end_ss >> std::get_time(&end_tm, "%Y-%m-%d");
    
    auto start_time = std::mktime(&start_tm);
    auto end_time = std::mktime(&end_tm);
    
    return static_cast<int>((end_time - start_time) / (24 * 60 * 60));
}