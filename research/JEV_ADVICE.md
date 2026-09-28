# Jev advice for Botmax

**Do first:** `more_data` (confidence 0.69)

Distribution: more_data 0.72, wider_mss 0.15, vwap_trend 0.05, vwap_fade 0.02, tsmom_bias 0.02, atr_regime 0.01, fvg_any_time 0.01, london_window 0.01, fvg_stop 0.01, trail_exit 0.00

| # | change | gain 0-3 | step | overfit risk | top reasons (p) |
|---|---|---|---|---|---|
| 1 | more_data | 2.06 | sample_size | 0.72 | fits_ict_logic 0.81, more_trades 0.8, cuts_drawdown 0.55, evidence_based 0.53 |
| 2 | vwap_fade | 1.75 | setup_quality | 0.88 | fits_ict_logic 0.63, cuts_drawdown 0.54 |
| 3 | vwap_trend | 1.59 | setup_quality | 0.87 | fits_ict_logic 0.62, cuts_drawdown 0.56, evidence_based 0.5 |
| 4 | atr_regime | 1.55 | setup_quality | 0.84 | fits_ict_logic 0.59, cuts_drawdown 0.58, evidence_based 0.57 |
| 5 | tsmom_bias | 1.54 | setup_quality | 0.86 | fits_ict_logic 0.58, cuts_drawdown 0.54 |
| 6 | trail_exit | 1.23 | exit_risk | 0.86 | fits_ict_logic 0.6, cuts_drawdown 0.58 |
| 7 | fvg_stop | 1.0 | exit_risk | 0.87 |  |
| 8 | fvg_any_time | 0.92 | setup_frequency | 0.87 | fits_ict_logic 0.5 |
| 9 | london_window | 0.44 | sample_size | 0.87 | fits_ict_logic 0.57 |
| 10 | wider_mss | 0.26 | setup_frequency | 0.88 | fixes_bottleneck 0.55 |
