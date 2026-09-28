# Concept matrix: every indicator x every ICT concept (Jev)

5074 pairs judged. Improve is 0-3 (0 hurts, 1 neutral, 2 useful, 3 strong); clean = probability the pair codes into non-repainting Pine rules; value = improve x (0.5 + 0.5 x clean).

## How indicators relate to concepts overall

- biases: 1337
- confirms: 1279
- filters: 831
- manages_risk: 567
- locates: 560
- times: 170
- unrelated: 145
- conflicts: 107
- implements: 78

## Best indicators overall (sum of value across all concepts)

- **Session VWAP with Standard Deviation Bands**: best with Fair Value Gap (FVG; BISI bullish / SIBI bearish; imbalance, inefficiency; Consequent Encroachment) (biases, 2.201); Killzones (Asia, London Open, NY AM/Open, London Close, NY PM) (biases, 2.175); Volume Imbalance (VI) (biases, 2.168)
- **Volatility Regime / Volatility Targeting**: best with Vacuum Block (event/opening gap) (manages_risk, 2.037); Balanced Price Range (BPR) (manages_risk, 2.027); Volume Imbalance (VI) (manages_risk, 2.01)
- **Time-Series Momentum (Trend Following)**: best with Fair Value Gap (FVG; BISI bullish / SIBI bearish; imbalance, inefficiency; Consequent Encroachment) (biases, 2.061); New Day Opening Gap (NDOG) (biases, 1.987); Inversion Fair Value Gap (IFVG; inverted FVG) (biases, 1.962)
- **Chandelier Exit**: best with Fair Value Gap (FVG; BISI bullish / SIBI bearish; imbalance, inefficiency; Consequent Encroachment) (manages_risk, 1.962); Killzones (Asia, London Open, NY AM/Open, London Close, NY PM) (manages_risk, 1.927); Balanced Price Range (BPR) (manages_risk, 1.918)
- **ATR Exceedance Probability Model [LuxAlgo]**: best with Volume Imbalance (VI) (filters, 1.955); Fair Value Gap (FVG; BISI bullish / SIBI bearish; imbalance, inefficiency; Consequent Encroachment) (filters, 1.941); Vacuum Block (event/opening gap) (filters, 1.935)
- **Universal Signal Backtester [LuxAlgo]**: best with Change in State of Delivery (CISD) (manages_risk, 1.932); Fair Value Gap (FVG; BISI bullish / SIBI bearish; imbalance, inefficiency; Consequent Encroachment) (manages_risk, 1.922); Market Structure Shift (MSS; Change of Character / CHoCH) (manages_risk, 1.907)
- **Supertrend**: best with Balanced Price Range (BPR) (manages_risk, 1.871); Inversion Fair Value Gap (IFVG; inverted FVG) (manages_risk, 1.862); New Day Opening Gap (NDOG) (manages_risk, 1.861)
- **SuperTrend AI (Clustering) [LuxAlgo]**: best with Volume Imbalance (VI) (manages_risk, 1.933); Inversion Fair Value Gap (IFVG; inverted FVG) (manages_risk, 1.902); Balanced Price Range (BPR) (manages_risk, 1.902)
- **Bollinger Bands (with %b and BandWidth)**: best with New Day Opening Gap (NDOG) (filters, 1.918); Vacuum Block (event/opening gap) (filters, 1.889); Volume Imbalance (VI) (filters, 1.871)
- **Trend Regularity Adaptive Moving Average [LuxAlgo]**: best with Inversion Fair Value Gap (IFVG; inverted FVG) (biases, 1.888); Balanced Price Range (BPR) (biases, 1.858); Killzones (Asia, London Open, NY AM/Open, London Close, NY PM) (biases, 1.836)
- **Keltner Channels**: best with Killzones (Asia, London Open, NY AM/Open, London Close, NY PM) (confirms, 1.797); Fair Value Gap (FVG; BISI bullish / SIBI bearish; imbalance, inefficiency; Consequent Encroachment) (filters, 1.785); Inversion Fair Value Gap (IFVG; inverted FVG) (filters, 1.767)
- **Anchored VWAP (manual and auto-anchored)**: best with Change in State of Delivery (CISD) (confirms, 1.768); Vacuum Block (event/opening gap) (confirms, 1.719); Market Structure Shift (MSS; Change of Character / CHoCH) (confirms, 1.7)
- **ADX / Directional Movement Index (DMI)**: best with Fair Value Gap (FVG; BISI bullish / SIBI bearish; imbalance, inefficiency; Consequent Encroachment) (filters, 1.801); Balanced Price Range (BPR) (filters, 1.795); Killzones (Asia, London Open, NY AM/Open, London Close, NY PM) (filters, 1.775)
- **AI Channels (Clustering) [LuxAlgo]**: best with Volume Imbalance (VI) (manages_risk, 1.802); Vacuum Block (event/opening gap) (manages_risk, 1.801); Killzones (Asia, London Open, NY AM/Open, London Close, NY PM) (biases, 1.783)
- **Multi-Horizon Volatility Waterfall [LuxAlgo]**: best with Vacuum Block (event/opening gap) (filters, 1.831); Volume Imbalance (VI) (filters, 1.823); Inversion Fair Value Gap (IFVG; inverted FVG) (filters, 1.803)
- **Floor Pivot Points (Traditional, Fibonacci, Woodie, Classic, DeMark, Camarilla)**: best with Vacuum Block (event/opening gap) (confirms, 1.906); Inversion Fair Value Gap (IFVG; inverted FVG) (locates, 1.879); Volume Imbalance (VI) (locates, 1.871)
- **LuxAlgo Backtesters (S&O / PAC / OSC) and LUCID**: best with Fair Value Gap (FVG; BISI bullish / SIBI bearish; imbalance, inefficiency; Consequent Encroachment) (manages_risk, 1.872); Market Structure Shift (MSS; Change of Character / CHoCH) (manages_risk, 1.826); Change in State of Delivery (CISD) (manages_risk, 1.823)
- **Choppiness Index (CHOP)**: best with Inversion Fair Value Gap (IFVG; inverted FVG) (filters, 1.786); Volume Imbalance (VI) (filters, 1.767); Balanced Price Range (BPR) (filters, 1.758)
- **Machine Learning Moving Average [LuxAlgo]**: best with Volume Imbalance (VI) (biases, 1.822); Balanced Price Range (BPR) (biases, 1.784); Inversion Fair Value Gap (IFVG; inverted FVG) (biases, 1.783)
- **TTM Squeeze / Squeeze Momentum Indicator**: best with Killzones (Asia, London Open, NY AM/Open, London Close, NY PM) (filters, 1.737); Fair Value Gap (FVG; BISI bullish / SIBI bearish; imbalance, inefficiency; Consequent Encroachment) (filters, 1.729); Balanced Price Range (BPR) (filters, 1.721)

## Top 5 indicators per ICT concept

### Swing Points hierarchy (STH/ITH/LTH, STL/ITL/LTL; ICT swing high/low)
- Order Blocks & Breaker Blocks [LuxAlgo]: locates, improve 2.52, clean 0.44 (review)
- Session VWAP with Standard Deviation Bands: biases, improve 2.26, clean 0.57 (review)
- Buyside & Sellside Liquidity [LuxAlgo]: locates, improve 2.69, clean 0.28
- Swing Failure Pattern (SFP) [LuxAlgo]: times, improve 2.53, clean 0.34 (review)
- Fair Value Gap [LuxAlgo]: locates, improve 2.11, clean 0.57 (review)

### Break of Structure (BOS)
- Session VWAP with Standard Deviation Bands: biases, improve 2.3, clean 0.74
- Liquidity Voids (FVG) [LuxAlgo]: locates, improve 2.15, clean 0.7
- Fair Value Gap [LuxAlgo]: locates, improve 2.13, clean 0.68 (review)
- Universal Signal Backtester [LuxAlgo]: manages_risk, improve 2.17, clean 0.64 (review)
- ICT Concepts [LuxAlgo]: implements, improve 2.52, clean 0.41 (review)

### Market Structure Shift (MSS; Change of Character / CHoCH)
- Session VWAP with Standard Deviation Bands: biases, improve 2.44, clean 0.76 (review)
- Order Blocks & Breaker Blocks [LuxAlgo]: locates, improve 2.56, clean 0.52 (review)
- Liquidity Voids (FVG) [LuxAlgo]: locates, improve 2.22, clean 0.73
- Universal Signal Backtester [LuxAlgo]: manages_risk, improve 2.27, clean 0.68 (review)
- Buyside & Sellside Liquidity [LuxAlgo]: locates, improve 2.73, clean 0.39 (review)

### Change in State of Delivery (CISD)
- Session VWAP with Standard Deviation Bands: biases, improve 2.32, clean 0.78 (review)
- Universal Signal Backtester [LuxAlgo]: manages_risk, improve 2.26, clean 0.71
- Buyside & Sellside Liquidity [LuxAlgo]: locates, improve 2.69, clean 0.41 (review)
- Chandelier Exit: manages_risk, improve 2.1, clean 0.8
- ICT Concepts [LuxAlgo]: confirms, improve 2.51, clean 0.48 (review)

### Displacement
- Session VWAP with Standard Deviation Bands: biases, improve 2.15, clean 0.87 (review)
- Intraday Momentum 'Noise Area' Breakout (Beat the Market): filters, improve 2.11, clean 0.83 (review)
- Time-Series Momentum (Trend Following): biases, improve 2.07, clean 0.83
- Volatility Regime / Volatility Targeting: manages_risk, improve 2.06, clean 0.83
- Chandelier Exit: manages_risk, improve 2.01, clean 0.87

### Fair Value Gap (FVG; BISI bullish / SIBI bearish; imbalance, inefficiency; Consequent Encroachment)
- Session VWAP with Standard Deviation Bands: biases, improve 2.38, clean 0.85 (review)
- Time-Series Momentum (Trend Following): biases, improve 2.29, clean 0.8
- Volatility Regime / Volatility Targeting: manages_risk, improve 2.22, clean 0.79
- Chandelier Exit: manages_risk, improve 2.11, clean 0.86
- ATR Exceedance Probability Model [LuxAlgo]: filters, improve 2.11, clean 0.84

### Inversion Fair Value Gap (IFVG; inverted FVG)
- Session VWAP with Standard Deviation Bands: biases, improve 2.27, clean 0.89
- Volatility Regime / Volatility Targeting: manages_risk, improve 2.11, clean 0.88
- Time-Series Momentum (Trend Following): biases, improve 2.11, clean 0.86
- ATR Exceedance Probability Model [LuxAlgo]: filters, improve 2.07, clean 0.86
- Chandelier Exit: manages_risk, improve 2.01, clean 0.9

### Balanced Price Range (BPR)
- Session VWAP with Standard Deviation Bands: biases, improve 2.21, clean 0.88
- Volatility Regime / Volatility Targeting: manages_risk, improve 2.18, clean 0.86
- Time-Series Momentum (Trend Following): biases, improve 2.12, clean 0.85
- ATR Exceedance Probability Model [LuxAlgo]: filters, improve 2.08, clean 0.85
- Chandelier Exit: manages_risk, improve 2.03, clean 0.89

### Volume Imbalance (VI)
- Session VWAP with Standard Deviation Bands: biases, improve 2.27, clean 0.91 (review)
- Volatility Regime / Volatility Targeting: manages_risk, improve 2.15, clean 0.87
- ATR Exceedance Probability Model [LuxAlgo]: filters, improve 2.08, clean 0.88
- SuperTrend AI (Clustering) [LuxAlgo]: manages_risk, improve 2.09, clean 0.85
- Intraday Momentum 'Noise Area' Breakout (Beat the Market): filters, improve 2.09, clean 0.85 (review)

### Liquidity Void (LV)
- Volatility Regime / Volatility Targeting: manages_risk, improve 2.2, clean 0.81
- Session VWAP with Standard Deviation Bands: biases, improve 2.18, clean 0.82
- Time-Series Momentum (Trend Following): biases, improve 2.14, clean 0.78
- ATR Exceedance Probability Model [LuxAlgo]: filters, improve 2.09, clean 0.81
- Supertrend: manages_risk, improve 1.99, clean 0.86

### Vacuum Block (event/opening gap)
- Volatility Regime / Volatility Targeting: manages_risk, improve 2.19, clean 0.86
- Session VWAP with Standard Deviation Bands: biases, improve 2.15, clean 0.89 (review)
- ATR Exceedance Probability Model [LuxAlgo]: filters, improve 2.07, clean 0.87
- Time-Series Momentum (Trend Following): biases, improve 2.09, clean 0.84
- Floor Pivot Points (Traditional, Fibonacci, Woodie, Classic, DeMark, Camarilla): confirms, improve 2.05, clean 0.86 (review)

### New Day Opening Gap (NDOG)
- Session VWAP with Standard Deviation Bands: biases, improve 2.21, clean 0.88
- Volatility Regime / Volatility Targeting: manages_risk, improve 2.14, clean 0.86
- Time-Series Momentum (Trend Following): biases, improve 2.16, clean 0.84
- Bollinger Bands (with %b and BandWidth): filters, improve 2.04, clean 0.88
- ATR Exceedance Probability Model [LuxAlgo]: filters, improve 2.04, clean 0.86

### New Week Opening Gap (NWOG)
- Session VWAP with Standard Deviation Bands: biases, improve 2.14, clean 0.68 (review)
- Time-Series Momentum (Trend Following): biases, improve 2.16, clean 0.57 (review)
- Supertrend: manages_risk, improve 1.96, clean 0.72 (review)
- Volatility Regime / Volatility Targeting: manages_risk, improve 2.07, clean 0.61 (review)
- ATR Exceedance Probability Model [LuxAlgo]: filters, improve 2.05, clean 0.62 (review)

### Opening Range Gap (ORG; RTH gap)
- Session VWAP with Standard Deviation Bands: biases, improve 2.38, clean 0.75
- Intraday Momentum 'Noise Area' Breakout (Beat the Market): times, improve 2.29, clean 0.72 (review)
- Time-Series Momentum (Trend Following): biases, improve 2.21, clean 0.64 (review)
- Supertrend: manages_risk, improve 1.96, clean 0.8
- Chandelier Exit: manages_risk, improve 2.0, clean 0.75

### First Presented Fair Value Gap (FPFVG; 1st presented FVG)
- Session VWAP with Standard Deviation Bands: biases, improve 2.38, clean 0.73
- Universal Signal Backtester [LuxAlgo]: manages_risk, improve 2.18, clean 0.68 (review)
- Intraday Momentum 'Noise Area' Breakout (Beat the Market): filters, improve 2.2, clean 0.65 (review)
- SuperTrend AI (Clustering) [LuxAlgo]: manages_risk, improve 2.16, clean 0.63 (review)
- Volatility Regime / Volatility Targeting: manages_risk, improve 2.16, clean 0.63 (review)

### Order Block (OB; bullish/bearish; mean threshold)
- Session VWAP with Standard Deviation Bands: biases, improve 2.32, clean 0.39 (review)
- Buyside & Sellside Liquidity [LuxAlgo]: locates, improve 2.57, clean 0.19 (review)
- Universal Signal Backtester [LuxAlgo]: manages_risk, improve 2.19, clean 0.37 (review)
- Fair Value Gap [LuxAlgo]: confirms, improve 2.08, clean 0.44 (review)
- Time-Series Momentum (Trend Following): biases, improve 2.28, clean 0.29

### Breaker Block (breaker)
- Universal Signal Backtester [LuxAlgo]: manages_risk, improve 2.18, clean 0.45 (review)
- Session VWAP with Standard Deviation Bands: biases, improve 2.25, clean 0.4 (review)
- LuxAlgo Backtesters (S&O / PAC / OSC) and LUCID: manages_risk, improve 2.1, clean 0.46 (review)
- ATR Exceedance Probability Model [LuxAlgo]: filters, improve 2.13, clean 0.39 (review)
- Buyside & Sellside Liquidity [LuxAlgo]: locates, improve 2.43, clean 0.21 (review)

### Mitigation Block
- Session VWAP with Standard Deviation Bands: biases, improve 2.23, clean 0.41 (review)
- Universal Signal Backtester [LuxAlgo]: manages_risk, improve 2.13, clean 0.41 (review)
- Volatility Regime / Volatility Targeting: manages_risk, improve 2.21, clean 0.31 (review)
- ATR Exceedance Probability Model [LuxAlgo]: filters, improve 2.1, clean 0.35 (review)
- Time-Series Momentum (Trend Following): biases, improve 2.18, clean 0.3

### Rejection Block
- Session VWAP with Standard Deviation Bands: biases, improve 2.23, clean 0.32 (review)
- Universal Signal Backtester [LuxAlgo]: manages_risk, improve 2.08, clean 0.4 (review)
- Time-Series Momentum (Trend Following): biases, improve 2.25, clean 0.27
- Anchored VWAP (manual and auto-anchored): confirms, improve 1.99, clean 0.41 (review)
- SuperTrend AI (Clustering) [LuxAlgo]: manages_risk, improve 2.04, clean 0.37 (review)

### Propulsion Block
- Fair Value Gap [LuxAlgo]: confirms, improve 2.09, clean 0.48 (review)
- Universal Signal Backtester [LuxAlgo]: manages_risk, improve 2.03, clean 0.44 (review)
- Session VWAP with Standard Deviation Bands: biases, improve 2.14, clean 0.36 (review)
- Time-Series Momentum (Trend Following): biases, improve 2.22, clean 0.26
- ICT Concepts [LuxAlgo]: locates, improve 2.33, clean 0.2 (review)

### Buy-side / Sell-side Liquidity (BSL / SSL; liquidity pools; draw on liquidity)
- Fair Value Gap [LuxAlgo]: locates, improve 2.21, clean 0.54 (review)
- Session VWAP with Standard Deviation Bands: biases, improve 2.3, clean 0.43 (review)
- Time-Series Momentum (Trend Following): biases, improve 2.4, clean 0.35 (review)
- Intraday Momentum 'Noise Area' Breakout (Beat the Market): filters, improve 2.21, clean 0.46 (review)
- Universal Signal Backtester [LuxAlgo]: manages_risk, improve 2.1, clean 0.52 (review)

### Equal Highs / Equal Lows (EQH/EQL; relative equal highs/lows)
- Universal Signal Backtester [LuxAlgo]: manages_risk, improve 2.17, clean 0.49 (review)
- Fair Value Gap [LuxAlgo]: confirms, improve 2.01, clean 0.55 (review)
- Session VWAP with Standard Deviation Bands: biases, improve 2.19, clean 0.38 (review)
- SuperTrend AI (Clustering) [LuxAlgo]: manages_risk, improve 2.1, clean 0.43 (review)
- LuxAlgo Backtesters (S&O / PAC / OSC) and LUCID: manages_risk, improve 2.02, clean 0.44 (review)

### Liquidity Sweep (stop hunt, stop run, raid, liquidity grab; swing failure)
- Session VWAP with Standard Deviation Bands: biases, improve 2.27, clean 0.77 (review)
- Fair Value Gap [LuxAlgo]: locates, improve 2.2, clean 0.75 (review)
- ATR Exceedance Probability Model [LuxAlgo]: filters, improve 2.1, clean 0.76
- Volatility Regime / Volatility Targeting: manages_risk, improve 2.16, clean 0.71
- Time-Series Momentum (Trend Following): biases, improve 2.18, clean 0.69 (review)

### Internal vs External Range Liquidity (IRL / ERL)
- Fair Value Gap [LuxAlgo]: locates, improve 2.32, clean 0.54 (review)
- Liquidity Voids (FVG) [LuxAlgo]: locates, improve 2.25, clean 0.44 (review)
- Session VWAP with Standard Deviation Bands: biases, improve 2.18, clean 0.4 (review)
- Universal Signal Backtester [LuxAlgo]: manages_risk, improve 2.07, clean 0.45 (review)
- ICT Concepts [LuxAlgo]: locates, improve 2.41, clean 0.17

### Previous Day / Week High & Low (PDH/PDL, PWH/PWL; also previous month)
- Session VWAP with Standard Deviation Bands: biases, improve 2.2, clean 0.86
- Time-Series Momentum (Trend Following): biases, improve 2.23, clean 0.75
- Chandelier Exit: manages_risk, improve 1.99, clean 0.84
- Volatility Regime / Volatility Targeting: manages_risk, improve 2.1, clean 0.74
- Supertrend: manages_risk, improve 1.93, clean 0.88

### Session Highs/Lows (Asian range, London high/low, NY session liquidity)
- Session VWAP with Standard Deviation Bands: biases, improve 2.23, clean 0.83
- Intraday Momentum 'Noise Area' Breakout (Beat the Market): times, improve 2.23, clean 0.77 (review)
- Time-Series Momentum (Trend Following): biases, improve 2.23, clean 0.66 (review)
- Chandelier Exit: manages_risk, improve 2.0, clean 0.83
- Supertrend: manages_risk, improve 1.95, clean 0.87

### Premium / Discount & Equilibrium (dealing range)
- Session VWAP with Standard Deviation Bands: biases, improve 2.12, clean 0.44 (review)
- Chandelier Exit: manages_risk, improve 2.05, clean 0.47 (review)
- Universal Signal Backtester [LuxAlgo]: manages_risk, improve 2.08, clean 0.41 (review)
- Time-Series Momentum (Trend Following): biases, improve 2.2, clean 0.33 (review)
- LuxAlgo Price Action Concepts - Market Structure (CHoCH/CHoCH+/BOS): locates, improve 2.39, clean 0.2 (review)

### Optimal Trade Entry (OTE; 62-79% Fibonacci zone)
- Session VWAP with Standard Deviation Bands: biases, improve 2.22, clean 0.46 (review)
- Chandelier Exit: manages_risk, improve 2.04, clean 0.5 (review)
- Universal Signal Backtester [LuxAlgo]: manages_risk, improve 2.0, clean 0.51 (review)
- Volatility Regime / Volatility Targeting: manages_risk, improve 2.17, clean 0.38 (review)
- Buyside & Sellside Liquidity [LuxAlgo]: locates, improve 2.33, clean 0.28 (review)

### Standard Deviation Projections (range multiples; STDV)
- Volatility Regime / Volatility Targeting: manages_risk, improve 2.08, clean 0.74
- Chandelier Exit: manages_risk, improve 1.96, clean 0.81
- Supertrend: manages_risk, improve 1.91, clean 0.85
- Session VWAP with Standard Deviation Bands: confirms, improve 1.94, clean 0.81 (review)
- Time-Series Momentum (Trend Following): biases, improve 2.08, clean 0.68 (review)

### Central Bank Dealers Range (CBDR), Asian Range & Flout
- Volatility Regime / Volatility Targeting: manages_risk, improve 2.17, clean 0.68 (review)
- Chandelier Exit: manages_risk, improve 1.95, clean 0.78
- Supertrend: manages_risk, improve 1.87, clean 0.8
- Universal Signal Backtester [LuxAlgo]: manages_risk, improve 2.06, clean 0.63 (review)
- Time-Series Momentum (Trend Following): biases, improve 2.06, clean 0.63 (review)

### Killzones (Asia, London Open, NY AM/Open, London Close, NY PM)
- Intraday Momentum 'Noise Area' Breakout (Beat the Market): times, improve 2.51, clean 0.74 (review)
- Session VWAP with Standard Deviation Bands: biases, improve 2.43, clean 0.79
- Fair Value Gap [LuxAlgo]: locates, improve 2.31, clean 0.83 (review)
- Market Intraday Momentum (first half-hour predicts last half-hour): biases, improve 2.16, clean 0.81
- ATR Exceedance Probability Model [LuxAlgo]: filters, improve 2.16, clean 0.79

### ICT Macros (algorithmic time windows)
- Intraday Momentum 'Noise Area' Breakout (Beat the Market): confirms, improve 2.47, clean 0.74 (review)
- Fair Value Gap [LuxAlgo]: confirms, improve 2.31, clean 0.8 (review)
- Session VWAP with Standard Deviation Bands: biases, improve 2.29, clean 0.78 (review)
- Liquidity Voids (FVG) [LuxAlgo]: locates, improve 2.17, clean 0.74 (review)
- Chandelier Exit: manages_risk, improve 2.04, clean 0.82

### Midnight Open / True Day Open (and 8:30 / 9:30 opens; time anchors)
- Session VWAP with Standard Deviation Bands: biases, improve 2.28, clean 0.77 (review)
- Intraday Momentum 'Noise Area' Breakout (Beat the Market): filters, improve 2.35, clean 0.63 (review)
- Fair Value Gap [LuxAlgo]: locates, improve 2.18, clean 0.75 (review)
- Chandelier Exit: manages_risk, improve 2.05, clean 0.74
- ATR Exceedance Probability Model [LuxAlgo]: filters, improve 2.07, clean 0.71

### ICT Silver Bullet
- Session VWAP with Standard Deviation Bands: biases, improve 2.05, clean 0.5 (review)
- Chandelier Exit: manages_risk, improve 1.97, clean 0.52 (review)
- LuxAlgo Backtesters (S&O / PAC / OSC) and LUCID: manages_risk, improve 2.02, clean 0.42 (review)
- Universal Signal Backtester [LuxAlgo]: manages_risk, improve 1.92, clean 0.48 (review)
- Anchored VWAP (manual and auto-anchored): confirms, improve 1.94, clean 0.46 (review)

### Judas Swing (false open move)
- Session VWAP with Standard Deviation Bands: biases, improve 2.17, clean 0.4 (review)
- Universal Signal Backtester [LuxAlgo]: manages_risk, improve 2.01, clean 0.46 (review)
- Fair Value Gap [LuxAlgo]: confirms, improve 2.11, clean 0.37 (review)
- Buyside & Sellside Liquidity [LuxAlgo]: locates, improve 2.35, clean 0.23
- Chandelier Exit: manages_risk, improve 2.03, clean 0.4 (review)

### Power of Three / AMD (Accumulation-Manipulation-Distribution; PO3)
- Fair Value Gap [LuxAlgo]: locates, improve 2.24, clean 0.56 (review)
- Session VWAP with Standard Deviation Bands: biases, improve 2.14, clean 0.49 (review)
- Intraday Momentum 'Noise Area' Breakout (Beat the Market): times, improve 2.21, clean 0.43 (review)
- Chandelier Exit: manages_risk, improve 2.02, clean 0.5 (review)
- ATR Exceedance Probability Model [LuxAlgo]: filters, improve 2.04, clean 0.48 (review)

### Daily Bias (with next-day close rules)
- Session VWAP with Standard Deviation Bands: confirms, improve 2.22, clean 0.8 (review)
- Volatility Regime / Volatility Targeting: manages_risk, improve 2.2, clean 0.79
- Time-Series Momentum (Trend Following): biases, improve 2.14, clean 0.78
- Intraday Momentum 'Noise Area' Breakout (Beat the Market): times, improve 2.12, clean 0.74 (review)
- Floor Pivot Points (Traditional, Fibonacci, Woodie, Classic, DeMark, Camarilla): locates, improve 1.98, clean 0.8

### SMT Divergence (Smart Money Technique / Tool; crack in correlation)
- Universal Signal Backtester [LuxAlgo]: manages_risk, improve 2.02, clean 0.53 (review)
- Volatility Regime / Volatility Targeting: manages_risk, improve 2.09, clean 0.45 (review)
- Chandelier Exit: manages_risk, improve 1.89, clean 0.52 (review)
- LuxAlgo Backtesters (S&O / PAC / OSC) and LUCID: manages_risk, improve 1.9, clean 0.5 (review)
- Session VWAP with Standard Deviation Bands: confirms, improve 1.9, clean 0.49 (review)

### IPDA Data Ranges (20/40/60-day look-back; quarterly shifts)
- Volatility Regime / Volatility Targeting: manages_risk, improve 2.23, clean 0.78
- Time-Series Momentum (Trend Following): biases, improve 2.12, clean 0.75
- Intraday Momentum 'Noise Area' Breakout (Beat the Market): times, improve 2.06, clean 0.74 (review)
- Fair Value Gap [LuxAlgo]: times, improve 2.02, clean 0.77 (review)
- ATR Exceedance Probability Model [LuxAlgo]: filters, improve 2.02, clean 0.77

### ICT 2022 Mentorship Model (2022 model)
- Volatility Regime / Volatility Targeting: manages_risk, improve 2.27, clean 0.53 (review)
- Session VWAP with Standard Deviation Bands: locates, improve 2.18, clean 0.56 (review)
- Universal Signal Backtester [LuxAlgo]: manages_risk, improve 1.94, clean 0.58 (review)
- Time-Series Momentum (Trend Following): biases, improve 2.04, clean 0.49 (review)
- ATR Exceedance Probability Model [LuxAlgo]: filters, improve 2.0, clean 0.47 (review)

### Turtle Soup (ICT liquidity-sweep reversal; Raschke/Connors origin)
- Volatility Regime / Volatility Targeting: manages_risk, improve 2.24, clean 0.75
- Session VWAP with Standard Deviation Bands: confirms, improve 2.0, clean 0.76 (review)
- ATR Exceedance Probability Model [LuxAlgo]: filters, improve 1.99, clean 0.73
- Fair Value Gap [LuxAlgo]: locates, improve 1.95, clean 0.74 (review)
- Bollinger Bands (with %b and BandWidth): filters, improve 1.91, clean 0.74

### Unicorn Model (breaker + FVG overlap)
- Volatility Regime / Volatility Targeting: manages_risk, improve 2.25, clean 0.43 (review)
- Session VWAP with Standard Deviation Bands: locates, improve 2.05, clean 0.55 (review)
- Universal Signal Backtester [LuxAlgo]: manages_risk, improve 1.88, clean 0.56 (review)
- Chandelier Exit: manages_risk, improve 1.89, clean 0.5 (review)
- Anchored VWAP (manual and auto-anchored): confirms, improve 1.93, clean 0.46 (review)

### Market Maker Buy/Sell Models (MMBM / MMSM; MMXM)
- Buyside & Sellside Liquidity [LuxAlgo]: locates, improve 2.45, clean 0.15
- Fair Value Gap [LuxAlgo]: locates, improve 2.03, clean 0.32 (review)
- Range Detector [LuxAlgo]: locates, improve 2.31, clean 0.15
- Universal Signal Backtester [LuxAlgo]: manages_risk, improve 2.11, clean 0.25
- kNN Market Architecture [LuxAlgo]: locates, improve 2.25, clean 0.16 (review)
