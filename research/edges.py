"""Time-of-day edges that trade at bar closes (Pine: process_orders_on_close = true), RTH only.

  na   - noise-area momentum (Zarattini, Aziz & Barbon 2024), same rules as pine/botmax_na.pine
  lhh  - last-half-hour momentum (Gao, Han, Li & Zhou 2018): sign of (prev RTH close -> 10:00) return,
         enter at the 15:30 close, exit at the 16:00 close
Costs: 1 tick slippage per fill against us, $2.25 per side. Returns a list of trade dicts like engine.Broker.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

TICK = 0.25
NY = "America/New_York"


@dataclass
class NA:
    lookback: int = 14
    k: float = 1.0
    every: int = 30
    first: int = 600          # minutes after midnight NY of the first decision bar close
    last: int = 930           # last entry decision
    vwap_stop: bool = True
    direction: int = 0        # 0 both, 1 long only, -1 short only
    commission: float = 2.25
    slippage_ticks: int = 1


@dataclass
class LHH:
    entry: int = 930          # 15:30 bar close
    signal_at: int = 600      # 10:00 bar close
    min_move: float = 0.0     # |first-half-hour return| must exceed this (fraction)
    commission: float = 2.25
    slippage_ticks: int = 1


def _rth(df):
    df = df.sort_values("time").reset_index(drop=True)
    t = pd.to_datetime(df["time"], unit="s", utc=True).dt.tz_convert(NY)
    om = (t.dt.hour * 60 + t.dt.minute).to_numpy()
    keep = (om >= 570) & (om < 960)
    df = df[keep].reset_index(drop=True)
    df["cm"] = om[keep] + 5                                   # bar close minute (5m bars)
    df["day"] = t[keep].dt.date.to_numpy()
    return df


def _trade(trades, d, t_in, px_in, t_out, px_out, p, pv):
    slip = p.slippage_ticks * TICK
    pnl = (px_out - px_in - 2 * slip * d) * d * pv - 2 * p.commission
    trades.append(dict(entry_time=int(t_in), exit_time=int(t_out), dir=d, entry=px_in, exit=px_out, pnl=round(pnl, 2)))


def run_na(df, p=NA(), point_value=20.0):
    df = _rth(df)
    days = df.groupby("day", sort=True)
    trades, hist, prev_close = [], [], None
    for day, g in days:
        g = g.reset_index(drop=True)
        if g["cm"].iloc[0] != 575 or len(g) < 60:             # need a full session starting 09:30
            prev_close = g["close"].iloc[-1]
            continue
        o = g["open"].iloc[0]
        slot = ((g["cm"] - 575) // 5).to_numpy()
        move = np.abs(g["close"].to_numpy() / o - 1)
        if len(hist) >= p.lookback and prev_close is not None:
            ref = np.vstack(hist[-p.lookback:])
            sigma = np.nanmean(ref, axis=0)[np.clip(slot, 0, 77)]
            up = max(o, prev_close) * (1 + p.k * sigma)
            lo = min(o, prev_close) * (1 - p.k * sigma)
            tp = (g["high"] + g["low"] + g["close"]) / 3
            vol = g["volume"].fillna(0).replace(0, 1)
            vwap = ((tp * vol).cumsum() / vol.cumsum()).to_numpy()
            C, T, cm = g["close"].to_numpy(), g["time"].to_numpy(), g["cm"].to_numpy()
            pos, t_in, px_in = 0, None, None
            for i in range(len(g)):
                if cm[i] >= 960:
                    break
                if cm[i] < p.first or cm[i] % p.every:
                    continue
                if pos == 1 and C[i] < (max(up[i], vwap[i]) if p.vwap_stop else up[i]):
                    _trade(trades, 1, t_in, px_in, T[i], C[i], p, point_value); pos = 0
                elif pos == -1 and C[i] > (min(lo[i], vwap[i]) if p.vwap_stop else lo[i]):
                    _trade(trades, -1, t_in, px_in, T[i], C[i], p, point_value); pos = 0
                if cm[i] <= p.last:
                    want = 1 if C[i] > up[i] else -1 if C[i] < lo[i] else 0
                    if want and want != pos and p.direction in (0, want):
                        if pos:
                            _trade(trades, pos, t_in, px_in, T[i], C[i], p, point_value)
                        pos, t_in, px_in = want, T[i], C[i]
            if pos:
                last = g[g["cm"] <= 960].iloc[-1]
                _trade(trades, pos, t_in, px_in, last["time"], last["close"], p, point_value)
        row = np.full(78, np.nan)
        row[np.clip(slot, 0, 77)] = move
        hist.append(row)
        prev_close = g["close"].iloc[-1]
    return trades


def run_lhh(df, p=LHH(), point_value=20.0):
    df = _rth(df)
    trades, prev_close = [], None
    for day, g in df.groupby("day", sort=True):
        sig = g[g["cm"] == p.signal_at]
        ent = g[g["cm"] == p.entry]
        ext = g[g["cm"] == 960]
        if prev_close is not None and len(sig) and len(ent) and len(ext):
            r = sig["close"].iloc[0] / prev_close - 1
            if abs(r) > p.min_move:
                d = 1 if r > 0 else -1
                _trade(trades, d, ent["time"].iloc[0], ent["close"].iloc[0], ext["time"].iloc[0], ext["close"].iloc[0], p, point_value)
        if len(ext):
            prev_close = ext["close"].iloc[0]
    return trades


@dataclass
class GAP:
    """Overnight gap fade: at the 09:30 open, if prev RTH close -> open gap is between g_min and g_max daily ATRs,
    trade toward the previous close (gap fill = target), stop at stop_atr daily ATRs beyond the open, flat 16:00.
    mode = 1 fades the gap, -1 trades with it (continuation, target = 2x gap)."""
    g_min: float = 0.1
    g_max: float = 1.0
    stop_atr: float = 0.5
    mode: int = 1
    commission: float = 2.25
    slippage_ticks: int = 1


def run_gap(df, p=GAP(), point_value=20.0):
    df = _rth(df)
    trades, prev_close, ranges = [], None, []
    for day, g in df.groupby("day", sort=True):
        g = g.reset_index(drop=True)
        full = g["cm"].iloc[0] == 575 and len(g) >= 60
        if full and prev_close is not None and len(ranges) >= 14:
            atr = float(np.mean(ranges[-14:]))
            o = g["open"].iloc[0]
            gap = (o - prev_close) / atr
            if p.g_min <= abs(gap) <= p.g_max:
                d = -int(np.sign(gap)) * p.mode
                tgt = prev_close if p.mode == 1 else o + d * abs(o - prev_close) * 2
                stp = o - d * p.stop_atr * atr
                px_in, t_in = o, g["time"].iloc[0]
                out = None
                for _, b in g.iterrows():
                    if b["cm"] > 960:
                        break
                    if (b["low"] <= stp) if d == 1 else (b["high"] >= stp):
                        out = (b["time"], stp); break
                    if (b["high"] >= tgt) if d == 1 else (b["low"] <= tgt):
                        out = (b["time"], tgt); break
                    last = b
                if out is None:
                    out = (last["time"], last["close"])
                _trade(trades, d, t_in, px_in, out[0], out[1], p, point_value)
        if full:
            ranges.append(g["high"].max() - g["low"].min())
        rth_end = g[g["cm"] <= 960]
        if len(rth_end):
            prev_close = rth_end["close"].iloc[-1]
    return trades
