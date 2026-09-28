"""Download Nasdaq-100 5-minute history from London Strategic Edge (free key) into data/nq_5m_lse.csv.

Key: LSE_API_KEY in .env (get one at https://londonstrategicedge.com/data).
  .venv/Scripts/python tools/lse_download.py --find          list Nasdaq-100 candidates in the catalog
  .venv/Scripts/python tools/lse_download.py SYMBOL [DATASET] download all 5m candles for that symbol
Pages forward 5,000 bars per call (limit: 200 calls/min); resumable from the last saved bar.
"""
import os
import sys
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from lse import LSE

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
OUT = ROOT / "data" / "nq_5m_lse.csv"


def find(client):
    hits = [x for x in client.catalog()
            if any(k in f"{x['symbol']} {x['name']}".lower() for k in ("nasdaq", "nq", "ndx", "nas100", "us100"))]
    for x in sorted(hits, key=lambda x: (x["category"] != "Futures", x["category"], x["symbol"])):
        print(f"{x['category']:10} {x['dataset']:14} {x['symbol']:16} {x['first']} -> {x['last']}  {x['name']}")


def download(client, symbol, dataset=None):
    have = pd.read_csv(OUT) if OUT.exists() else pd.DataFrame()
    start = pd.to_datetime(have["time"].max(), unit="s", utc=True).strftime("%Y-%m-%d") if len(have) else "1990-01-01"
    frames = [have] if len(have) else []
    while True:
        rows = client.candles(symbol, "5m", start=start, limit=5000, order="asc", dataset=dataset)
        if not rows:
            break
        df = pd.DataFrame(rows)
        # to seconds via datetime64[s]: astype("int64") on a tz-aware column depends on its unit (ns/us)
        df["time"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert(None).to_numpy().astype("datetime64[s]").astype("int64")
        df = df[["time", "open", "high", "low", "close", "volume"]]
        prev_last = int(frames[-1]["time"].max()) if frames else -1
        frames.append(df)
        last = int(df["time"].max())
        print(f"  {len(df)} bars up to {pd.to_datetime(last, unit='s', utc=True)}", flush=True)
        pd.concat(frames).drop_duplicates("time").sort_values("time").to_csv(OUT, index=False)
        if len(df) < 5000 or last <= prev_last:
            break
        # the API takes whole days (YYYY-MM-DD): restart at the last bar's day, duplicates are dropped
        start = pd.to_datetime(last, unit="s", utc=True).strftime("%Y-%m-%d")
        time.sleep(0.35)  # stay under 200 calls/min
    out = pd.read_csv(OUT)
    t = pd.to_datetime(out["time"], unit="s", utc=True)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(out)} bars, {t.min()} -> {t.max()}")


if __name__ == "__main__":
    if not os.environ.get("LSE_API_KEY"):
        sys.exit("Add LSE_API_KEY=... to .env (free key: https://londonstrategicedge.com/data)")
    c = LSE(timeout=120)
    if len(sys.argv) < 2 or sys.argv[1] == "--find":
        find(c)
    else:
        download(c, sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
