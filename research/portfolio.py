"""Stage 5: combine validated edges into one portfolio with volatility targeting.

Each component's daily P&L is scaled so its trailing 60-day volatility (known before the day) matches the same
dollar target, then components are summed. Reports per-component and portfolio Sharpe, max drawdown and the
correlation matrix of daily P&L. Scaling uses only past data (no look-ahead); contracts are fractional here,
in practice round to MNQ/MES micros (1/10 size).
"""
import math

import numpy as np
import pandas as pd

from wf import PERIODS, data, evaluate, slice_period


def all_days(root, period):
    df = slice_period(data(root), period)
    return pd.Index(sorted(pd.to_datetime(df["time"], unit="s", utc=True).dt.tz_convert("America/New_York").dt.date.unique()))


def vol_target(daily, target=1000.0, window=60, cap=3.0):
    vol = daily.rolling(window, min_periods=20).std().shift(1)
    scale = (target / vol).clip(upper=cap).fillna(1.0)
    return daily * scale


def combine(components, period="VAL", target=1000.0):
    """components: list of (name, P, root). Returns (summary DataFrame, correlation DataFrame, portfolio daily)."""
    cols = {}
    for name, p, root in components:
        st = evaluate(p, root, period)
        days = all_days(root, period)
        d = st["daily"].reindex(days, fill_value=0.0)
        cols[f"{name} {root}"] = vol_target(d, target)
    m = pd.DataFrame(cols).fillna(0.0)
    m["PORTFOLIO"] = m.sum(axis=1)
    rows = []
    for c in m.columns:
        x = m[c]
        eq = x.cumsum()
        sr = x.mean() / x.std() * math.sqrt(252) if x.std() > 0 else 0.0
        rows.append(dict(component=c, sharpe=round(sr, 2), net=round(x.sum()), max_dd=round((eq.cummax() - eq).max()),
                         pos_years=f"{(x.groupby(pd.Index([d.year for d in x.index])).sum() > 0).sum()}/"
                                   f"{len(set(d.year for d in x.index))}"))
    return pd.DataFrame(rows), m.drop(columns="PORTFOLIO").corr().round(2), m["PORTFOLIO"]
