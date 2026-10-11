"""Stitch quarterly contract CSVs from tools/tv_contracts.mjs into one back-adjusted continuous 5m series.

Each contract is used from the previous contract's roll to its own roll, rolling ROLL_DAYS calendar days before
its last bar (= expiry, CME's usual roll week). Older segments are shifted additively by the price gap between
the two contracts at the roll bar (TradingView "B-ADJ" style), so intraday ranges and tick sizes are unchanged.
The raw (unadjusted) close is kept in `raw_close` and the contract in `contract`.

Usage: python tools/stitch_contracts.py NQ    -> data/nq_5m_tv_stitched.csv
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "tv_contracts"
ROLL_DAYS = 8
MONTH = {"H": 3, "M": 6, "U": 9, "Z": 12}


def main(root):
    files = sorted(SRC.glob(f"{root}[HMUZ]20[0-9][0-9].csv"), key=lambda f: (int(f.stem[-4:]), MONTH[f.stem[len(root)]]))
    cons = []
    for f in files:
        df = pd.read_csv(f).drop_duplicates("time").sort_values("time")
        if len(df) < 100:
            continue
        df["contract"] = f.stem
        cons.append(df)
    segs, prev_roll = [], None
    for k, df in enumerate(cons):
        roll = df["time"].iloc[-1] - ROLL_DAYS * 86400
        lo = prev_roll if prev_roll is not None else df["time"].iloc[0] - 1
        seg = df[(df["time"] > lo) & (df["time"] <= roll)].copy() if k < len(cons) - 1 else df[df["time"] > lo].copy()
        segs.append(seg)
        prev_roll = roll
    # back-adjust: walk from the newest segment backwards, shifting older ones by the roll gap
    adj = 0.0
    for k in range(len(segs) - 1, 0, -1):
        old, new_c = segs[k - 1], cons[k]
        t_roll = old["time"].iloc[-1]
        new_px = new_c.loc[new_c["time"] <= t_roll, "close"]
        gap = (new_px.iloc[-1] - old["close"].iloc[-1]) if len(new_px) else 0.0
        adj += gap
        segs[k - 1] = old.assign(**{c: old[c] + adj for c in ("open", "high", "low", "close")}, raw_close=old["close"])
    segs[-1] = segs[-1].assign(raw_close=segs[-1]["close"])
    out = pd.concat(segs).sort_values("time").drop_duplicates("time")
    path = ROOT / "data" / f"{root.lower()}_5m_tv_stitched.csv"
    out.to_csv(path, index=False)
    t = pd.to_datetime(out["time"], unit="s")
    gaps = (t.diff().dt.days > 5).sum()
    print(f"{path.name}: {len(out)} bars, {t.iloc[0].date()} -> {t.iloc[-1].date()}, "
          f"{len(segs)} contracts, total back-adjustment {adj:+.2f} pts, gaps > 5 days: {gaps}")


if __name__ == "__main__":
    main(sys.argv[1])
