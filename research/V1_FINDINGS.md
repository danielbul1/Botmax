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
---

# Round 5 — sources beyond alttrading.ai, and two TradingView tests (same 6-month RTH window)

**What was searched.** alttrading.ai/pinescript lists 10 scripts (ATX Price Action, ATX ORB Sniper, Mike's ORB Signal
Pro, Tom's Reversal, Regime Detection, Technical Analysis, Asia Fibonacci, and Lab-only B1 / P1 / S1). Only names and
one-line blurbs are public; code needs a (free) sign-in, and B1/P1/S1 rules and results are Lab-only ("Coming soon").
morluto/rea (REA) is a reverse-engineering MCP for binaries, apps and websites; it was **not** used to pull code from
behind alttrading's login or paywall. The free scripts can be read legitimately by signing in.
Public, citable work on intraday index edges:
- Zarattini, Aziz & Barbon (2024), "Beat the Market: An Effective Intraday Momentum Strategy for SPY" (SFI WP 24-97,
  SSRN 4824172): noise-area breakout, VWAP/band trailing stop, 2007-2024, Sharpe 1.33 net (authors' backtest).
- Gao, Han, Li & Zhou (2018, JFE), "Market intraday momentum": first half-hour return predicts the last half-hour.
- Zarattini & Aziz (2023), 5m ORB on QQQ: 24% hit rate, +0.13R/trade; an independent rerun on index CFDs found it
  zero after costs.
- No rigorous public study of the failed-breakout (reclaim) fade was found; vendor claims (60-80% breakout failure
  rates) are unsourced.

## 5a. Fade + filters (6 bars, opposite side; `research/round4_tv_grid.jsonl` baseline)

| filters | ES n / PF / net | NQ n / PF / net |
|---|---|---|
| none | 97 / 1.46 / +$11.9k | 97 / 1.22 / +$15.6k |
| 1h regime | 36 / **1.84** / +$7.1k | 38 / **1.58** / +$14.4k |
| hourly colour run | 24 / 1.51 / +$3.4k | 30 / 1.27 / +$5.8k |
| regime + colour run | 10 / 2.52 / +$3.1k | 16 / 2.02 / +$8.8k |
| VWAP-slope playbook | 57 / 1.15 / +$2.4k | 54 / 1.25 / +$11.0k |

The 1h regime filter improves PF on both markets and halves drawdown (ES $4.2k -> $2.1k, NQ $15.2k -> $6.7k) while
keeping most of NQ's profit. ~37 trades per market is too few to trust; worth carrying into the multi-year test as the
first candidate filter. The VWAP-slope switch (Alt's "VWAP Isn't a Line") hurts the fade.

## 5b. Noise-area momentum (`pine/botmax_na.pine`, paper defaults: 14 sessions, k = 1, every 30 min from 10:00)

| | k = 0.75 (15/30/60 min) | k = 1 (15/30/60 min) | k = 1.5 (15/30/60 min) |
|---|---|---|---|
| NQ PF | 0.94 / 1.00 / 0.98 | **1.34 / 1.33 / 1.23** | 1.04 / 0.97 / 1.29 |
| ES PF | 0.70 / 0.73 / 0.65 | 0.68 / 0.75 / 0.75 | 0.78 / 0.94 / 0.67 |

Paper defaults on NQ: 85 trades, PF 1.33, +$26.4k, max DD $20.0k. But ES loses in all 9 cells and NQ only works at
k = 1 with losers on both sides: no plateau. Raw rows: `research/round5_na_grid.jsonl`.

## Conclusion

Apr-Oct 2026 was a mean-reversion regime for index futures: the reclaim fade works on both markets, momentum
breakouts don't (ES) or only by luck of one parameter (NQ). That fits Round 3's warning in reverse: the fade's edge
is probably regime-dependent too. The two ideas are natural complements, so the next real step is still multi-year 5m
data (IBKR, or one month of TradingView Premium Deep Backtesting) to test (1) fade, (2) fade + 1h regime, (3) noise-area
momentum, and (4) a regime switch between them, with a held-out final year.
---

# Round 6 — 15 years of real 5m futures data: the first validated edge

**Data.** Every quarterly NQ and ES contract since 2011 (128 contracts, expired ones included), pulled from
TradingView on the Essential plan (`tools/tv_contracts.mjs`), RTH 5m bars, rolled 8 days before expiry and
back-adjusted (`tools/stitch_contracts.py`): 321k bars per market, 2010-12 -> 2026-10-09, no gaps. Checked against
TradingView's own NQ1!: 95% of bars have identical ranges, the rest sit in roll windows (NQ1! rolls on another day).
Not committed (TradingView data is not redistributable); rebuild with the two tools.

**Method** (`research/wf.py`, `research/ROADMAP.md`): locked periods DISCOVERY 2011-2019 / VALIDATION 2020-2022 /
HOLDOUT 2023-2026, 45 configs on discovery only, then only the survivors forward; holdout opened once, with the
decision config declared beforehand. Costs: 1 tick slippage per fill + $2.25/side; stress test at 2x.

## Stage 1 — discovery 2011-2019 (45 configs; full tables `research/round6_disc_nq.csv`, `round6_disc_es.csv`)

| edge | NQ best / typical PF | ES best / typical PF | verdict |
|---|---|---|---|
| A ORB reclaim fade | 0.97 / 0.79-0.94 (2/9 years) | 0.73 / 0.57-0.70 (0/9 years) | **dead**: the 2026 result was a regime |
| A2 fade + 1h regime | 1.11 / 0.85-1.11 | 0.87 / 0.65-0.87 | dead |
| B noise-area momentum | **1.33 / 1.14-1.33** for k >= 1 (plateau) | 1.11 / 0.84-1.11 | NQ plateau, ES only at k = 1.5 |
| C last-half-hour momentum | 0.86 / 0.79-0.86 | 0.84 / 0.66-0.84 | dead (decayed since 2018 publication) |
| D overnight gap fade / go | 1.10 / 0.87-1.10 | 1.00 / 0.73-1.00 | dead |

No config cleared the strict "PF > 1.15 on both markets" gate. B was promoted as an NQ-led candidate (declared before
validation): k in {1.0, 1.5} x decision interval in {30, 60} min.

## Stage 2 — validation 2020-2022 (`round6_val.csv`)

| config | NQ PF / Sharpe | ES PF / Sharpe | PF at 2x costs NQ / ES |
|---|---|---|---|
| k1.0 e30 (paper defaults) | 1.28 / 1.30 | 1.20 / 0.96 | 1.24 / 1.11 |
| k1.0 e60 | 1.43 / 1.64 | 1.22 / 0.96 | 1.39 / 1.14 |
| k1.5 e30 | 1.33 / 1.11 | 1.16 / 0.62 | 1.29 / 1.07 |
| k1.5 e60 | 1.23 / 0.74 | 1.22 / 0.70 | 1.20 / 1.13 |

All 4 pass on both markets; every NQ year positive.

## Stage 3 — holdout 2023-2026, opened once (`round6_hold.csv`). Decision config: paper defaults k1.0 e30

| | trades | PF | Sharpe | per year | PF 2x costs |
|---|---|---|---|---|---|
| **NQ** | 845 | **1.27** | **1.11** | 2023 +38.9k, 2024 +36.2k, 2025 +37.7k, 2026 +22.4k | 1.24 |
| ES | 898 | 0.98 | -0.08 | +15.4k, +3.7k, +0.4k, -24.0k | 0.90 |

The other three configs: NQ PF 1.16-1.28 (all positive), ES PF 0.98-1.06.

## Full history, NQ, paper defaults (2011-01 .. 2026-10)

- 1 contract: 3,682 trades, PF 1.26, net +$283,766, max DD $41,642, 13/16 years positive
  (weak years: 2013 -1.1k, 2016 -2.5k, 2019 -0.9k: calm, grinding markets).
- Volatility-targeted ($1,000 daily-vol target, trailing 60 days, past data only): **Sharpe 0.96 over 15.8 years**
  (t ~ 3.8), ~$16k/year, max DD $20.4k.
- Adding ES (same rule) hurts: ES Sharpe 0.05, correlation 0.69 with NQ, combined Sharpe 0.55. ES is dropped.
- Python vs TradingView parity for this rule (`pine/botmax_na.pine`, Apr-Oct 2026): 90 vs 85 trades, PF 1.28 vs 1.33.

## Conclusion

**Botmax has its first edge that survives a strict, pre-registered test: noise-area intraday momentum on NQ,
Sharpe ~1 net over 16 years, positive in all three locked periods.** That is the "real single edge" tier in
`ROADMAP.md`. Everything from the alttrading.ai library (ORB, sweep, fade, filters) is dead on 15 years of data.
The road to the 1.5-2.5 portfolio tier is now diversification: the same rule on markets that are **not** US equity
indices (crude, gold, treasuries, FX futures: intraday momentum is documented across asset classes), each run through
the same three-stage gate, then combined with volatility targeting.
---

# Round 7 — pushing NQ / ES only: what else is there? (same locked periods, raw-price simulator)

Correction to Round 6: the noise-area bands are percentages, so `research/edges.py` now computes them on raw contract
prices (the stitched file stores the back-adjustment per bar in `adj`). Paper defaults on NQ become
DISC PF 1.21 / Sharpe 0.80, VAL 1.24 / 1.15, HOLD 1.26 / 1.06 (vs 1.21 / 1.28 / 1.27 before); full 2011-2026
vol-targeted Sharpe 0.96. Conclusions unchanged.

| idea (all searched on 2011-2019 only) | result | verdict |
|---|---|---|
| B + volatility-regime filter (skip calmest 25% / 50% of regimes) | DISC Sharpe 0.80 -> 0.99 / 1.00; VAL 1.03 / **1.35**; HOLD (decision q0.5, declared in advance) PF 1.24, Sharpe **0.68** vs base 1.06 | passes, but **worse than the base out of sample**: not adopted |
| B on NQ, entries confirmed by ES breaking its band too | DISC Sharpe 0.80 -> 0.59 | dead |
| B parameter ensemble (k 1/1.5 x 30/60 min), vol-targeted | pairwise corr 0.8; Sharpe DISC 0.65, VAL 1.22, HOLD 1.04, all 0.88 (base 0.96) | no gain |
| Overnight hold (16:00 close -> 09:30 open) | NQ DISC PF 1.14 / Sharpe 0.67; VAL PF 1.05, 2022 -$70k | dead (long beta; ES premium eaten by costs) |
| Turn of the month (long day -k .. +m) | NQ PF 1.06-1.48 depending on the window, not a plateau; earns less than the same days of buy-and-hold | dead |
| NQ-ES intraday spread, follow or fade, dollar-neutral | PF 0.44-0.83, 0-2/9 years | dead (two-leg costs > spread moves) |

Overnight vs intraday decomposition (gross, both markets, all three periods): the overnight session earns more per unit
of risk than the RTH session (NQ 2011-2019 overnight 11.2%/yr, Sharpe 1.12; intraday 5.1%/yr, 0.37). Real, but one
round trip per night costs ~3%/yr on NQ and ~7%/yr on ES, and the remainder is mostly market beta.

**Execution is the largest remaining lever** (NQ, paper defaults, 2011-2026, vol-targeted):

| slippage per fill | PF | Sharpe |
|---|---|---|
| 0 ticks | 1.28 | 1.22 |
| 1 tick (our default) | 1.24 | 0.96 |
| 2 ticks | 1.21 | 0.71 |

## Conclusion — the edge ceiling with NQ / ES on 5m bars

After 70+ configurations across 9 edge families on 16 years of both markets, **one** edge survives every gate:
noise-area intraday momentum on NQ. Its realistic ceiling is **Sharpe ~1.0-1.2 net**: 0.96 with a conservative 1-tick
fill, 1.22 with perfect fills, volatility-targeted. Nothing tried on NQ/ES alone adds an uncorrelated second
edge, so a portfolio above ~1.2 is not available from these two markets with this data.

What would move it further, in order of expected gain:
1. **Execution**: fills at or near the decision price (limit at the touch, or entering on the bar that crosses
   rather than the 30-minute grid) are worth up to +0.25 Sharpe. Measure live slippage on MNQ first.
2. **Other markets** (rejected for now): the same rule on non-equity futures is the standard way past ~1.2.
3. **Better data**: order-flow / tick data, or options positioning (dealer gamma, which the source paper reports as
   a strong conditioning variable). Not available in TradingView Essential.