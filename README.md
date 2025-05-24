# Backtest Tool for MumeParrot

MumeParrot ([android](https://play.google.com/store/apps/details?id=com.mumemume.mumeparrot&hl=en), [ios](https://testflight.apple.com/join/wBtRGB72)) trades the stocks on behalf of users.
Especially, MumeParrot strictly follows the stock trading strategy based on [Infinite Buying](https://blog.naver.com/mortley/222577958223) (For non-korean readers, please refer to [Background of MumeParrot]()).
However, following Infinite Buying as it is has a high risk of failure and some missing parts on handling such cases.

Thus, MumeParrot backtest seeks for more safe strategy with higher return rate. 
Based on Infinite Buying, it backtests the strategy with variable parameters on the historical chart of stocks.
Once a better strategy and parameters are found, it will be updated to MumeParrot to follow them in real world.
For more details, please refer to the [Background of MumeParrot]().

## Usage

### 1. Fetch Chart History

To run this backtest tool, you first have to fetch the chart data.
`fetch-charts.py` fetches the historical chart of stocks listed in `tickers.json` (by default) and saves them under `charts` directory.
Specifically, it reconstructs the chart of 3-times leverage stock (e.g., SOXL) based on the corresponding 1-times stock (e.g., SOXX) for missing period, to get longer history.

\* `fetch-charts.py` fails to fetch the data in some cases, please retry after removing already fetched stocks in `tickers.json` in such cases.

```
./fetch-charts.py --help
Usage: fetch-charts.py [OPTIONS]

Options:
  -i, --input TEXT  json file containing key, value map of 3-times ticker and
                    1-times base ticker (default: tickers.json)
  -g, --graph       Draw graph for each ticker
  --help            Show this message and exit.
```

### 2. Run Backtest

After fetching the chart history, `backtest.py` runs backtests on the charts with variable `config` parameters.
It has two modes: sliding window mode (`t`) and full simulation mode (`f`).

* **Sliding window mode** is to statistically capture the performance of strategy (i.e., whether it correctly captures the fluctuation of the stock and makes profit from it).
Especially, this mode is to correctly capture the effect of stock price fluctuation (which is the core backbone of Infinite Buying to make profit), but exclude any other external factors such as long-term price variation.
Please refer to [Background of MumeParrot]() for more details.

* **Full simulation mode** is to simulate the given strategy throughout the entire period of market (like the backtests normally done).
However, one cannot trust the results of this mode 100% as those results are quite sensitive to noise, and that's the reason why we need Sliding window mode.
For example, some statistical outliers like the stocks not sold due to only 0.1% low profit can make large variation, which disguises the people as if the strategy is wrong.

While `configs.json` contains the best configurations found by optimization (i.e., will be explained later), you can test various different configuration parameters as shown below.
Furthermore, if you want to apply totally different strategies, you can modify `src/sim.py`, which contains the core strategy implementation of MumeParrot.

```
./backtest.py
mode [default=p]: h
=== MumeParrot backtest ===
Usage: python3 backtest.py
 Modes:
  -h) print this help message
  -t) sliding window test
  -f) full simulation
 Tickers:
   all, UPRO, SPXL, CURE, DFEN, FNGB,
   FAS, HIBL, LABU, MIDU, NAIL,
   PILL, RETL, SOXL, TECL, TNA,
   WANT, WEBL, TQQQ
 Config:
  term: number of days to split the seed and buy the stock
  margin: margin to sell the stock
  bullish_rsi: rsi threshold to buy the stock
  bullish_u50: rate of market days under 50 moving average to determine burst buy and
  burst_scale: scale of burst buy when the market fluctuates
  burst_vol: volatility threshold to determine burst buy
  sell_base: base sell rate when all seed is exhausted
  sahm_threshold: sahm threshold to exclude when sliding window test
(Environment variables)
 TICKER_FILE: path to ticker file (default: tickers.json)
 CONFIGS_FILE: path to best configs file (default: configs.json)
 START: start date in 'yyyy-mm-dd' format, either 'yyyy' or 'yyyy-mm' are allowed also (default: empty)
 END: end date in 'yyyy-mm-dd' format, either 'yyyy' or 'yyyy-mm' are allowed also (default: empty)
 CYCLE_DAYS: number of days to simulate per each cycle (default: 60)
 SEED: amount of seed (default: 1000000)
 MAX_CYCLES: maximum cycles (default: 2)
 FAIL_PENALTY: penalty for cycle failure when optimization (default: 2)
 FAIL_LIMIT: limit for cycle failure when optimization (default: 0.1)
 DEBUG: set to log history under 'logs/test (default: 0)
 VERBOSE: set to print history (default: 0)
 GRAPH: print graph when full simulation (default: 0)
```

### 3. Optimize Parameters

Once you find some parameters and strategies that can be meaningful to the stability and return rate of MumeParrot, you can find the best set of parameters by running `optimize.py`.
`optimize.py` finds the best set of parameters by optimizing the object which consists of fail rate and return rate (i.e., `score` returned by `test` function).
You can find an example of running `optimize.py` in `run-optimize.sh`.

```
./optimize.py --help
Usage: optimize.py [OPTIONS]

Options:
  -m, --mode [o|a]                Optimize or analyze
  -d, --directory TEXT            Directory to save results
  -t, --ticker [UPRO|SPXL|CURE|DFEN|FNGB|FAS|HIBL|LABU|MIDU|NAIL|PILL|RETL|SOXL|TECL|TNA|WANT|WEBL|TQQQ]
  -f, --fixed TEXT                Fixed config parameters
  --help                          Show this message and exit.
```

## Results

We show the sliding window test results with the best configurations below.
Numbers in last paranthesis (i.e., `(X%, Y%)`) marks the average return of rate per year (i.e., `X%`), and the rate of failing two consecutive cycles (i.e., `Y%`).

```
./backtest.py
mode [default=p]: t
ticker [default=all]:
config [default=best](type 'n' to manually set):
UPRO: term: 40, margin: 0.08, bullish_rsi: 60, bullish_u50: 0.70, burst_scale: 0.50, burst_vol: 25, sell_base: 0.40, sahm_threshold: 1.00 | 11.61 (12.5%, 3.6%)
SPXL: term: 40, margin: 0.08, bullish_rsi: 60, bullish_u50: 0.50, burst_scale: 0.50, burst_vol: 25, sell_base: 0.40, sahm_threshold: 1.00 | 11.45 (12.3%, 3.6%)
CURE: term: 40, margin: 0.06, bullish_rsi: 60, bullish_u50: 0.30, burst_scale: 2.00, burst_vol: 25, sell_base: 0.30, sahm_threshold: 1.00 | 8.85 (9.5%, 3.3%)
DFEN: term: 40, margin: 0.10, bullish_rsi: 60, bullish_u50: 0.60, burst_scale: 0.00, burst_vol: 45, sell_base: 0.30, sahm_threshold: 1.00 | 12.41 (14.4%, 6.8%)
FNGB: term: 40, margin: 0.08, bullish_rsi: 80, bullish_u50: 0.50, burst_scale: 1.00, burst_vol: 25, sell_base: 0.40, sahm_threshold: 1.00 | 18.21 (19.7%, 3.7%)
FAS: term: 40, margin: 0.10, bullish_rsi: 60, bullish_u50: 0.50, burst_scale: 0.50, burst_vol: 30, sell_base: 0.40, sahm_threshold: 1.00 | 9.60 (11.6%, 8.6%)
HIBL: term: 40, margin: 0.05, bullish_rsi: 65, bullish_u50: 0.50, burst_scale: 2.00, burst_vol: 25, sell_base: 0.40, sahm_threshold: 1.00 | 7.63 (8.0%, 2.3%)
LABU: term: 40, margin: 0.11, bullish_rsi: 65, bullish_u50: 0.60, burst_scale: 0.00, burst_vol: 40, sell_base: 0.00, sahm_threshold: 1.00 | 12.52 (14.5%, 7.0%)
MIDU: term: 40, margin: 0.05, bullish_rsi: 85, bullish_u50: 0.30, burst_scale: 2.00, burst_vol: 40, sell_base: 0.10, sahm_threshold: 1.00 | 10.16 (11.2%, 4.6%)
NAIL: term: 40, margin: 0.09, bullish_rsi: 85, bullish_u50: 0.40, burst_scale: 2.50, burst_vol: 30, sell_base: 0.10, sahm_threshold: 1.00 | 15.25 (17.4%, 6.3%)
PILL: term: 40, margin: 0.05, bullish_rsi: 60, bullish_u50: 0.70, burst_scale: 0.50, burst_vol: 30, sell_base: 0.40, sahm_threshold: 1.00 | 7.30 (7.8%, 3.0%)
RETL: term: 40, margin: 0.05, bullish_rsi: 70, bullish_u50: 0.70, burst_scale: 2.50, burst_vol: 25, sell_base: 0.00, sahm_threshold: 1.00 | 11.65 (12.5%, 3.3%)
SOXL: term: 40, margin: 0.09, bullish_rsi: 85, bullish_u50: 0.60, burst_scale: 1.00, burst_vol: 25, sell_base: 0.10, sahm_threshold: 1.00 | 15.35 (17.3%, 5.7%)
TECL: term: 40, margin: 0.07, bullish_rsi: 75, bullish_u50: 0.50, burst_scale: 2.50, burst_vol: 25, sell_base: 0.40, sahm_threshold: 1.00 | 12.43 (13.4%, 3.6%)
TNA: term: 40, margin: 0.05, bullish_rsi: 60, bullish_u50: 0.70, burst_scale: 2.50, burst_vol: 35, sell_base: 0.40, sahm_threshold: 1.00 | 11.08 (11.4%, 1.2%)
WANT: term: 40, margin: 0.06, bullish_rsi: 65, bullish_u50: 0.50, burst_scale: 2.50, burst_vol: 25, sell_base: 0.20, sahm_threshold: 1.00 | 12.13 (12.9%, 3.1%)
WEBL: term: 40, margin: 0.09, bullish_rsi: 90, bullish_u50: 0.70, burst_scale: 2.50, burst_vol: 40, sell_base: 0.00, sahm_threshold: 1.00 | 14.83 (17.5%, 7.7%)
TQQQ: term: 40, margin: 0.06, bullish_rsi: 95, bullish_u50: 0.60, burst_scale: 1.00, burst_vol: 25, sell_base: 0.00, sahm_threshold: 1.00 | 11.91 (13.3%, 5.1%)
```

Full simulation results are shown below.


