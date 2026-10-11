# Botmax roadmap — how good can this get, and how we get there

## 1. What "maximum edge" realistically means

There is no knowable maximum, but there are hard reference points for what a retail system trading NQ/ES on
5-minute bars through TradingView can reach. "Best" is measured **net of costs, out of sample**, by Sharpe ratio
(return per unit of risk), not by backtest profit.

| level | net Sharpe (annual, out of sample) | what it looks like | who gets there |
|---|---|---|---|
| noise | < 0.3 | indistinguishable from luck within a few years | most published retail strategies after costs |
| real single edge | 0.5 - 1.0 | profitable most years, drawdowns of 6-18 months of profit | a sound, documented effect, traded simply |
| strong single edge | 1.0 - 1.5 | the best published intraday index effects (e.g. Zarattini et al. noise-area momentum, Sharpe 1.33 net on SPY 2007-2024, authors' backtest) | rare; needs years of validation |
| portfolio of edges | 1.5 - 2.5 | 3-6 **uncorrelated** edges, volatility-targeted sizing | the realistic ceiling for this setup |
| professional / HFT | 3 - 10+ | market making, latency, rebates, order-book data | needs co-location and tick data, not reachable with 5m bars |

Two consequences:
- **A backtest Sharpe above ~3 on 5m bars is a red flag, not a win.** It almost always means look-ahead, bad fills,
  or overfitting. Round 2's fade (PF 2.3 on ES over 7 weeks) shrank to PF 1.2 on the next unseen 3.5 months.
- **The path to the ceiling is a portfolio, not a better single rule.** Combining N uncorrelated edges of Sharpe S
  gives roughly S x sqrt(N). Four 0.8-Sharpe edges ~ 1.6. One magic setup with Sharpe 3 does not exist here.

So the target is: **portfolio Sharpe 1.5+ out of sample, every component surviving a locked holdout, max drawdown
under ~1 year of expected profit.** Stretch: 2.0+.

## 2. What blocks us today

1. **Data.** 6 months of 5m bars (TradingView chart limit) gives ~100 trades: a t-stat of 1 is all you can see.
   Fixed now: `tools/tv_contracts.mjs` pulls every quarterly NQ/ES contract back to 2011 from TradingView (expired
   contracts are available on this plan), `tools/stitch_contracts.py` back-adjusts them: ~15 years, ~280k bars each.
2. **Multiple testing.** Every grid cell we try raises the bar. Fixed by `research/wf.py`: locked periods and a
   Deflated Sharpe Ratio that accounts for the number of configs tried.
3. **One edge at a time.** Nothing combines edges or sizes by volatility yet (stage 5 below).

## 3. The pipeline (each stage has a pass/fail gate)

| stage | what | gate to pass |
|---|---|---|
| 0 data | 15y stitched 5m NQ + ES (RTH) | parity: Python engine vs TradingView on the same months (done for the fade: PF 1.60 vs 1.66) |
| 1 discovery | 2011-2019, grids allowed | PF > 1.15 on **both** markets, >= 300 trades, >= 6/9 positive years, a parameter plateau (neighbours profitable) |
| 2 validation | 2020-2022, chosen configs only | PF > 1.1 on both, Deflated Sharpe > 0.9, 2x-cost PF > 1.0 |
| 3 holdout | 2023-2026, touched once | PF > 1.05 on both; failure = idea retired, not retuned |
| 4 TradingView | the Pine version on the live chart | trade-for-trade parity with Python on the last 6 months |
| 5 portfolio | combine survivors, volatility-target each (same $ risk per day) | portfolio Sharpe > 1.5 on 2020-2026, correlation between components < 0.3 |
| 6 forward | paper trading via TradingView alerts, 3 months | live results inside the backtest's 90% band |
| 7 live | 1 micro contract (MNQ/MES), scale only with live evidence | |

## 4. Candidate edges (documented effects first, our own ideas second)

| # | idea | type | status |
|---|---|---|---|
| A | ORB reclaim fade (failed breakout) | mean reversion | **dead** on 2011-2019 (NQ PF 0.94, ES 0.70) |
| A2 | A + 1h regime filter | filtered MR | **dead** (NQ <= 1.11, ES <= 0.87) |
| B | noise-area momentum (Zarattini, Aziz & Barbon 2024) | trend | **VALIDATED on NQ** (holdout PF 1.27, Sharpe 1.11; 16y vol-targeted Sharpe 0.96); fails on ES |
| C | last-half-hour momentum (Gao, Han, Li & Zhou 2018, JFE) | trend, 1 trade/day | **dead** (PF 0.66-0.86) |
| D | overnight gap fade / continuation by gap size vs ATR | MR / trend | **dead** (PF <= 1.10) |
| E | calendar: turn-of-month, pre-holiday, FOMC days | seasonality | to build, as filters |
| F | regime switch: pick A or B by trailing realised vol / trend strength | meta | after A and B are validated |
| G | VIX / VIX term-structure regime as a filter (CBOE data in TradingView) | filter | to build |

A (mean reversion) and B (momentum) are naturally negatively correlated: Apr-Oct 2026 showed exactly that
(fade won, momentum lost on ES). That pairing is the most promising portfolio core.

## 5a. Status (Round 7, NQ / ES only)

Searched further on NQ/ES only: vol-regime filter, ES confirmation, parameter ensemble, overnight hold, turn of the
month, NQ-ES spread. None beats or diversifies the base rule out of sample. Ceiling with NQ/ES on 5m bars:
**Sharpe ~1.0 (1-tick fills) to ~1.2 (perfect fills)**, one edge. Next gains: execution quality, then other markets.

## 5. Status (Round 6)

Stages 0-3 done for A-D. One survivor: **B on NQ**. Current level: real single edge, Sharpe ~1.
Next, in order: (1) B on non-equity futures (CL, GC, ZN, 6E; session windows per market) through the same gates;
(2) E/G as filters on B, tested on discovery only; (3) portfolio of survivors; (4) forward test of
`pine/botmax_na.pine` on NQ with TradingView alerts, MNQ size.

## 6. Original order of work

1. Finish the 15y download, stitch, sanity-check against TradingView (current).
2. Run A, A2, B through stages 1-3 on both markets.
3. Build C, D, E in `engine_v1.py`, same gates.
4. Portfolio of survivors with volatility targeting; report combined Sharpe and drawdown.
5. Port the portfolio to one Pine strategy (or one per component) and forward-test with alerts.
