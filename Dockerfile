FROM debian:bookworm-slim

RUN apt update && apt install -y \
    cmake \
    build-essential \
    pkg-config \
    libprotobuf-dev \
    protobuf-compiler \
    libgrpc++-dev \
    libgrpc-dev \
    protobuf-compiler-grpc \
    nlohmann-json3-dev \
    libabsl-dev \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /mumeparrot-backtest

COPY . .
RUN rm -rf charts

RUN mkdir -p build && \
    cd build && \
    cmake .. && \
    make server

VOLUME ["/mumeparrot-backtest/charts"]

EXPOSE 50051

CMD ["./build/server"]
