"""Walk-forward test of Botmax v0 on long 5m history, no TradingView needed.

Jev's #1 advice (JEV_ADVICE.md, more_data): test the exact rules on years of data and keep
TradingView only for final confirmation. This script is the honest version of that test:

  1. Run every grid combination once over the full history (engine.py, TradingView parity).
  2. Walk forward: for each fold, pick the best combination on the previous TRAIN days only,
     then record its trades in the next TEST days. Stitched test trades = out-of-sample result.
  3. Report the out-of-sample result next to the fixed defaults, with a bootstrap p-value and
     the number of combinations tried (the more we try, the more luck can look like an edge).

Trades on contract roll days (and the day after, whose PDH/PDL come from the old contract) are
dropped, because stitched futures jump at the roll.

Usage: python research/wf.py [csv] [--train 180] [--test 60] [--min-trades 15]
  csv: time (UTC seconds), open, high, low, close [, contract]; default data/nq_5m_ibkr.csv
Writes research/WF_REPORT.md and data/wf_oos_trades.csv.
"""
import argparse
import itertools
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from engine import NY, Params, run

ROOT = Path(__file__).resolve().parent.parent
DAY = 86400

# Small on purpose: every extra combination is another chance to fit noise.
GRID = {
    "mss_window": [15, 25, 40],
    "max_stop_atr": [3.0, 6.0],
    "rr": [1.5, 2.0, 3.0],
    "bias": ["off", "tsmom"],
}


def load(path):
    df = pd.read_csv(path)
    df = df.sort_values("time").drop_duplicates("time").reset_index(drop=True)
    return df


def roll_days(df):
    """Trading days (CME, starting 18:00 NY) on which the contract changes, plus the day after."""
    if "contract" not in df:
        return set()
    t = pd.to_datetime(df["time"], unit="s", utc=True).dt.tz_convert(NY)
    tday = (t + pd.Timedelta(hours=6)).dt.date
    days = sorted(set(tday))
    idx = {d: k for k, d in enumerate(days)}
    out = set()
    for d in tday[df["contract"] != df["contract"].shift(1)].iloc[1:]:
        out.add(d)
        if idx[d] + 1 < len(days):
            out.add(days[idx[d] + 1])
    return out


def trades_for(df, p, skip):
    t = pd.DataFrame(run(df[["time", "open", "high", "low", "close"]], p).trades)
    if t.empty:
        return t
    et = pd.to_datetime(t["entry_time"], unit="s", utc=True).dt.tz_convert(NY)
    t["tday"] = (et + pd.Timedelta(hours=6)).dt.date
    return t[~t["tday"].isin(skip)].reset_index(drop=True)


def stats(t):
    if t is None or t.empty:
        return dict(trades=0, net=0.0, win_rate=None, pf=None, avg=None, max_dd=0.0)
    pnl = t["pnl"].astype(float)
    wins, losses = pnl[pnl > 0].sum(), -pnl[pnl <= 0].sum()
    eq = pnl.cumsum()
    return dict(trades=len(t), net=round(pnl.sum(), 2), win_rate=round((pnl > 0).mean(), 3),
                pf=round(wins / losses, 2) if losses > 0 else None, avg=round(pnl.mean(), 2),
                max_dd=round((eq.cummax() - eq).max(), 2))


def bootstrap_p(pnl, n=10000, seed=0):
    """P(mean trade <= 0) under resampling: small = the edge is unlikely to be pure luck."""
    pnl = np.asarray(pnl, dtype=float)
    if len(pnl) < 2:
        return None
    rng = np.random.default_rng(seed)
    means = rng.choice(pnl, size=(n, len(pnl)), replace=True).mean(axis=1)
    return round(float((means <= 0).mean()), 4)


def score(t, min_trades):
    """Selection metric on the train window: net $, only if there are enough trades."""
    if t.empty or len(t) < min_trades:
        return -np.inf
    return t["pnl"].sum()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="?", default=str(ROOT / "data" / "nq_5m_ibkr.csv"))
    ap.add_argument("--train", type=int, default=180, help="train window, calendar days")
    ap.add_argument("--test", type=int, default=60, help="test window, calendar days")
    ap.add_argument("--min-trades", type=int, default=15, help="min train trades to be selectable")
    ap.add_argument("--report", default=str(ROOT / "research" / "WF_REPORT.md"))
    a = ap.parse_args()

    df = load(a.csv)
    skip = roll_days(df)
    t0, t1 = int(df["time"].iloc[0]), int(df["time"].iloc[-1])
    span = f"{pd.to_datetime(t0, unit='s', utc=True).date()} -> {pd.to_datetime(t1, unit='s', utc=True).date()}"
    print(f"{len(df)} bars, {span}, {len(skip)} roll days skipped")

    keys = list(GRID)
    combos = [dict(zip(keys, v)) for v in itertools.product(*GRID.values())]
    runs = {}
    for k, c in enumerate(combos, 1):
        runs[k - 1] = trades_for(df, replace(Params(), **c), skip)
        print(f"  [{k}/{len(combos)}] {c}: {stats(runs[k - 1])['trades']} trades", flush=True)
    default = trades_for(df, Params(), skip)

    def window(t, lo, hi):
        return t if t.empty else t[(t["entry_time"] >= lo) & (t["entry_time"] < hi)]

    folds, oos = [], []
    start = t0 + 2 * DAY                          # warm-up for levels, pivots, ATR
    lo = start + a.train * DAY
    while lo < t1:
        hi = min(lo + a.test * DAY, t1 + 1)
        scores = {k: score(window(t, lo - a.train * DAY, lo), a.min_trades) for k, t in runs.items()}
        best = max(scores, key=scores.get)
        if np.isfinite(scores[best]):
            got = window(runs[best], lo, hi).assign(combo=best)
            oos.append(got)
            s = stats(got)
        else:
            best, s = None, dict(trades=0, net=0.0)
        folds.append(dict(test=f"{pd.to_datetime(lo, unit='s').date()} -> {pd.to_datetime(hi, unit='s').date()}",
                          combo=combos[best] if best is not None else "none (too few train trades)",
                          train_net=round(scores[best], 2) if best is not None else None, **s))
        lo = hi

    oos = pd.concat(oos, ignore_index=True) if oos else pd.DataFrame()
    first_test = start + a.train * DAY
    base = window(default, first_test, t1 + 1)
    full = {k: stats(t) for k, t in runs.items()}
    best_full = max(full, key=lambda k: full[k]["net"])

    o, b = stats(oos), stats(base)
    lines = [
        "# Botmax v0 walk-forward report", "",
        f"Data: `{Path(a.csv).name}`, {len(df)} bars, {span}. Roll days skipped: {len(skip)}.",
        f"Walk-forward: train {a.train} days, test {a.test} days, min {a.min_trades} train trades. "
        f"Grid: {len(combos)} combinations ({', '.join(f'{k} {v}' for k, v in GRID.items())}).", "",
        "## Out-of-sample (the number that matters)", "",
        "| | trades | net $ | win rate | PF | avg $ | max DD $ | p(mean <= 0) |", "|---|---|---|---|---|---|---|---|",
        f"| walk-forward pick | {o['trades']} | {o['net']} | {o['win_rate']} | {o['pf']} | {o['avg']} | {o['max_dd']} | "
        f"{bootstrap_p(oos['pnl']) if len(oos) else None} |",
        f"| fixed defaults | {b['trades']} | {b['net']} | {b['win_rate']} | {b['pf']} | {b['avg']} | {b['max_dd']} | "
        f"{bootstrap_p(base['pnl']) if len(base) else None} |", "",
        "p(mean <= 0) is a bootstrap estimate; below 0.05 is weak evidence of an edge, and only if it "
        "also holds on data we have not looked at yet.", "",
        "## Folds", "", "| test window | picked | train net $ | test trades | test net $ |", "|---|---|---|---|---|",
        *[f"| {f['test']} | {f['combo']} | {f['train_net']} | {f['trades']} | {f['net']} |" for f in folds], "",
        "## In-sample, full history (optimistic, for context only)", "",
        f"Best combination over everything: {combos[best_full]} -> {full[best_full]}. "
        f"Picking the best of {len(combos)} after the fact overstates the edge; compare with the out-of-sample row.", "",
    ]
    Path(a.report).write_text("\n".join(lines), encoding="utf-8")
    if len(oos):
        oos.to_csv(ROOT / "data" / "wf_oos_trades.csv", index=False)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
