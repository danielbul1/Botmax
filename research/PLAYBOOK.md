# Botmax Playbook — Building, Validating and Shipping a Pine v6 ICT Algo for NQ

Scope: the *how*. How to structure, code, test and validate an intraday NQ/MNQ strategy in Pine Script v6
that combines ICT concepts (structure, liquidity, FVG, OB, killzones, HTF bias).
Legend: **[DOC]** = stated in official TradingView docs (URL given). **[LIT]** = quant literature.
**[PRAC]** = common practitioner consensus (not official). **[VERIFY]** = uncertain, check before relying on it.

Key sources
- Repainting: https://www.tradingview.com/pine-script-docs/concepts/repainting/
- Other timeframes: https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/
- Strategies: https://www.tradingview.com/pine-script-docs/concepts/strategies/
- Execution model: https://www.tradingview.com/pine-script-docs/language/execution-model/
- Limitations: https://www.tradingview.com/pine-script-docs/writing/limitations/
- Objects/UDTs: https://www.tradingview.com/pine-script-docs/language/objects/
- Lines & boxes: https://www.tradingview.com/pine-script-docs/visuals/lines-and-boxes/
- Sessions: https://www.tradingview.com/pine-script-docs/concepts/sessions/
- v6 migration: https://www.tradingview.com/pine-script-docs/migration-guides/to-pine-version-6/
- Reference manual: https://www.tradingview.com/pine-script-reference/v6/
- Publishing rules: https://www.tradingview.com/support/solutions/43000590599-script-publishing-rules/
- Deflated Sharpe (Bailey & López de Prado 2014): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551
- Probability of Backtest Overfitting (Bailey, Borwein, López de Prado, Zhu): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253
- MNQ intraday falsification study (2026): https://arxiv.org/abs/2605.04004

---

## 0. The 10 non-negotiable rules

1. **Decide only on confirmed data.** Signals use closed-bar values (strategies calc on bar close by default; keep `calc_on_every_tick = false`). No `varip`, `timenow`, or `barstate.isnew` in signal logic. [DOC repainting]
2. **HTF data = `request.security(sym, tf, expr[1], lookahead = barmerge.lookahead_on)`.** The `[1]` and `lookahead_on` are interdependent; never use `lookahead_on` without `[1]`. [DOC]
3. **Pivots are known R bars late.** A swing at bar `t` is usable only from bar `t+R`. Never act, or draw as if actionable, before then. [DOC repainting: "plotting in the past"]
4. **Call every `ta.*` function on every bar in global scope.** v6 `and`/`or` are lazy, so `cond and ta.rsi(...) > 50` silently stops updating RSI. [DOC v6 migration]
5. **Killzones via `time(timeframe.period, "0830-1100", "America/New_York")`.** Always pass the IANA timezone; never rely on the chart/exchange timezone (CME = Chicago). [DOC sessions]
6. **Model costs honestly:** per-contract commission (per side), >=1 tick slippage, realistic margin (v6 default margin is 100% of notional!), bar magnifier on. [DOC strategies / v6 migration]
7. **One trade at a time, flat by end of session, a hard daily loss stop.** Simpler risk model = more trustworthy backtest. [PRAC]
8. **Reserve untouched out-of-sample data** before tuning anything. Tune on IS only; OOS is looked at once. [LIT]
9. **Prefer parameter plateaus to peaks.** If +/-20% on any parameter flips the result, the edge is noise. [LIT/PRAC]
10. **Enough trades, enough regimes:** >100 trades is TradingView's publishing floor; aim for 200-300+ across multiple years/volatility regimes, and average trade >= 3x round-trip friction. [DOC publishing rules / PRAC]

---

## 1. Architecture

### 1.1 File layout (single script, top to bottom)
```
//@version=6
strategy(...)                 // 1. declaration: costs, limits, object caps
// 2. inputs, grouped (group=, inline=, tooltip=)
// 3. types (UDTs) + enums
// 4. methods (behavior on UDTs)
// 5. global series: ATR, pivots, session flags, HTF requests (ALL ta.* here, unconditionally)
// 6. state updates: structure, zone lists (add / mitigate / expire)
// 7. SIGNAL layer: pure bools/Setup objects, no strategy.* calls
// 8. EXECUTION layer: sizing, strategy.entry/exit/cancel, risk guards
// 9. VISUAL layer: boxes/lines/labels (optionally only on recent bars)
// 10. alerts + debug (plot(display=display.data_window), log.info)
```
Rule: signal logic never references `strategy.*`; execution never computes indicators. This lets you
ship an `indicator()` twin for alerts and unit-check signals visually. [PRAC]

### 1.2 Declaration template (NQ, 1-5 min)
```pine
//@version=6
strategy("Botmax NQ", overlay = true,
     initial_capital       = 100000,
     currency              = currency.USD,
     default_qty_type      = strategy.fixed,
     default_qty           = 1,
     pyramiding            = 1,
     commission_type       = strategy.commission.cash_per_contract,
     commission_value      = 2.25,     // per contract PER FILL (per side). NQ ~ $2-2.50/side all-in; MNQ ~ $0.50-0.75
     slippage              = 1,        // ticks; applied to market & stop orders, not limits
     margin_long           = 8,        // % of notional; v6 default is 100 (= no leverage) -> NQ orders get rejected
     margin_short          = 8,
     use_bar_magnifier     = true,     // Premium/Ultimate plans only
     backtest_fill_limits_assumption = 1, // price must trade 1 tick through a limit to fill
     process_orders_on_close = false,
     calc_on_every_tick    = false,
     max_boxes_count       = 500, max_lines_count = 500, max_labels_count = 500,
     max_bars_back         = 2000)
```
- `commission_value` per side: TradingView charges it on each fill, so round trip = 2x. [PRAC, VERIFY on a 1-trade test]
- Margin: required = qty x price x pointvalue x margin%. NQ @ 25,000 x $20 = $500k notional; at 100% margin
  a $100k account can never open 1 contract. Set margin to approx. CME initial margin as % of notional
  (roughly 5-8% for NQ recently; [VERIFY] current CME value) and make sure `initial_capital` covers it.
  Docs: https://www.tradingview.com/support/solutions/43000717375-how-to-simulate-trading-with-leverage-in-pine-script/
- Never use margin 0 (infinite leverage) — explicitly called unrealistic in the publishing rules. [DOC]

### 1.3 UDTs and methods (v6 syntax, per objects docs)
```pine
type Swing
    int   bar
    int   t
    float price
    bool  isHigh
    bool  broken = false
    bool  swept  = false

type Zone                          // FVG or OB
    int   kind                     // 1 bull, -1 bear
    float top
    float bot
    int   bornBar
    int   bornTime
    bool  touched  = false
    bool  dead     = false
    box   bx       = na

method ce(Zone z) => (z.top + z.bot) / 2          // consequent encroachment (50%)
method contains(Zone z, float p) => p <= z.top and p >= z.bot
method kill(Zone z) =>
    z.dead := true
    if not na(z.bx)
        z.bx.delete()

var array<Swing> swingHighs = array.new<Swing>()
var array<Zone>  fvgs       = array.new<Zone>()
```
- `var` on an object applies to all its fields; `copy()` is shallow (nested objects/boxes shared). [DOC objects]
- History on UDT fields in v6: `(obj[1]).field`, not `obj.field[1]`. [DOC v6 migration]
- Use `enum` for modes (e.g. `enum StopMode` with `structure`, `atr`) + `input.enum()` for clean inputs.
- Maps (`map<string, float>`) are good for named levels: `"PDH"`, `"PDL"`, `"AsiaH"`, `"LonL"`, etc.

### 1.4 Zone storage and lifetime
- Keep bounded arrays: newest at index 0 (`unshift`), cap at N (e.g. 10-20 per side), `pop()` + `kill()` the oldest.
- Remove dead zones by iterating **backwards**, and guard empty arrays:
```pine
if fvgs.size() > 0
    for i = fvgs.size() - 1 to 0          // counts down automatically when from > to
        Zone z = fvgs.get(i)
        if z.dead or bar_index - z.bornBar > maxAgeBars
            z.kill()
            fvgs.remove(i)
```
  Pitfall: with size 0, `for i = -1 to 0` iterates i = -1, 0 -> runtime error (v6 accepts negative indices on
  get(), so -1 may silently hit the last element on non-empty arrays). Always guard. [DOC v6: negative indices]
- v6 re-evaluates the `to` bound every iteration; precompute bounds if the loop mutates the array. [DOC]

### 1.5 Limits that shape the design [DOC limitations]
| Resource | Limit |
|---|---|
| boxes / lines / labels | 500 each (default shows last 50; raise with `max_*_count`) — oldest auto-garbage-collected |
| polylines / tables | 100 / 9 |
| plots | 64 plot counts |
| `request.*()` calls | 40 unique (64 on Ultimate) |
| history reference | 5,000 bars for most series (10,000 for OHLC/time) |
| drawings x-coordinate (bar_index) | `bar_index - 10000` .. `bar_index + 500`; use `xloc.bar_time` to go further back |
| loop time per bar | 500 ms; total script ~20 s (basic) / 40 s |
| collections | 100,000 elements (maps 50,000 pairs) |
| strategy orders | 9,000 in default range (v6 trims oldest instead of erroring); Deep Backtesting keeps all |

Implications:
- Garbage collection deletes *drawings*, not your UDT objects: a `Zone` whose box was GC'd still exists — keep logic
  independent of boxes (never read box coordinates as state).
- "Pine cannot determine the referencing length" -> set `max_bars_back` in the declaration or `max_bars_back(src, n)`.
- For heavy visuals, draw only when `bar_index > last_bar_index - lookbackVisual` (logic still runs on all bars).
- Use the Pine Profiler (editor) to find hot loops. [DOC profiler page] Use `log.info()` + Pine Logs for debugging.

### 1.6 Libraries
- Put reusable, tested primitives (swing tracker, FVG detector, sizing) in a `library()` with `export type`,
  `export method`, `export` functions; import with `import user/Lib/1 as ict`. Version pinning makes backtests reproducible.
- Keep the strategy thin: glue + execution. [PRAC]

---

## 2. Repainting and lookahead — every trap and the fix

### 2.1 Trap list
| Trap | Why | Fix |
|---|---|---|
| Using `close/high/low` of the open realtime bar | fluid values; history only saw final OHLC | strategies calc at close by default; in indicators add `barstate.isconfirmed` or use `[1]` [DOC] |
| `request.security(..., close)` default (lookahead_off) on HTF | no lookahead on history, but in realtime the current (unfinished) HTF bar's value changes tick by tick -> **realtime differs from history** | `expr[1]` + `lookahead_on` [DOC] |
| `lookahead_on` without `[1]` | reads the future HTF close on historical bars -> fantastic, fake backtest | always pair with `[1]` [DOC] |
| `ta.pivothigh(high, L, R)` | returns value R bars after the pivot | treat signal time = pivot bar + R [DOC] |
| Drawing pivots/labels with negative `offset` or at `bar_index - R` | chart looks like it knew in advance | fine for display, but the *signal* happens at `bar_index`; disclose [DOC] |
| `calc_on_every_tick = true` | realtime fills differ from history | keep false; if true, disclose [DOC + publishing rules] |
| `calc_on_order_fills = true` | extra intrabar executions after fills, not reproducible without magnifier | avoid unless needed for bracket logic |
| `varip`, `timenow`, `barstate.isnew`, `barstate.isrealtime` in logic | no historical equivalent | visuals/diagnostics only [DOC] |
| `request.security_lower_tf` in realtime | intrabars unsorted/incomplete in realtime | use only confirmed chart bars [DOC] |
| `barstate.isconfirmed` inside `request.security` | reflects the *requested* TF's bar state | evaluate confirmation on the chart side [DOC exec model] |
| Heikin Ashi / Renko charts for strategies | fills at synthetic prices | standard candles; `fill_orders_on_standard_ohlc` if unavoidable [DOC] |
| `process_orders_on_close = true` | fills at the close of the bar that generated the signal (can't really trade that price) | leave false (fill next bar open) unless modelling MOC-type exits; if true, add slippage [PRAC] |
| Daily levels via `request.security("D", high)` on futures | daily bar = 18:00-17:00 ET session; lookahead_off repaints today's H/L | use `high[1]` + lookahead_on for PDH, or track session H/L in-script |

### 2.2 Correct HTF pattern
```pine
// Non-repainting HTF value: last *completed* HTF bar
htf(expr, tf) => request.security(syminfo.tickerid, tf, expr[1], lookahead = barmerge.lookahead_on)

string biasTF = input.timeframe("60", "Bias timeframe")
float  htfClose = htf(close, biasTF)
float  htfEma   = htf(ta.ema(close, 50), biasTF)       // ta.* evaluated in the HTF context
bool   htfBull  = htfClose > htfEma

// Guard: requested TF must be >= chart TF
if timeframe.in_seconds(biasTF) < timeframe.in_seconds(timeframe.period)
    runtime.error("Bias TF must be >= chart TF")
```
- Signature: `request.security(symbol, timeframe, expression, gaps, lookahead, ignore_invalid_symbol, currency, calc_bars_count)`. [DOC]
- Dynamic requests are ON by default in v6 (series symbol/tf, calls in loops/ifs allowed). [DOC]
- For HTF *structure* (HTF swings/FVGs), compute the whole thing inside a function passed to `request.security`
  and return a tuple, still with the `[1]` offset on each element — or build HTF candles yourself from chart bars
  (more control, no request budget). [PRAC]

### 2.3 Repainting self-test (do this before every serious backtest)
- [ ] Add the strategy to a 1-min chart, let it run live for a session (or use Bar Replay), screenshot signals; reload the chart; signals must be identical.
- [ ] Search code for: `lookahead_on` (each must have `[1]`), `varip`, `timenow`, `calc_on_every_tick`, `offset =` negative, `barstate.isnew`.
- [ ] Compare results with bar magnifier on vs off; large divergence = intrabar-ambiguity dependence (see 5.2).

---

## 3. Coding ICT concepts correctly

General: define every concept with an unambiguous, testable rule, then parametrize minimally. Discretionary ICT
language ("obvious" liquidity, "clean" displacement) must become numbers (ATR multiples, bar counts). [PRAC]

### 3.1 Swings
- Fractal pivots: `ta.pivothigh(high, L, R)` / `ta.pivotlow(low, L, R)`. Confirmation delay = R bars.
- Two layers (as in LuxAlgo SMC): **internal** (small L/R, e.g. 3-5) for entries, **swing** (e.g. 10-50) for bias. Trade internal breaks only in the direction of swing/HTF structure.
- Tie handling: equal highs inside the window — `ta.pivothigh` needs strict dominance on the left [VERIFY exact tie rule]; don't rely on EQH being pivots, detect EQH separately (|h1-h2| <= k x ATR).
```pine
int   L  = input.int(3, "Internal pivot left",  minval = 1)
int   R  = input.int(3, "Internal pivot right", minval = 1)
float ph = ta.pivothigh(high, L, R)
float pl = ta.pivotlow(low,  L, R)
if not na(ph)
    swingHighs.unshift(Swing.new(bar_index - R, time[R], ph, true))
    if swingHighs.size() > 20
        swingHighs.pop()
```

### 3.2 BOS / CHoCH
- Track `trend` (1/-1) and the most recent *unbroken* swing high/low.
- Break rule: `close > lastHigh.price` (body close — more robust than wick; make it an input).
  - If `trend == 1` -> **BOS** (continuation). If `trend == -1` -> **CHoCH** (reversal), set `trend := 1`.
- Mark the swing `broken := true` so it fires once. Only the latest confirmed swing is eligible.
- Pitfall: because the swing is confirmed R bars late, price may already have closed beyond it before it exists.
  Decide explicitly: break must occur *after* confirmation (strict, no lookahead) — do not retro-label.
```pine
var int trend = 0
if swingHighs.size() > 0
    Swing sh = swingHighs.get(0)
    if not sh.broken and close > sh.price and bar_index > sh.bar + R
        sh.broken := true
        bool isChoch = trend == -1
        trend := 1
        bullBreak := true         // declared earlier in global scope: bool bullBreak = false (reset each bar)
```

### 3.3 Fair Value Gaps
- Bullish FVG on the close of bar 0: `low > high[2]` -> zone `[high[2], low]`. Bearish: `high < low[2]` -> `[high, low[2]]`.
- Filter noise: `gap >= minAtrMult * ta.atr(14)` (ATR computed globally), and optionally require the middle candle
  body to be displacement (`math.abs(close[1]-open[1]) >= k * atr`).
- States: `fresh -> touched (first trade into it) -> CE hit (50%) -> filled (price through far edge) / invalidated (close beyond far edge)`.
  Choose one mitigation definition and keep it consistent between logic and visuals.
- First-touch only: most setups trade the first return; mark `touched` and ignore later touches.
- Expire after N bars or at session end (intraday FVGs lose relevance). Cap count.
- Entry at CE via limit order (see 4.1) — remember limits fill only if price trades through by
  `backtest_fill_limits_assumption` ticks.
- HTF FVGs: build via `request.security` returning `[high[1], low[1], high[3]...]` with the `[1]` rule, or aggregate chart bars.

### 3.4 Order blocks
- Operational definition (pick one, document it): last opposite-colored candle before a displacement leg that
  produces a BOS/CHoCH. Bull OB = last down-close candle before the up-leg that broke the swing high.
- Zone = candle body (tighter) or full range (wick) — input.
- Search backwards from the break bar to the swing low bar for the last bearish candle; bounded loop
  (`for i = 1 to math.min(bar_index - sh.bar, 50)`).
- Mitigation: LuxAlgo-style removes OB on close through it; "touched" on first wick into it.
- Quality filters: OB followed by an FVG (displacement), OB inside discount (below 50% of dealing range) for longs.

### 3.5 Liquidity and sweeps
- Pools: prior swing highs/lows, EQH/EQL, PDH/PDL, session highs/lows (Asia 20:00-00:00 ET, London 02:00-05:00 ET),
  overnight high/low, previous week H/L.
- Sweep (bearish example): `high > level and close < level` on the same bar (wick through, close back) — or
  within K bars (reclaim). Require the level to be "untouched" before the sweep.
- Track session H/L in-script (robust, no request budget):
```pine
bool inAsia   = not na(time(timeframe.period, "2000-0000", "America/New_York"))
var float asiaH = na
var float asiaL = na
if inAsia and not inAsia[1]
    asiaH := high, asiaL := low
else if inAsia
    asiaH := math.max(asiaH, high), asiaL := math.min(asiaL, low)
bool sweptAsiaH = high > asiaH and close < asiaH and not inAsia
```
  Note: `inAsia[1]` on a bool is fine; `na()` on bool is a compile error in v6.

### 3.6 Killzones and time
- Always `time(timeframe.period, sess, "America/New_York")`; returns `na` outside the session. [DOC]
- Session strings `"HHmm-HHmm:days"`, days 1 = Sunday .. 7 = Saturday; overnight like `"2000-0000"` or `"1800-1700"` allowed. [DOC]
  [VERIFY] whether weekday digits are evaluated in the given timezone or exchange timezone — avoid day digits for sessions crossing midnight.
- Typical NY-time windows (ICT convention, [PRAC]): Asia 20:00-00:00, London 02:00-05:00, NY AM 08:30-11:00
  (Silver Bullet 10:00-11:00), NY lunch 12:00-13:30 (avoid), NY PM 13:30-16:00. Put all as `input.session`.
- DST is handled by the IANA timezone name; never hardcode UTC offsets.
- Session start detection: `inKZ and not inKZ[1]`. End-of-day flatten:
```pine
bool eod = not na(time(timeframe.period, "1555-1600", "America/New_York"))
if eod
    strategy.cancel_all()
    strategy.close_all(comment = "EOD")
```
- Chart-TF caveat: a 15-min bar that opens 08:15 is outside `0830-1100`; killzone logic behaves differently per TF — test on the TF you'll trade.

### 3.7 HTF bias
- Candidates: HTF swing structure direction (from 3.2 run on HTF), HTF close vs. prior day's midpoint, daily
  open ("midnight open" 00:00 ET) above/below, price in HTF premium/discount of the prior-day range.
- All via the non-repainting pattern or from completed in-script levels. Bias is fixed per session in many
  ICT models — compute it once at session start and hold it (`var`), which also reduces overfitting. [PRAC]

---

## 4. Strategy design

### 4.1 Entries
- Canonical sequence (one example): HTF bias -> in killzone -> liquidity sweep against bias -> CHoCH/BOS with
  displacement in bias direction -> FVG created by that leg -> limit entry at FVG edge or CE.
- Market entry at next open after confirmation is simplest and most honest; limit entries improve price but
  suffer adverse selection (you fill on the losers, miss the fast winners). Test both. [PRAC]
- Order expiry: cancel an unfilled limit after N bars or when the setup invalidates:
```pine
if longSetup and strategy.position_size == 0 and not pending
    strategy.entry("L", strategy.long, qty = qty, limit = entryPx, comment = "FVG CE")
    pending := true, pendingBar := bar_index
if pending and (bar_index - pendingBar > maxWait or close < stopPx)
    strategy.cancel("L"), pending := false
if strategy.position_size != 0
    pending := false
```
- `strategy.entry(id, direction, qty, limit, stop, oca_name, oca_type, comment, alert_message, disable_alert)` —
  no `when` in v6 (wrap in `if`). An entry opposite an open position reverses it (adds position size). [DOC]

### 4.2 Stops
- Structure stop: beyond the swept extreme / OB far edge / FVG far edge, plus buffer (e.g. 2-4 ticks or 0.1 x ATR).
- ATR stop: `k x ta.atr(n)`; use as a floor/cap on the structure stop (reject setups where structure stop > maxStopATR x ATR).
- Round to tick: `math.round_to_mintick(px)`.
- Place protective exits in the same bar as entry so they're active once filled:
```pine
if strategy.position_size > 0
    strategy.exit("LX", from_entry = "L", stop = stopPx, limit = tpPx, comment_loss = "SL", comment_profit = "TP")
```
- v6: if you pass both absolute (`stop`/`limit`) and relative (`loss`/`profit` in ticks), whichever triggers first
  is used (v5 preferred absolute). Use one style only. [DOC migration]

### 4.3 Targets
- Liquidity targets: nearest opposing pool (swing high/low, session H/L, PDH/PDL) — the ICT "draw on liquidity".
- R-multiple targets: 2R fixed, or partials (`qty_percent = 50` at 1R, runner to liquidity, stop to BE).
- Require `targetDistance >= minRR x stopDistance`, else skip the trade.
- Partials and BE moves increase parameter count: add only if OOS improves. [PRAC]

### 4.4 Position sizing
```pine
float riskUSD = input.float(500, "Risk per trade ($)")
float stopPts = math.abs(entryPx - stopPx)
int   qty     = stopPts > 0 ? int(math.floor(riskUSD / (stopPts * syminfo.pointvalue))) : 0
// NQ pointvalue = 20, MNQ = 2 (CME specs). qty == 0 -> skip trade.
```
- Validate with fixed 1 contract first (clean per-trade stats), then fixed-risk sizing.
- Publishing guidance: risk per trade should be sustainable (PineCoders/TradingView commonly cite <= 5-10% of equity [VERIFY exact wording]); for NQ intraday, 0.5-1% is typical.
- MNQ lets you size finely and makes small-account backtests realistic.

### 4.5 One trade at a time, pyramiding, risk guards
- `pyramiding = 1`, gate entries with `strategy.position_size == 0 and not pending`.
- Max trades per session (counter reset at session start), max 1 loss per killzone, etc.
- Built-in guards: `strategy.risk.max_intraday_loss(value, strategy.cash)`, `strategy.risk.max_intraday_filled_orders(n)`,
  `strategy.risk.allow_entry_in(strategy.direction.long)` (note: opposite entries then close without reversing). [DOC]
- News: Pine has no reliable economic-calendar feed for backtests [VERIFY]; approximate by excluding 08:30 ET bars
  on CPI/NFP days via a manual date list input, or accept it as part of the distribution.

### 4.6 Session filters and contract data
- Trade RTH/killzones only; CME daily halt 17:00-18:00 ET; flatten before.
- Continuous contract `NQ1!` has roll gaps; TradingView offers back-adjustment for continuous futures in chart
  settings [VERIFY availability on your plan]. Levels spanning a roll date (PDH on roll day) can be wrong — consider
  skipping roll days.
- Intraday history depth depends on plan; Deep Backtesting extends range. Record the exact date range with every result.

---

## 5. Validation

### 5.1 How the broker emulator fills (know this or be fooled) [DOC strategies]
- Historical orders placed on bar close fill at the earliest on the **next bar's open**.
- Intrabar path assumed: if open is closer to high -> O-H-L-C, else O-L-H-C; **no gaps inside bars**.
- Consequence: when stop and target are both inside one bar, the outcome is guessed. With tight NQ stops on
  1-5 min bars this happens a lot. -> `use_bar_magnifier = true` (Premium/Ultimate; up to 200k LTF bars, so early
  history may lack magnifier coverage). [DOC]
- Slippage (ticks) hits market and stop orders; limits fill at the limit price (optionally only if traded through
  by `backtest_fill_limits_assumption` ticks).
- Realtime vs history can still differ; forward-test (paper) for weeks before live.

### 5.2 Realistic NQ settings checklist
- [ ] Commission per side: NQ ~ $2.00-2.50, MNQ ~ $0.50-0.75 all-in (broker + CME + NFA). Examples: NinjaTrader and IBKR schedules — https://ninjatrader.com/pricing/commissions/ , https://www.interactivebrokers.com/en/pricing/commissions-futures.php . Use the high end.
- [ ] Slippage: 1 tick minimum on stops/market; stress-test at 2 ticks (NQ tick = 0.25 pt = $5; MNQ = $0.50). CME specs: https://www.cmegroup.com/markets/equities/nasdaq/e-mini-nasdaq-100.html
- [ ] Friction sanity: 1 tick each side + commission ~ 0.75-1 pt round trip on NQ. An academic MNQ study used a
      2.0-point friction floor and found none of 14 OHLCV intraday momentum families survived walk-forward — the bar is high. (arXiv 2605.04004)
- [ ] Margin set to a realistic % (not 100, not 0); initial capital realistic for the contract (MNQ for < $50k).
- [ ] Bar magnifier on; also run with it off and compare.
- [ ] `process_orders_on_close = false`, `calc_on_every_tick = false`.
- [ ] No warnings in the Strategy Tester (publishing rules require resolving them).

### 5.3 Metrics that matter
| Metric | Healthy intraday range [PRAC] | Notes |
|---|---|---|
| Trade count | >= 200 (>= 100 minimum) | per regime matters more than total |
| Profit factor | 1.3-2.0 net | PF > 2.5-3 with many trades -> suspect a bug/lookahead |
| Expectancy | > 0.15R net; avg trade >= 3x friction | in points and R, after costs |
| Max drawdown | < 20-25% of capital; recovery < 3-6 months | compare to annual net profit (Calmar-like) |
| Win rate x avg R | consistent with each other | 80% WR + 0.3R avg win = one bad day wipes weeks |
| Sharpe / Sortino | daily-returns based, annualized | TV Sharpe uses monthly returns [VERIFY]; compute your own from exported trades |
| Consecutive losses | plan capital for 2x worst seen | |
| Exposure / time in market | low for ICT intraday | |
| Long vs short split | both positive or explained | NQ upward drift flatters longs |
| Per-year / per-weekday / per-killzone breakdown | no single period carrying the result | |

### 5.4 In-sample / out-of-sample in TradingView
- Add a date window input and gate entries (not indicator calculations) by it:
```pine
int  tStart = input.time(timestamp("2021-01-01T00:00:00"), "Test start")
int  tEnd   = input.time(timestamp("2024-01-01T00:00:00"), "Test end")
bool inTest = time >= tStart and time < tEnd
// ... longSignal := longSignal and inTest
```
- Split: e.g. IS = oldest 60-70%, OOS = newest 30-40%. Freeze rules and parameters before the single OOS run.
  Also keep the last 2-3 months as a paper-trade "holdout" (the ultimate OOS). [LIT]
- The Strategy Tester's own date-range setting can also be used [VERIFY current UI]; the input approach is reproducible and scriptable.

### 5.5 Walk-forward (manual, since TV has no built-in WFO)
1. Choose windows: optimize 12 months, test next 3 months; roll forward 3 months.
2. For each window, pick the parameter set from the *plateau center* (not the max) on IS; record OOS stats.
3. Concatenate OOS segments -> this equity curve is the real estimate. Walk-forward efficiency = OOS annualized / IS annualized; > 0.5 is acceptable [PRAC].
4. If most OOS windows are negative, stop — don't add filters until it "works".
- Export "List of trades" from the Strategy Tester to CSV and do WFO/Monte Carlo analysis in Python.

### 5.6 Parameter robustness
- Fewer parameters is the strongest defence. Target <= 4-6 tunables; hardcode ICT definitions where possible.
- Sweep each key parameter across a grid (pivot length 2-8, FVG min size 0-0.5 ATR, RR 1.5-3) and plot net PF as a
  heatmap; require a broad positive plateau.
- Stress tests: +1 tick slippage, +50% commission, delay entry by 1 bar, remove best 5% of trades, shift killzone +/-15 min.
  The strategy should degrade gracefully, not collapse.
- Cross-validation on related markets: ES/MES and YM with same parameters — a real edge usually transfers partially. [PRAC]

### 5.7 Statistical overfitting controls [LIT]
- **Count your trials.** Every variant you tried inflates the best Sharpe. The Deflated Sharpe Ratio corrects for
  number of trials, skew and kurtosis (Bailey & López de Prado 2014, SSRN 2460551).
- **PBO / CSCV:** split history into S blocks, evaluate all IS/OOS combinations, estimate probability the IS-best
  config underperforms OOS median (SSRN 2326253). Doable in Python from exported per-config trade lists.
- **Minimum backtest length** grows with the number of configurations tried (Bailey et al., "Pseudo-Mathematics and Financial Charlatanism", Notices AMS 2014).
- **Monte Carlo** on trade list: reshuffle order (drawdown distribution), bootstrap with replacement (PF/expectancy
  CI), randomly skip 10-20% of trades (fill uncertainty). Use the 95th-percentile drawdown for sizing.
- t-stat of mean trade return > 2 (ideally > 3 given multiple testing — Harvey & Liu). [LIT]
- Keep a research log: every variant, its date, its IS result. This is the input for DSR.

### 5.8 Red flags of a fake-looking backtest
- [ ] Equity curve nearly a straight line; PF > 3 or win rate > 85% over hundreds of trades.
- [ ] `lookahead_on` without `[1]`; `security()` of the chart TF or lower with lookahead.
- [ ] Signals that appear on pivot bars (acting before R-bar confirmation).
- [ ] Zero commission / zero slippage / margin 0 / huge default qty or % of equity sizing compounding.
- [ ] Results collapse with bar magnifier on, or with 1 extra tick of slippage.
- [ ] Heikin Ashi/Renko chart backtests.
- [ ] Few trades (< 100) or all profit from a handful of trades / one month / one year (e.g. 2020 or 2022).
- [ ] Average trade < 2x round-trip cost (a few ticks).
- [ ] Profit comes almost only from limit entries at exact extremes (fill-assumption artifact).
- [ ] Strategy only works on one chart TF and breaks on adjacent TFs (e.g. 3m vs 5m).
- [ ] `calc_on_every_tick` or `calc_on_order_fills` enabled without explanation.

---

## 6. What separates the best published scripts

### 6.1 Traits of top scripts [PRAC, observed in LuxAlgo SMC / PineCoders guidance]
- Precise, documented definitions (internal vs swing structure, body vs wick break, mitigation rule) with inputs to switch.
- Bounded memory: fixed-size arrays of UDTs, explicit deletion of mitigated zones, `max_*_count` set, no reliance on GC.
- Visual-logic separation; visuals never feed back into logic.
- Honest repainting disclosure (e.g. "pivots confirm N bars late; labels are drawn back on the pivot bar").
- Clean inputs: `group=`, `inline=`, `tooltip=`, sensible defaults, `display = display.none` on noisy plots.
- Default properties that match the description (publishing rules require explaining Properties defaults).
- Alerts that mirror strategy logic (`alert_message` on orders + `{{strategy.order.alert_message}}` placeholder, or `alert()` with `alert.freq_once_per_bar_close`).

### 6.2 Common mistakes
- Calling `ta.*` inside `if`/loops or after lazy `and` -> stale series (compiler warns; heed it).
- Treating `na` bools (v6: impossible — bool can't be na; `na(boolVar)` won't compile).
- Integer division surprises: v6 `5/2 = 2.5` for const ints; wrap with `int()` if you need floor.
- Comparing `timeframe.period == "D"` (v6 returns `"1D"`).
- Using `obj.field[1]` (v6 requires `(obj[1]).field`).
- Loop bound recomputation / empty-array reverse loops.
- Reading box coordinates as state; boxes get garbage-collected.
- Hardcoding UTC offsets or relying on exchange timezone for NY sessions.
- Optimizing on the whole history then reporting the same period.
- Adding filters until the curve is smooth (each filter = another trial for DSR).
- Mixing chart TF assumptions (killzone start bars, FVG sizes) and testing on a different TF than traded.
- Ignoring roll dates, halts, and the 17:00-18:00 ET break.
- Forgetting the v6 margin default and wondering why no trades appear / "margin call" events.

---

## 7. Workflow we will follow

1. **Spec**: write each concept rule in plain text with numbers (this doc, section 3). Freeze v1.
2. **Indicator first**: build detection (swings, BOS/CHoCH, FVG, OB, sweeps, killzones, bias) as an `indicator()`;
   eyeball 50+ examples across dates; run the repainting self-test (2.3).
3. **Library**: move stable primitives into a versioned library.
4. **Strategy v1**: 1 contract, market entry next bar, structure stop, 2R target, one trade/day per killzone, EOD flat.
   Realistic costs (5.2). Only IS date range.
5. **Diagnose** on IS: breakdown by year/weekday/killzone/long-short; fix bugs, not results.
6. **Robustness** (5.6) on IS; pick plateau parameters; log every trial.
7. **Walk-forward** (5.5), then the **single OOS run** (5.4). Compute DSR/Monte Carlo from exported trades.
8. **Paper-trade** the live chart with alerts for 4-8 weeks; compare live fills vs backtest on the same days.
9. **Ship**: document defaults, repainting behavior, costs, date range, and known weaknesses.

### Pre-ship checklist
- [ ] `//@version=6`, no compiler warnings, no Strategy Tester warnings
- [ ] All HTF calls use `expr[1]` + `lookahead_on`; no `varip`/`timenow` in logic
- [ ] All `ta.*` calls global and unconditional
- [ ] Sessions use `"America/New_York"`; EOD flatten; no trades in 17:00-18:00 ET
- [ ] Commission per side, slippage >= 1 tick, margin realistic, bar magnifier on
- [ ] >= 200 trades, positive in most years and both directions (or direction restriction justified)
- [ ] OOS and walk-forward results reported alongside IS; trial count logged
- [ ] Survives +1 tick slippage, 1-bar entry delay, +/-20% parameter changes
- [ ] Live/paper signals match reloaded-chart signals (no repaint)
