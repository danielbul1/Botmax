"""Grid search over engine_v1 setups x filters, judged on in-sample only, then checked out-of-sample.

Split: first 65% of the NQ window is in-sample (IS). ES over the same IS window is a second, independent-ish
market. Configs are ranked on IS only; OOS numbers are printed for the shortlist and never used to pick.
Usage: python research/search_v1.py  -> research/search_v1_results.csv + printed shortlist
"""
import itertools
import sys
from dataclasses import asdict
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import engine_v1 as v  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"
NQ = pd.read_csv(DATA / "nq_5m_yahoo.csv")
ES = pd.read_csv(DATA / "es_5m_yahoo.csv")
SPLIT = int(NQ.time.iloc[0] + 0.65 * (NQ.time.iloc[-1] - NQ.time.iloc[0]))

FILTERS = [dict(regime=a, hbias=b, vwap=c, tsmom=d)
           for a, b, c, d in itertools.product([False, True], [False, True], [False, True], [0, 5])]


def grid():
    for orb_end, stop, entry, rr, flt in itertools.product(
            ["09:45", "10:00", "10:30"], ["range", "mid", "bar"], ["market", "retest"], [1.0, 1.5, 2.0, 3.0], FILTERS):
        yield v.P(setup="orb", orb_end=orb_end, orb_stop=stop, orb_entry=entry, rr=rr, **flt)
    for win, levels, fib, rr, piv, flt in itertools.product(
            [("08:30", "11:00"), ("03:00", "11:00"), ("09:30", "12:00")],
            [("asia", "london", "pd"), ("asia",), ("pd",), ("london", "pd")],
            [0.382, 0.5, 0.618], [1.0, 1.5, 2.0, 3.0], [1, 2], FILTERS):
        yield v.P(setup="sweep", sweep_win=win, levels=levels, fib=fib, rr=rr, piv=piv, **flt)


def evaluate(p):
    nq = v.run(NQ, p, 20.0)
    es = v.run(ES, p, 50.0)
    nq_is, nq_oos = v.split_stats(nq, SPLIT)
    es_is, es_oos = v.split_stats(es, SPLIT)
    row = {k: (",".join(x) if isinstance(x, tuple) and k == "levels" else
               "-".join(x) if isinstance(x, tuple) else x) for k, x in asdict(p).items()}
    for tag, s in (("nq_is", nq_is), ("nq_oos", nq_oos), ("es_is", es_is), ("es_oos", es_oos)):
        row.update({f"{tag}_{k}": val for k, val in s.items()})
    return row


if __name__ == "__main__":
    configs = list(grid())
    print(len(configs), "configs; split at", pd.to_datetime(SPLIT, unit="s"))
    with Pool() as pool:
        rows = pool.map(evaluate, configs, chunksize=20)
    df = pd.DataFrame(rows)
    df.to_csv(Path(__file__).parent / "search_v1_results.csv", index=False)
