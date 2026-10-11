# Botmax v1 — findings (Yahoo 5m, 2026-08-02 .. 2026-10-09)

Data: ~60 days of 5m NQ=F and ES=F (`tools/yahoo_download.py`). IS = first 65% (to 2026-09-16), OOS = rest.
Engine: `research/engine_v1.py` (TradingView fill model: next-bar fills, 1 tick slippage, limit 1 tick through,
$2.25/side). Grid: `research/search_v1.py`, 5,760 configs (ORB x 3 range ends x 3 stops x 2 entries x 4 R,
sweep x 3 windows x 4 level sets x 3 fibs x 4 R x 2 swing sizes, each x 16 filter combos).

## Result: no edge found

| | NQ | ES |
|---|---|---|
| configs profitable in-sample | 4.9% | 7.7% |
| configs profitable out-of-sample | 6.0% | 9.1% |
| configs profitable IS on **both** markets with >= 8 trades | **0** | |

- Best NQ in-sample config with >= 15 trades: ORB 09:30-09:45, stop at breakout-bar extreme, market entry,
  2R, no filters -> PF 1.06 IS (37 trades), **0.60 OOS**, 0.64 on ES. That is noise, not an edge.
- Sweep -> BOS -> fib setup barely trades (median 0 trades per config): the combined conditions plus an unfilled
  fib limit kill almost every signal in 60 days.
- Raw ORB follow-through (first 5m close outside 09:30-09:45, held to 16:00): NQ +13 pts/trade, ES +3.8 pts,
  47-48 days, win rate 45-54%. Price re-enters the range on 94-98% of days, so range-opposite stops get run.
  t-stat well below 1: indistinguishable from zero.
- Filters: the hourly colour run (Tom's bias) and 1h regime reduce losses mostly by cutting trade count;
  the VWAP filter is redundant for ORB (a close above the range is almost always above RTH VWAP).

## What this does and does not say

60 days is one regime and ~40 trading days in-sample; it cannot prove that these ideas never work, only that
nothing in the alttrading.ai library shows an edge big enough to see here. Next steps, in order:
1. Multi-year 5m history (`tools/ibkr_download.py`, or TradingView Deep Backtesting of `pine/botmax_v1.pine`
   via `tools/bt.mjs --grid`), then rerun `search_v1.py` on it with a fixed, untouched OOS year.
2. Only promote a config that is profitable IS on NQ **and** ES, sits on a parameter plateau, and has 200+ trades.
