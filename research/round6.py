"""Round 6: stage 1 (DISCOVERY 2011-2019) for edges A, A2, B, C on stitched 15-year NQ + ES 5m futures.

Grid sizes are kept small on purpose; every cell counts as a trial in the Deflated Sharpe.
Writes research/round6_discovery.csv and prints a ranked table.
Usage: python research/round6.py [DISC|VAL|HOLD] [config-name ...]   (VAL/HOLD: pass the chosen names)
"""
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

import edges
import engine_v1 as v
from wf import grid_report

FADE = v.P(setup="fade", orb_trade_end="13:00", fade_bars=6, fade_tp="opp")


def configs():
    out = []
    for bars in (3, 6, 12):
        for tp in ("opp", "mid"):
            for reg in (False, True):
                out.append((f"A fade b{bars} {tp}{' +reg' if reg else ''}", replace(FADE, fade_bars=bars, fade_tp=tp, regime=reg)))
    for k in (0.75, 1.0, 1.5):
        for every in (15, 30, 60):
            out.append((f"B na k{k} e{every}", edges.NA(k=k, every=every)))
    for mm in (0.0, 0.002, 0.005):
        out.append((f"C lhh min{mm}", edges.LHH(min_move=mm)))
    for gmin, gmax in ((0.1, 0.5), (0.25, 1.0), (0.5, 1.5)):
        for stop in (0.3, 0.6):
            for mode in (1, -1):
                out.append((f"D gap {'fade' if mode == 1 else 'go'} {gmin}-{gmax} s{stop}", edges.GAP(g_min=gmin, g_max=gmax, stop_atr=stop, mode=mode)))
    return out


if __name__ == "__main__":
    period = sys.argv[1] if len(sys.argv) > 1 else "DISC"
    chosen = set(sys.argv[2:])
    cfg = [c for c in configs() if not chosen or c[0] in chosen]
    rep = grid_report(cfg, period=period)
    rep["min_pf"] = rep[["NQ_pf", "ES_pf"]].min(axis=1)
    rep = rep.sort_values("min_pf", ascending=False)
    path = Path(__file__).with_name(f"round6_{period.lower()}.csv")
    rep.drop(columns=[c for c in rep.columns if c.endswith("_days")]).to_csv(path, index=False)
    pd.set_option("display.width", 250)
    print(rep[["config", "NQ_n", "NQ_pf", "NQ_sr", "NQ_years", "NQ_dsr", "ES_n", "ES_pf", "ES_sr", "ES_years", "ES_dsr"]].to_string(index=False))

