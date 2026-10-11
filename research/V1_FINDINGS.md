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

---

# Round 2 — modules from Alt's own published logic (`research/search_v2.py`, 2,208 configs)

Source: alttrading.ai's free Substack posts ("Breakouts Are Probability", "Turning the Open Into a Decision
Model", "Why Pivots Should Be Measured", "Reversals Without Gambling", "VWAP Isn't a Line") and the site.
Their stated pipeline: regime -> location -> acceptance -> entry with defined invalidation.

| module | rule | share of configs profitable (NQ IS / ES IS / NQ OOS / ES OOS) | median PF NQ OOS / ES OOS |
|---|---|---|---|
| B1 acceptance | ORB break, retest within x ATR that holds, optional ATR-expansion gate | 39% / 20% / low / low | 0.00 / 0.62 |
| **ORB reclaim fade** | ORB break closes back inside within N bars -> market back across, stop past the break extreme, target mid/opposite side | **59% / 76% / – / –** | **1.25 / 3.64** |
| P1 pivots | anchor (RTH open / prior close) +/- k x daily ATR, reject or accept | 13% / 12% | 0.96 / 0.52 |
| VWAP playbook | VWAP slope > x ATR = trend day (continuation only), else fades only | filter; small effect | |

**ORB reclaim fade** is the only thing so far that works as a plateau, not a lucky cell: 55 of the 71 configs that are
profitable in-sample on both NQ and ES are fades. Untuned default (09:30-09:45 range, reclaim within 6 bars,
target opposite side, trades until 13:00, no filters), full 60 days:

| | trades | win % | PF | net | max DD | IS PF | OOS PF | 2x costs PF |
|---|---|---|---|---|---|---|---|---|
| NQ (1 contract) | 34 | 50% | 1.66 | +$10,467 | $4,252 | 2.19 | 0.87 | 1.63 |
| ES (1 contract) | 38 | 63% | 2.32 | +$7,879 | $1,227 | 2.69 | 1.88 | 2.10 |

Every neighbour (target midpoint, 12-bar reclaim, 10:00 range end) stays profitable on the full sample on both
markets. Weak spots: NQ OOS is about breakeven (PF 0.87-1.31 depending on the neighbour), October is negative on
both, NQ profit came almost entirely from shorts. It matches the raw stat above (price re-enters the range on
94-98% of days) and Alt's own advice ("if price re-enters the range quickly, switch mindset").

Still ~35 trades per market: a t-stat around 1.5, so promising, **not proven**. It is in
`pine/botmax_v1.pine` as Setup = "ORB reclaim fade" for a multi-year Deep Backtest before anything else.

---

# Round 3 — longer check with 2.4 years of hourly bars (via tradingview-mcp's data source)

atilaahmettaner/tradingview-mcp runs locally (39 tools); its backtester only offers 9 fixed indicator strategies
on 1d/1h, so the fade can't run inside it. It did show Yahoo serves ~2 years of 1h futures bars, so
`data/{nq,es}_1h_yahoo.csv` (2024-05-19 .. 2026-10-09) were pulled and the fade rerun in `engine_v1.py` as a
coarse proxy: range = the 09:00-10:00 hourly bar (Yahoo hours start on :00), reclaim within 1-3 hourly bars,
flat at 16:00 (`orb_start` param added).

| | configs with PF > 1 | PF range | trades |
|---|---|---|---|
| NQ | 0 / 24 | 0.59 - 0.77 | 86 - 187 |
| ES | 10 / 24 | 0.87 - 1.18 | 77 - 202 |

NQ loses in every variant and in 8 of 11 quarters; ES is roughly breakeven. Not the same rules as the 5m fade
(coarser range and reclaim), but it is a clear warning that the 5m result may belong to the Aug-Oct 2026 regime.
The 5m fade still needs a true multi-year 5m test (TradingView Deep Backtest or IBKR data) before any use.

---

# Round 4 — TradingView (CME_MINI NQ1! / ES1!, 5m, RTH bars, 2026-04-13 .. 2026-10-09)

Run through tradingview-mcp (tradesdontlie) + `tools/bt.mjs` on TradingView Desktop 3.4.1. `pine/botmax_v1.pine`
needed three Pine v6 compile fixes first (enum field `range` is reserved -> `opp`; `int(math.sign())` cast; typed return
for `trackSession`). Setup = "ORB reclaim fade", range 09:30-09:45, "Breakout window" 0945-1300 (= Round 2's
"trades until 13:00"), stop buffer 4 ticks, max 2 trades/day, no filters, 1 contract, $2.25/side, 1 tick slippage.

**History:** Deep Backtesting needs a Premium plan (the account is Essential), so the test runs on the bars loaded on
the chart (~10k). With the session set to RTH only, that is 6 months (Apr 13 - Oct 9 2026) instead of 7 weeks with ETH.
The fade trades only inside RTH, so RTH bars don't change its signals.

## Grid (full 6 months)

| market | reclaim bars | target | trades | win % | PF | net | max DD |
|---|---|---|---|---|---|---|---|
| NQ | 3 | opposite | 84 | 44% | 1.11 | +$6,947 | $15,998 |
| NQ | 3 | mid | 81 | 65% | 1.28 | +$9,721 | $8,953 |
| NQ | **6** | **opposite** | 97 | 47% | 1.22 | +$15,624 | $15,188 |
| NQ | 6 | mid | 93 | 67% | 1.24 | +$10,322 | $13,378 |
| NQ | 12 | opposite | 110 | 46% | 1.20 | +$16,375 | $16,172 |
| NQ | 12 | mid | 106 | 67% | 1.28 | +$13,673 | $13,378 |
| ES | 3 | opposite | 82 | 52% | 1.39 | +$8,331 | $4,097 |
| ES | 3 | mid | 76 | 68% | 1.13 | +$1,621 | $2,738 |
| ES | **6** | **opposite** | 97 | 55% | 1.46 | +$11,864 | $4,195 |
| ES | 6 | mid | 91 | 70% | 1.17 | +$2,566 | $5,353 |
| ES | 12 | opposite | 113 | 56% | 1.51 | +$15,054 | $4,750 |
| ES | 12 | mid | 106 | 71% | 1.23 | +$4,036 | $6,317 |

All 12 cells are profitable: a plateau, not one lucky cell. ES prefers the opposite-side target; NQ is indifferent.
Raw rows: `research/round4_tv_grid.jsonl`.

## Default config (6 bars, opposite side) split by period

| | trades | win % | PF | net | t-stat |
|---|---|---|---|---|---|
| NQ Aug 2 - Oct 9 (Round 2 window) | 35 | 49% | 1.60 | +$9,843 | 1.21 |
| NQ Apr 13 - Aug 1 (**new, unseen**) | 62 | 47% | **1.10** | +$5,781 | 0.35 |
| ES Aug 2 - Oct 9 (Round 2 window) | 38 | 63% | 2.28 | +$7,642 | 2.31 |
| ES Apr 13 - Aug 1 (**new, unseen**) | 59 | 49% | **1.21** | +$4,222 | 0.65 |
| NQ full 6 months | 97 | 47% | 1.22 | +$15,624 | 0.85 |
| ES full 6 months | 97 | 55% | 1.46 | +$11,864 | 1.62 |

Monthly net, NQ: Apr -3.3k, May +1.6k, Jun +6.6k, Jul +0.9k, Aug +6.4k, Sep +7.3k, Oct -3.9k.
ES: Apr -0.1k, May +1.5k, Jun +3.4k, Jul -0.6k, Aug +2.4k, Sep +5.7k, Oct -0.4k.
NQ longs/shorts both positive this time (PF 1.18 / 1.26), so Round 2's "NQ profit came only from shorts" doesn't hold.

## Comparison with Round 2

**Parity is good.** On the overlapping window TradingView matches the Python engine almost trade-for-trade:
NQ 35 vs 34 trades, PF 1.60 vs 1.66, net $9,843 vs $10,467; ES 38 vs 38 trades, PF 2.28 vs 2.32, net $7,642 vs $7,879.
So `engine_v1.py` is a faithful twin of the Pine, and Round 2's numbers were not an engine artefact.

**On the 3.5 months Round 2 never saw, the edge shrinks a lot but stays positive:** PF 1.10 on NQ and 1.21 on ES,
t-stats 0.35 and 0.65. That is consistent with a small real edge **or** with zero; it is not consistent with the
PF 1.7-2.3 that the Aug-Oct window suggested. Round 3's hourly proxy (NQ negative over 2.4 years) still stands as the
warning: six months is still one market regime.

## Conclusion

The fade survives its first out-of-sample test on both markets and across all 6 grid cells, which nothing else in
v1/v2 did, but the out-of-sample edge is about a third of the in-sample one and statistically indistinguishable from
zero. ES (opposite-side target) is the stronger and steadier market (max DD ~$4-5k vs ~$15k on NQ). **Not tradeable
yet.** Next: multi-year 5m data (IBKR download, or one month of TradingView Premium for Deep Backtesting) to get
500+ trades and a yearly breakdown; promote only if PF stays > 1.15 on ES with a positive NQ.