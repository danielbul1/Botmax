"""Honest evaluation harness for Botmax candidates on the stitched multi-year 5m futures data.

Periods are fixed and must not be moved after seeing results:
  DISCOVERY  2011-01-01 .. 2019-12-31   free to search
  VALIDATE   2020-01-01 .. 2022-12-31   look only at configs chosen on DISCOVERY
  HOLDOUT    2023-01-01 .. end          touch once per idea, at the end (decision, not tuning)

For every config: trades, PF, net, max DD, per-year net, daily Sharpe (annualised), 2x-cost PF, and a
Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014) that discounts the best Sharpe by how many configs were tried.

Usage (module): from wf import evaluate, grid_report
"""
import math
from dataclasses import replace
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

import engine_v1 as v

ROOT = Path(__file__).resolve().parent.parent
PV = {"NQ": 20.0, "ES": 50.0}
PERIODS = {"DISC": ("2011-01-01", "2019-12-31"), "VAL": ("2020-01-01", "2022-12-31"), "HOLD": ("2023-01-01", "2100-01-01")}
N = NormalDist()
_DATA = {}


def data(root):
    if root not in _DATA:
        _DATA[root] = pd.read_csv(ROOT / "data" / f"{root.lower()}_5m_tv_stitched.csv")
    return _DATA[root]


def _ts(s):
    return int(pd.Timestamp(s, tz="America/New_York").timestamp())


def slice_period(df, period):
    a, b = PERIODS[period]
    return df[(df["time"] >= _ts(a)) & (df["time"] <= _ts(b) + 86400)]


def daily_pnl(trades):
    if not trades:
        return pd.Series(dtype=float)
    t = pd.DataFrame(trades)
    day = pd.to_datetime(t["exit_time"], unit="s", utc=True).dt.tz_convert("America/New_York").dt.date
    return t.groupby(day)["pnl"].sum()


def sharpe(daily, n_days):
    """Annualised Sharpe over all trading days in the window (no-trade days count as 0)."""
    if n_days < 2 or daily.empty:
        return 0.0
    x = np.zeros(n_days)
    x[: len(daily)] = daily.to_numpy()
    sd = x.std(ddof=1)
    return float(x.mean() / sd * math.sqrt(252)) if sd > 0 else 0.0


def deflated_sharpe(sr_ann, n_days, n_trials, sr_ann_all, skew=0.0, kurt=3.0):
    """Probability that the true Sharpe > 0 after picking the best of n_trials configs."""
    sr = sr_ann / math.sqrt(252)
    var_sr = np.var(np.asarray(sr_ann_all) / math.sqrt(252), ddof=1) if len(sr_ann_all) > 1 else 0.0
    g = 0.5772156649
    if n_trials > 1 and var_sr > 0:
        sr0 = math.sqrt(var_sr) * ((1 - g) * N.inv_cdf(1 - 1 / n_trials) + g * N.inv_cdf(1 - 1 / (n_trials * math.e)))
    else:
        sr0 = 0.0
    den = math.sqrt(max(1e-12, 1 - skew * sr + (kurt - 1) / 4 * sr * sr))
    return N.cdf((sr - sr0) * math.sqrt(max(n_days - 1, 1)) / den)


def evaluate(p, root, period="DISC", cost_mult=1.0):
    df = slice_period(data(root), period)
    if cost_mult != 1.0:
        p = replace(p, commission=p.commission * cost_mult, slippage_ticks=int(round(p.slippage_ticks * cost_mult)))
    if isinstance(p, v.P):
        trades = v.run(df, p, point_value=PV[root]).trades
    else:                                                  # edges.NA / edges.LHH
        import edges
        fn = {edges.NA: edges.run_na, edges.LHH: edges.run_lhh, edges.GAP: edges.run_gap}[type(p)]
        trades = fn(df, p, point_value=PV[root])
    st = v.stats(trades)
    days = pd.to_datetime(df["time"], unit="s", utc=True).dt.tz_convert("America/New_York").dt.date.nunique()
    dp = daily_pnl(trades)
    st["sharpe"] = round(sharpe(dp, days), 2)
    st["days"] = days
    if trades:
        t = pd.DataFrame(trades)
        yr = pd.to_datetime(t["entry_time"], unit="s").dt.year
        st["years"] = {int(k): int(x) for k, x in t.groupby(yr)["pnl"].sum().round().items()}
        st["pos_years"] = f"{sum(1 for x in st['years'].values() if x > 0)}/{len(st['years'])}"
    st["daily"] = dp
    return st


def grid_report(configs, roots=("NQ", "ES"), period="DISC"):
    """Run every (name, P) on every root; returns a DataFrame with DSR computed across the whole grid."""
    rows = []
    for name, p in configs:
        row = {"config": name}
        for r in roots:
            s = evaluate(p, r, period)
            row.update({f"{r}_n": s["n"], f"{r}_pf": s["pf"], f"{r}_net": s["net"], f"{r}_dd": s["dd"],
                        f"{r}_sr": s["sharpe"], f"{r}_years": s.get("pos_years"), f"{r}_days": s["days"]})
        rows.append(row)
    out = pd.DataFrame(rows)
    for r in roots:
        srs = out[f"{r}_sr"].tolist()
        out[f"{r}_dsr"] = [round(deflated_sharpe(s, d, len(srs), srs), 3) for s, d in zip(srs, out[f"{r}_days"])]
    return out


