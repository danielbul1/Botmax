"""Download recent intraday futures bars from Yahoo (free, ~60 days of 5m) into data/<sym>_<tf>.csv.

Columns match tools/export_bars.mjs / research/engine.py: time (UTC seconds), open, high, low, close, volume.
Yahoo's NQ=F is a continuous front month, so rolls show up as small gaps; fine for intraday research,
use tools/ibkr_download.py for multi-year history.
"""
import json
import sys
import urllib.request
from pathlib import Path

import pandas as pd

URL = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval={tf}&range={rng}"


def fetch(sym, tf="5m", rng="60d"):
    req = urllib.request.Request(URL.format(sym=sym, tf=tf, rng=rng), headers={"User-Agent": "Mozilla/5.0"})
    r = json.load(urllib.request.urlopen(req, timeout=30))["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    df = pd.DataFrame(dict(time=r["timestamp"], open=q["open"], high=q["high"], low=q["low"],
                           close=q["close"], volume=q["volume"]))
    return df.dropna(subset=["open", "high", "low", "close"]).drop_duplicates("time").sort_values("time")


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "data"
    for sym in sys.argv[1:] or ["NQ=F", "ES=F"]:
        df = fetch(sym)
        path = out / f"{sym.replace('=F', '').lower()}_5m_yahoo.csv"
        df.to_csv(path, index=False)
        print(path.name, len(df), pd.to_datetime(df.time.iloc[0], unit="s"), "->", pd.to_datetime(df.time.iloc[-1], unit="s"))
