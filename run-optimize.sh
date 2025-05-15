#!/usr/bin/bash

ticker_json=${tickers:-tickers.json}
date_str=$(date +"%Y-%m-%d")
max_cycles=${max_cycles:-2}
rsi_days=${rsi_days:-5}
results=results-${date_str}

mkdir -p ${results}
for ticker in $(jq -r 'keys[]' ${ticker_json}); 
do
    for i in {1..3}
    do
	echo "[${i}] Optimizing ${ticker}..."
	./optimize.py -t ${ticker} --fixed term:40,sahm_threshold:1.0 > ${results}/${ticker}-${i}.dat &
    done
done

wait
