"""Grid for the four modules taken from alttrading.ai's published logic (Substack + site):
B1 acceptance, ORB reclaim fade, P1 volatility-scaled pivots, VWAP-slope playbook switch.
Same split and markets as search_v1.py; ranked on in-sample only.
Usage: python research/search_v2.py -> research/search_v2_results.csv
"""
import itertools
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

from search_v1 import FILTERS, evaluate, v

FLT = [dict(regime=a, hbias=b, vwapmode=c) for a, b, c in itertools.product([False, True], repeat=3)]


def grid():
    for orb_end, win, tol, stop, vol, rr, flt in itertools.product(
            ["09:45", "10:00", "10:30"], [6, 12], [0.25, 0.5], ["retest", "mid"], [False, True],
            [1.0, 1.5, 2.0, 3.0], FLT):
        yield v.P(setup="b1", orb_end=orb_end, acc_window=win, retest_tol=tol, b1_stop=stop, b1_vol=vol, rr=rr, **flt)
    for orb_end, bars, tp, trade_end, flt in itertools.product(
            ["09:45", "10:00", "10:30"], [3, 6, 12], ["mid", "opp"], ["11:30", "13:00"], FLT):
        yield v.P(setup="fade", orb_end=orb_end, fade_bars=bars, fade_tp=tp, orb_trade_end=trade_end, **flt)
    for step, mode, rr, anchor, flt in itertools.product(
            [0.25, 0.5, 0.75], ["reject", "accept"], [1.0, 1.5, 2.0, 3.0], ["open", "close"], FLT):
        yield v.P(setup="p1", p1_step=step, p1_mode=mode, rr=rr, p1_anchor=anchor, **flt)


if __name__ == "__main__":
    configs = list(grid())
    print(len(configs), "configs")
    with Pool() as pool:
        rows = pool.map(evaluate, configs, chunksize=20)
    pd.DataFrame(rows).to_csv(Path(__file__).parent / "search_v2_results.csv", index=False)
