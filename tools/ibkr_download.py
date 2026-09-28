"""Download NQ 5-minute history from Interactive Brokers (TWS / IB Gateway API) into data/nq_5m_ibkr.csv.

Read-only: requests historical bars, never places orders.
IBKR doesn't allow end dates on continuous futures, so this walks the quarterly NQ contracts
(expired ones included; IBKR keeps about 2 years) and stitches them: each contract is used
from the previous contract's roll date to its own roll date (8 days before expiry).
Chunks are cached in data/ibkr_chunks/, so an interrupted run resumes.

Usage: .venv/Scripts/python tools/ibkr_download.py [port]   (7497 paper TWS, 7496 live TWS, 4001/4002 Gateway)
"""
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from ib_async import IB, Future

ROOT = Path(__file__).resolve().parent.parent
CHUNKS = ROOT / "data" / "ibkr_chunks"
CHUNKS.mkdir(parents=True, exist_ok=True)
ROLL_DAYS = 8


def main(port):
    ib = IB()
    ib.connect("127.0.0.1", port, clientId=77, readonly=True, timeout=15)
    details = ib.reqContractDetails(Future(symbol="NQ", exchange="CME", currency="USD", includeExpired=True))
    contracts = sorted({d.contract.lastTradeDateOrContractMonth[:8]: d.contract for d in details}.items())
    contracts = [(datetime.strptime(k, "%Y%m%d").replace(tzinfo=timezone.utc), c) for k, c in contracts]
    now = datetime.now(timezone.utc)
    print(f"{len(contracts)} NQ contracts, expiries {contracts[0][0].date()} .. {contracts[-1][0].date()}")

    frames, prev_roll = [], None
    for expiry, c in contracts:
        roll = expiry - timedelta(days=ROLL_DAYS)
        start = prev_roll or roll - timedelta(days=92)
        prev_roll = roll
        end = min(roll, now)
        if end <= start:
            continue
        cur = end
        while cur > start:
            tag = f"{c.localSymbol or c.conId}_{cur:%Y%m%d}"
            f = CHUNKS / f"{tag}.csv"
            if not f.exists():
                bars = ib.reqHistoricalData(c, endDateTime=cur.strftime("%Y%m%d-%H:%M:%S"), durationStr="10 D",
                                            barSizeSetting="5 mins", whatToShow="TRADES", useRTH=False,
                                            formatDate=2, timeout=120)
                df = pd.DataFrame([dict(time=int(b.date.timestamp()), open=b.open, high=b.high, low=b.low,
                                        close=b.close, volume=b.volume) for b in bars])
                df.to_csv(f, index=False)
                print(f"  {tag}: {len(df)} bars", flush=True)
                time.sleep(1)  # IBKR pacing
            df = pd.read_csv(f)
            if not df.empty:
                df = df[(df.time >= start.timestamp()) & (df.time < end.timestamp())]
                df["contract"] = c.localSymbol
                frames.append(df)
            cur -= timedelta(days=10)
        if roll > now:
            break
    ib.disconnect()

    out = pd.concat(frames).drop_duplicates("time").sort_values("time")
    out.to_csv(ROOT / "data" / "nq_5m_ibkr.csv", index=False)
    t = pd.to_datetime(out.time, unit="s", utc=True)
    print(f"wrote data/nq_5m_ibkr.csv: {len(out)} bars, {t.min()} -> {t.max()}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 7497)
