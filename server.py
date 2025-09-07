import grpc
import logging

from typing import List, Dict
from concurrent import futures
from dataclasses import fields

import backtest_pb2
import backtest_pb2_grpc

from src.const import StockRow, Status, State
from src.env import TICKERS, BEST_CONFIGS
from src.configs import Config
from src.data import read_chart, compute_rsi, compute_volatility, compute_urates
from src.full import full_backtest


class MumeBacktestServer(backtest_pb2_grpc.MumeBacktestServerServicer):

    CHARTS: Dict[str, List[StockRow]] = {}
    RSIS: Dict[str, Dict[str, float]] = {}
    VOLATILITIS: Dict[str, Dict[str, float]] = {}
    URATES: Dict[str, Dict[str, float]] = {}

    @classmethod
    def initialize(cls):
        for ticker in TICKERS.keys():
            chart = read_chart(ticker, "", "")

            cls.CHARTS[ticker] = chart
            cls.RSIS[ticker] = compute_rsi(chart, 5)
            cls.VOLATILITIS[ticker] = compute_volatility(chart, 5)
            cls.URATES[ticker] = compute_urates(chart, 50, 40)

    def get_chart(self, ticker: str, start: str, end: str) -> List[StockRow]:
        chart = self.CHARTS[ticker]

        sidx = [int(c.date == start) for c in chart].index(1) if start else 0
        eidx = (
            [int(c.date == end) for c in chart].index(1) if end else len(chart)
        )

        return chart[sidx : eidx + 1]

    def FullBacktest(self, request, context):

        def state_to_pb2(s: State) -> backtest_pb2.State:
            kwargs = {}

            for field in fields(s):
                val = getattr(s, field.name, field.default)
                kwargs[field.name] = (
                    getattr(backtest_pb2.Status, val.name.upper())
                    if isinstance(val, Status)
                    else val
                )

            return backtest_pb2.State(**kwargs)

        ticker = request.ticker
        if not ticker in TICKERS:
            return backtest_pb2.HistoryWithErr(
                error=f"{request.ticker} not supported"
            )

        try:
            chart = self.get_chart(ticker, request.start, request.end)
        except ValueError:
            return backtest_pb2.HistoryWithErr(
                error=f"start='{request.start}', end='{request.end}' not supported"
            )

        config = (
            Config._from(request.config)
            if request.HasField("config")
            else BEST_CONFIGS[request.ticker]
        )

        try:
            # Generate history
            history = full_backtest(
                config,
                chart,
                self.URATES[ticker],
                self.RSIS[ticker],
                self.VOLATILITIS[ticker],
            )
            history = [state_to_pb2(s) for s in history]

            return backtest_pb2.HistoryWithErr(history=history)

        except Exception as e:
            return backtest_pb2.HistoryWithErr(error=f"Server error: {str(e)}")


def serve():
    """Start the gRPC server"""
    MumeBacktestServer.initialize()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    backtest_pb2_grpc.add_MumeBacktestServerServicer_to_server(
        MumeBacktestServer(), server
    )

    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)

    logging.basicConfig(level=logging.INFO)
    logging.info(f"Starting gRPC server on {listen_addr}")

    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
