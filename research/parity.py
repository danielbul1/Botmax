"""Check the Python engine against TradingView on the same bars (exported by tools/export_bars / bt.mjs)."""
import json
import sys
from pathlib import Path

import pandas as pd

from engine import Params, run, summarize

DATA = Path(__file__).resolve().parent.parent / "data"
tv = pd.read_csv(DATA / "tv_parity.csv")
bars = tv[["time", "open", "high", "low", "close"]]
warm = tv["time"].iloc[0] + 2 * 86400          # skip 2 days of warm-up (levels, pivots, ATR)

res = run(bars, Params())
py = {(e["time"], "sweep") for e in res.events if e["sweep"]} | {(e["time"], "mss") for e in res.events if e["mss"]}
tvs = set()
for _, r in tv.iterrows():
    if r["Sweep high"] == 1 or r["Sweep low"] == 1:
        tvs.add((r["time"], "sweep"))
    if r["MSS down"] == 1 or r["MSS up"] == 1:
        tvs.add((r["time"], "mss"))
py = {x for x in py if x[0] >= warm}
tvs = {x for x in tvs if x[0] >= warm}
print(f"signals after warm-up: TV {len(tvs)}, Python {len(py)}, matching {len(py & tvs)}")
for x in sorted(tvs - py):
    print("  only TV:    ", pd.to_datetime(x[0], unit='s', utc=True).tz_convert('America/New_York'), x[1])
for x in sorted(py - tvs):
    print("  only Python:", pd.to_datetime(x[0], unit='s', utc=True).tz_convert('America/New_York'), x[1])

tvt = json.loads((DATA / "tv_trades_mss40_atr6.json").read_text())["trades"]
res2 = run(bars, Params(mss_window=40, max_stop_atr=6))
print("\ntrades (MSS 40, stop 6 ATR):")
for t in tvt:
    if t["e"]["tm"] / 1000 >= warm:
        print("  TV:    ", pd.to_datetime(t['e']['tm'], unit='ms', utc=True).tz_convert('America/New_York'), t["e"]["p"], "->", t["x"]["p"], t["x"]["c"], t["tp"]["v"])
for t in res2.trades:
    if t["entry_time"] >= warm:
        print("  Python:", pd.to_datetime(t['entry_time'], unit='s', utc=True).tz_convert('America/New_York'), t["entry"], "->", t["exit"], t["why"], t["pnl"])
