# Botmax v0 walk-forward report

Data: `nq_5m_lse.csv`, 724818 bars, 2016-05-29 -> 2026-09-28. Roll days skipped: 84.
Walk-forward: train 365 days, test 90 days, min 10 train trades. Grid: 36 combinations (mss_window [15, 25, 40], max_stop_atr [3.0, 6.0], rr [1.5, 2.0, 3.0], bias ['off', 'tsmom']).

## Out-of-sample (the number that matters)

| | trades | net $ | win rate | PF | avg $ | max DD $ | p(mean <= 0) |
|---|---|---|---|---|---|---|---|
| walk-forward pick | 216 | -17347.0 | 0.343 | 0.87 | -80.31 | 33738.5 | 0.7943 |
| fixed defaults | 167 | -1491.5 | 0.359 | 0.98 | -8.93 | 17024.5 | 0.535 |

p(mean <= 0) is a bootstrap estimate; below 0.05 is weak evidence of an edge, and only if it also holds on data we have not looked at yet.

## Folds

| test window | picked | train net $ | test trades | test net $ |
|---|---|---|---|---|
| 2017-05-31 -> 2017-08-29 | {'mss_window': 15, 'max_stop_atr': 6.0, 'rr': 2.0, 'bias': 'off'} | 2232.5 | 8 | 699.0 |
| 2017-08-29 -> 2017-11-27 | {'mss_window': 40, 'max_stop_atr': 6.0, 'rr': 3.0, 'bias': 'off'} | 2862.0 | 8 | -686.0 |
| 2017-11-27 -> 2018-02-25 | {'mss_window': 40, 'max_stop_atr': 6.0, 'rr': 3.0, 'bias': 'off'} | 2843.0 | 7 | 3123.5 |
| 2018-02-25 -> 2018-05-26 | {'mss_window': 40, 'max_stop_atr': 6.0, 'rr': 3.0, 'bias': 'tsmom'} | 4619.5 | 2 | -724.0 |
| 2018-05-26 -> 2018-08-24 | {'mss_window': 40, 'max_stop_atr': 6.0, 'rr': 3.0, 'bias': 'tsmom'} | 3450.0 | 3 | -808.5 |
| 2018-08-24 -> 2018-11-22 | {'mss_window': 40, 'max_stop_atr': 6.0, 'rr': 3.0, 'bias': 'off'} | 1763.0 | 4 | 882.0 |
| 2018-11-22 -> 2019-02-20 | {'mss_window': 40, 'max_stop_atr': 6.0, 'rr': 3.0, 'bias': 'off'} | 3331.0 | 9 | -1940.5 |
| 2019-02-20 -> 2019-05-21 | {'mss_window': 40, 'max_stop_atr': 6.0, 'rr': 1.5, 'bias': 'off'} | 605.0 | 13 | 1076.5 |
| 2019-05-21 -> 2019-08-19 | {'mss_window': 40, 'max_stop_atr': 6.0, 'rr': 3.0, 'bias': 'off'} | 2641.0 | 5 | -17.5 |
| 2019-08-19 -> 2019-11-17 | {'mss_window': 40, 'max_stop_atr': 6.0, 'rr': 3.0, 'bias': 'off'} | 1470.0 | 10 | 1380.0 |
| 2019-11-17 -> 2020-02-15 | {'mss_window': 25, 'max_stop_atr': 3.0, 'rr': 2.0, 'bias': 'off'} | 3251.0 | 8 | -376.0 |
| 2020-02-15 -> 2020-05-15 | {'mss_window': 25, 'max_stop_atr': 6.0, 'rr': 3.0, 'bias': 'off'} | 5402.5 | 8 | -986.0 |
| 2020-05-15 -> 2020-08-13 | {'mss_window': 25, 'max_stop_atr': 3.0, 'rr': 3.0, 'bias': 'off'} | 7762.0 | 5 | -472.5 |
| 2020-08-13 -> 2020-11-11 | {'mss_window': 25, 'max_stop_atr': 3.0, 'rr': 2.0, 'bias': 'off'} | 6838.0 | 2 | -269.0 |
| 2020-11-11 -> 2021-02-09 | {'mss_window': 25, 'max_stop_atr': 3.0, 'rr': 2.0, 'bias': 'off'} | 3420.5 | 4 | 4247.0 |
| 2021-02-09 -> 2021-05-10 | {'mss_window': 25, 'max_stop_atr': 3.0, 'rr': 2.0, 'bias': 'off'} | 7589.0 | 8 | -496.0 |
| 2021-05-10 -> 2021-08-08 | {'mss_window': 15, 'max_stop_atr': 3.0, 'rr': 1.5, 'bias': 'off'} | 7653.0 | 2 | -1134.0 |
| 2021-08-08 -> 2021-11-06 | {'mss_window': 40, 'max_stop_atr': 6.0, 'rr': 1.5, 'bias': 'off'} | 10904.5 | 9 | -9645.5 |
| 2021-11-06 -> 2022-02-04 | {'mss_window': 40, 'max_stop_atr': 6.0, 'rr': 1.5, 'bias': 'tsmom'} | 1175.5 | 7 | -6361.5 |
| 2022-02-04 -> 2022-05-05 | {'mss_window': 15, 'max_stop_atr': 3.0, 'rr': 2.0, 'bias': 'off'} | 115.0 | 3 | 2501.5 |
| 2022-05-05 -> 2022-08-03 | {'mss_window': 15, 'max_stop_atr': 3.0, 'rr': 2.0, 'bias': 'off'} | 838.5 | 7 | -6091.5 |
| 2022-08-03 -> 2022-11-01 | {'mss_window': 15, 'max_stop_atr': 3.0, 'rr': 2.0, 'bias': 'off'} | -4119.0 | 0 | 0.0 |
| 2022-11-01 -> 2023-01-30 | {'mss_window': 40, 'max_stop_atr': 3.0, 'rr': 3.0, 'bias': 'off'} | 4467.5 | 4 | 5897.0 |
| 2023-01-30 -> 2023-04-30 | {'mss_window': 15, 'max_stop_atr': 6.0, 'rr': 3.0, 'bias': 'off'} | 14805.5 | 8 | -1931.0 |
| 2023-04-30 -> 2023-07-29 | {'mss_window': 25, 'max_stop_atr': 6.0, 'rr': 3.0, 'bias': 'off'} | 5644.0 | 9 | 1719.5 |
| 2023-07-29 -> 2023-10-27 | {'mss_window': 25, 'max_stop_atr': 6.0, 'rr': 3.0, 'bias': 'off'} | 12184.0 | 7 | -1316.5 |
| 2023-10-27 -> 2024-01-25 | {'mss_window': 25, 'max_stop_atr': 6.0, 'rr': 2.0, 'bias': 'off'} | 6900.5 | 11 | -2359.5 |
| 2024-01-25 -> 2024-04-24 | {'mss_window': 25, 'max_stop_atr': 6.0, 'rr': 2.0, 'bias': 'tsmom'} | 4178.5 | 1 | -664.5 |
| 2024-04-24 -> 2024-07-23 | {'mss_window': 25, 'max_stop_atr': 6.0, 'rr': 2.0, 'bias': 'tsmom'} | 2481.5 | 3 | 166.5 |
| 2024-07-23 -> 2024-10-21 | {'mss_window': 25, 'max_stop_atr': 6.0, 'rr': 1.5, 'bias': 'tsmom'} | -519.0 | 3 | -968.5 |
| 2024-10-21 -> 2025-01-19 | {'mss_window': 25, 'max_stop_atr': 3.0, 'rr': 1.5, 'bias': 'off'} | 508.5 | 4 | -1453.0 |
| 2025-01-19 -> 2025-04-19 | {'mss_window': 25, 'max_stop_atr': 3.0, 'rr': 3.0, 'bias': 'off'} | 3373.5 | 6 | 1703.0 |
| 2025-04-19 -> 2025-07-18 | {'mss_window': 40, 'max_stop_atr': 3.0, 'rr': 2.0, 'bias': 'tsmom'} | 12140.5 | 4 | -3683.0 |
| 2025-07-18 -> 2025-10-16 | {'mss_window': 25, 'max_stop_atr': 3.0, 'rr': 2.0, 'bias': 'tsmom'} | 11276.0 | 3 | -1458.5 |
| 2025-10-16 -> 2026-01-14 | {'mss_window': 25, 'max_stop_atr': 3.0, 'rr': 2.0, 'bias': 'tsmom'} | 6022.0 | 5 | -6067.5 |
| 2026-01-14 -> 2026-04-14 | {'mss_window': 25, 'max_stop_atr': 3.0, 'rr': 1.5, 'bias': 'off'} | 6775.0 | 9 | 134.5 |
| 2026-04-14 -> 2026-07-13 | {'mss_window': 15, 'max_stop_atr': 3.0, 'rr': 1.5, 'bias': 'off'} | 2422.0 | 4 | 8447.0 |
| 2026-07-13 -> 2026-09-28 | {'mss_window': 15, 'max_stop_atr': 6.0, 'rr': 1.5, 'bias': 'off'} | 14338.5 | 3 | 586.5 |

## Fixed defaults by year (whole history)

| year | trades | net $ |
|---|---|---|
| 2016 | 6 | 413.0 |
| 2017 | 12 | 571.0 |
| 2018 | 15 | -6127.5 |
| 2019 | 19 | 3224.5 |
| 2020 | 18 | 3469.0 |
| 2021 | 17 | -3941.5 |
| 2022 | 16 | 7183.0 |
| 2023 | 18 | -3316.0 |
| 2024 | 16 | -5412.0 |
| 2025 | 21 | -3659.5 |
| 2026 | 18 | 6244.0 |

## In-sample, full history (optimistic, for context only)

Best combination over everything: {'mss_window': 25, 'max_stop_atr': 3.0, 'rr': 1.5, 'bias': 'off'} -> {'trades': 189, 'net': 12584.5, 'win_rate': 0.45, 'pf': 1.14, 'avg': 66.58, 'max_dd': 14776.0}. Picking the best of 36 after the fact overstates the edge; compare with the out-of-sample row.
