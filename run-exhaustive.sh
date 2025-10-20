#!/usr/bin/bash

ticker_json=${tickers:-tickers.json}
date_str=$(date +"%Y-%m-%d")
results=results-${date_str}

periods="1990,2000-02 2000-03,2008-12 2009-01,2020-12 2021-01,2025-10"

mkdir -p ${results}
for ticker in $(jq -r 'keys[]' ${ticker_json}); 
do
    for period in ${periods}
    do
        IFS=',' read -r start end <<< "${period}"
        echo "[${ticker}] Exhaustive from ${start} to ${end}..."
        START=${start} END=${end} ./exhaustive.py -t ${ticker} --fixed term:40,sahm_threshold:1.0 > ${results}/${ticker}-${start},${end}.dat &
    done
done

wait
