#include <grpc++/grpc++.h>
#include "build/generated/backtest.grpc.pb.h"
#include "build/generated/backtest.pb.h"
#include "src/env.h"
#include "src/data.h"
#include "src/full.h"
#include <iostream>
#include <memory>

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
// Don't use "using grpc::Status" to avoid conflict with our Status enum

class MumeBacktestServerImpl final : public backtest::MumeBacktestServer::Service {
private:
    std::unordered_map<std::string, std::vector<StockRow>> CHARTS;
    std::unordered_map<std::string, std::vector<StockRow>> BASE_CHARTS;
    std::unordered_map<std::string, std::unordered_map<std::string, double>> RSIS;
    std::unordered_map<std::string, std::unordered_map<std::string, double>> VOLATILITIES;
    std::unordered_map<std::string, std::unordered_map<std::string, double>> URATES;

public:
    void Initialize() {
        for (const auto& [ticker, base_ticker] : TICKERS) {
            auto chart = read_chart(ticker, "", "");
            auto base_chart = read_base_chart(base_ticker, "", "");

            CHARTS[ticker] = chart;
            BASE_CHARTS[ticker] = base_chart;
            RSIS[ticker] = compute_rsi(chart, 5);
            VOLATILITIES[ticker] = compute_volatility(chart, 5);
            URATES[ticker] = compute_urates(chart, 50, 40);
        }
    }

    std::vector<StockRow> get_chart(const std::string& ticker, const std::string& start, const std::string& end) {
        auto chart = this->CHARTS[ticker];

        size_t sidx = 0;
        if (!start.empty()) {
            for (size_t i = 0; i < chart.size(); ++i) {
                if (chart[i].date.substr(0, start.length()) == start) {
                    sidx = i;
                    break;
                }
            }
        }

        size_t eidx = chart.size();
        if (!end.empty()) {
            for (int i = static_cast<int>(chart.size()) - 1; i >= 0; --i) {
                if (chart[i].date.substr(0, end.length()) == end) {
                    eidx = i + 1;
                    break;
                }
            }
        }

        return std::vector<StockRow>(chart.begin() + sidx, chart.begin() + eidx);
    }

    std::vector<StockRow> get_base_chart(const std::string& ticker, const std::string& start, const std::string& end) {
        auto chart = this->BASE_CHARTS[ticker];

        size_t sidx = 0;
        if (!start.empty()) {
            for (size_t i = 0; i < chart.size(); ++i) {
                if (chart[i].date.substr(0, start.length()) == start) {
                    sidx = i;
                    break;
                }
            }
        }

        size_t eidx = chart.size();
        if (!end.empty()) {
            for (int i = static_cast<int>(chart.size()) - 1; i >= 0; --i) {
                if (chart[i].date.substr(0, end.length()) == end) {
                    eidx = i + 1;
                    break;
                }
            }
        }

        return std::vector<StockRow>(chart.begin() + sidx, chart.begin() + eidx);
    }

    grpc::Status FullBacktest(ServerContext* context, const backtest::FullBacktestArg* request,
                              backtest::HistoryWithErr* response) override {
        
        auto state_to_pb2 = [](const State& s) -> backtest::State {
            backtest::State pb_state;
            pb_state.set_date(s.date);
            pb_state.set_elapsed(s.elapsed);
            pb_state.set_principal(s.principal);
            pb_state.set_price(s.price);
            pb_state.set_close_price(s.close_price);
            pb_state.set_max_cycle(s.max_cycle);
            pb_state.set_seed(s.seed);
            pb_state.set_invested_seed(s.invested_seed);
            pb_state.set_remaining_seed(s.remaining_seed);
            pb_state.set_stock_qty(s.stock_qty);
            pb_state.set_commission(s.commission);
            
            switch(s.status) {
                case Status::Buying:
                    pb_state.set_status(backtest::Status::BUYING);
                    break;
                case Status::Sold:
                    pb_state.set_status(backtest::Status::SOLD);
                    break;
                case Status::Exhausted:
                    pb_state.set_status(backtest::Status::EXHAUSTED);
                    break;
            }
            
            pb_state.set_cycle(s.cycle);
            pb_state.set_balance(s.balance);
            pb_state.set_boxx_seed(s.boxx_seed);
            pb_state.set_boxx_eval(s.boxx_eval);
            pb_state.set_avg_price(s.avg_price);
            pb_state.set_stock_eval(s.stock_eval);
            pb_state.set_ror(s.ror);
            pb_state.set_base_ror(s.base_ror);
            
            return pb_state;
        };

        std::string ticker = request->ticker();
        if (TICKERS.find(ticker) == TICKERS.end()) {
            response->set_error(ticker + " not supported");
            return grpc::Status::OK;
        }

        std::vector<StockRow> chart;
        std::vector<StockRow> base_chart;
        
        try {
            chart = get_chart(ticker, request->start(), request->end());
            base_chart = get_base_chart(ticker, request->start(), request->end());
        } catch (const std::exception&) {
            response->set_error("start='" + request->start() + "', end='" + request->end() + "' not supported");
            return grpc::Status::OK;
        }

        Config config;
        if (request->has_config()) {
            // Convert protobuf config to C++ config
            const auto& pb_config = request->config();
            config.term = pb_config.term();
            config.margin = pb_config.margin();
            config.bullish_rsi = pb_config.bullish_rsi();
            config.burst_urate = pb_config.burst_urate();
            config.burst_scale = pb_config.burst_scale();
            config.burst_vol = pb_config.burst_vol();
            config.sell_base = pb_config.sell_base();
            config.sell_limit = pb_config.sell_limit();
            config.sahm_threshold = pb_config.sahm_threshold();
        } else {
            config = BEST_CONFIGS[ticker];
        }

        try {
            auto history = full_backtest(
                config,
                chart,
                this->URATES[ticker],
                this->RSIS[ticker],
                this->VOLATILITIES[ticker],
                nullptr,
                base_chart
            );

            auto* pb_history = response->mutable_history();
            for (const auto& state : history) {
                *pb_history->Add() = state_to_pb2(state);
            }
        } catch (const std::exception& e) {
            response->set_error("Server error: " + std::string(e.what()));
        }

        return grpc::Status::OK;
    }
};

void RunServer() {
    std::string server_address("0.0.0.0:50051");
    MumeBacktestServerImpl service;

    try {
        init_env();
        service.Initialize();
    } catch (const std::exception& e) {
        std::cerr << "Failed to initialize server: " << e.what() << std::endl;
        return;
    }

    ServerBuilder builder;
    builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    builder.RegisterService(&service);

    std::unique_ptr<Server> server(builder.BuildAndStart());
    std::cout << "Server listening on " << server_address << std::endl;

    server->Wait();
}

int main(int argc, char** argv) {
    RunServer();
    return 0;
}