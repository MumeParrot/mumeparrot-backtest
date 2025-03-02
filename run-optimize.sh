#!/usr/bin/bash

ticker_json=${tickers:-tickers.json}
date_str=$(date +"%Y-%m-%d")
max_cycles=${max_cycles:-2}
results=results-c${max_cycles}-${date_str}

mkdir -p ${results}
for ticker in $(jq -r 'keys[]' ${ticker_json}); do
	echo "Optimizing ${ticker}..."
	START=2023 MAX_CYCLES=${max_cycles} ./optimize.py -t ${ticker} --fixed bearish_rsi:0,min_bearish_rate:1.0,sahm_threshold:1.0 > ${results}/${ticker}.dat &
done

wait
