#pragma once

#include <string>
#include <vector>
#include <tuple>
#include <exception>
#include <cmath>
#include <sstream>
#include <iomanip>

class SeedExhausted : public std::exception {
public:
    const char* what() const noexcept override {
        return "Seed exhausted";
    }
};

enum class Status {
    Buying = 0,
    Sold = 1,
    Exhausted = 2
};

bool is_sold(Status status);
bool is_exhausted(Status status);

struct StockRow {
    std::string date;
    double price;
    double close_price;

    StockRow() = default;
    StockRow(const std::string& d, double p, double cp) 
        : date(d), price(p), close_price(cp) {}
};

struct State {
    std::string date;
    int elapsed;
    double principal;
    double price;
    double close_price;
    int max_cycle;

    double seed;
    double invested_seed;
    double remaining_seed;
    double stock_qty;
    double commission;

    Status status;
    int cycle;

    double balance;
    double boxx_seed;
    double boxx_eval;

    double avg_price;
    double stock_eval;
    double ror;
    double base_ror;

    static State init(double seed_val, int max_cycle_val);
    static State from(const State& s, const StockRow& c);
    
    bool cycle_left() const;
    bool cycle_done() const;
    void sell(int qty, double sell_price, bool sold = false);
    void buy(int qty, double buy_price);
    void complete();
    
    std::string to_string() const;

    State() : elapsed(0), principal(0), price(0), close_price(0), max_cycle(0),
              seed(0), invested_seed(0), remaining_seed(0), stock_qty(0), 
              commission(0), status(Status::Buying), cycle(0), balance(0),
              boxx_seed(0), boxx_eval(0), avg_price(0), stock_eval(0),
              ror(0), base_ror(0) {}
};

using History = std::vector<State>;

struct Result {
    std::string start;
    std::string end;
    bool sold;
    double ror;

    int days() const;
};

extern double COMMISSION_RATE;
extern int MARKET_DAYS_PER_YEAR;
extern bool BOXX;
extern double BOXX_UNIT;
extern double BOXX_IR;