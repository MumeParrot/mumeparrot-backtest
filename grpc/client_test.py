#!/usr/bin/env python3
import grpc
import backtest_pb2
import backtest_pb2_grpc
from dataclasses import fields
from datetime import datetime, timedelta

from src.env import BEST_CONFIGS
from src.const import State


def create_test_config():
    """Create a test configuration for backtesting"""

    config = BEST_CONFIGS["SOXL"]
    config.margin = 0.1
    kwargs = {}
    for field in fields(config):
        kwargs[field.name] = getattr(config, field.name, field.default)
    return backtest_pb2.Config(**kwargs)


def test_full_backtest(ticker="SOXL", start_date="", end_date="", config=None):
    """Test the FullBacktest gRPC API"""

    # Create gRPC channel
    channel = grpc.insecure_channel("localhost:50051")
    stub = backtest_pb2_grpc.MumeBacktestServerStub(channel)

    try:
        # Create request
        request = backtest_pb2.FullBacktestArg(
            ticker=ticker, start=start_date, end=end_date
        )

        # Add config if provided
        if config:
            request.config.CopyFrom(config)

        print(
            f"Testing FullBacktest for {ticker} {("from " + start_date) if start_date else ""} {"to " + end_date if end_date else ""}"
        )
        print("-" * 60)

        # Make the gRPC call
        response = stub.FullBacktest(request)

        # Check for errors
        if response.error:
            print(f"Error: {response.error}")
            return None

        # Process successful response
        history = [State._from(s) for s in response.history]
        print(f"Received {len(history)} history entries")

        if history:
            print("\nFirst 5 entries:")
            for i, state in enumerate(history[:5]):
                print(f"[{i}] {state}")

            if len(history) > 5:
                print(f"  ... ({len(history) - 6} more entries)")

            print(f"[{len(history)}]: {history[-1]}")

        return response

    except grpc.RpcError as e:
        print(f"gRPC Error: {e.code()}: {e.details()}")
        return None
    finally:
        channel.close()


def main():
    """Main function to run various test scenarios"""
    print("=== Python gRPC Client for FullBacktest API ===\n")

    # Test 1: Basic test with default config
    print("Test 1: Basic test with default config")
    test_full_backtest()
    print()

    # Test 2: Test with custom config
    print("Test 2: Test with custom config")
    custom_config = create_test_config()
    test_full_backtest(config=custom_config)
    print()

    # Test 3: Test with different ticker (will likely fail if not supported)
    print("Test 3: Test with unsupported ticker")
    test_full_backtest(ticker="TSLA")
    print()

    # Test 4: Test with invalid date format
    print("Test 4: Test with invalid date format")
    test_full_backtest(start_date="invalid-date", end_date="2023-12-31")


if __name__ == "__main__":
    main()
