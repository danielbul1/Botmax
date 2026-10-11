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
    vol_regime: float = 0.0   # >0: trade only if mean daily range (last `lookback` days) > this quantile of the last 250
    confirm: str = ""         # other market root (e.g. "ES"): enter only if it is outside its band the same way
    commission: float = 2.25
    slippage_ticks: int = 1
    tick: float = TICK


@dataclass
class LHH:
    entry: int = 930          # 15:30 bar close
    signal_at: int = 600      # 10:00 bar close
    min_move: float = 0.0     # |first-half-hour return| must exceed this (fraction)
    commission: float = 2.25
    slippage_ticks: int = 1
    tick: float = TICK


def _rth(df):
    df = df.sort_values("time").reset_index(drop=True)
    if "adj" in df:                                           # work on raw contract prices (percent moves)
        df = df.assign(**{c: df[c] - df["adj"] for c in ("open", "high", "low", "close")})
    t = pd.to_datetime(df["time"], unit="s", utc=True).dt.tz_convert(NY)
    om = (t.dt.hour * 60 + t.dt.minute).to_numpy()
    keep = (om >= 570) & (om < 960)
    df = df[keep].reset_index(drop=True)
    df["cm"] = om[keep] + 5                                   # bar close minute (5m bars)
    df["day"] = t[keep].dt.date.to_numpy()
    return df


def _trade(trades, d, t_in, px_in, t_out, px_out, p, pv):
    slip = p.slippage_ticks * getattr(p, "tick", TICK)
    pnl = (px_out - px_in - 2 * slip * d) * d * pv - 2 * p.commission
    trades.append(dict(entry_time=int(t_in), exit_time=int(t_out), dir=d, entry=px_in, exit=px_out, pnl=round(pnl, 2)))


def run_na(df, p=NA(), point_value=20.0, states=None, confirm=None):
    """states: dict to fill with {decision bar time: +1 above band / -1 below / 0}; confirm: such a dict from another
    market, required to agree in sign for new entries."""
    df = _rth(df)
    days = df.groupby("day", sort=True)
    trades, hist, prev_close, rng = [], [], None, []
    for day, g in days:
        g = g.reset_index(drop=True)
        if g["cm"].iloc[0] != 575 or len(g) < 60:             # need a full session starting 09:30
            prev_close = g["close"].iloc[-1]
            continue
        o = g["open"].iloc[0]
        slot = ((g["cm"] - 575) // 5).to_numpy()
        move = np.abs(g["close"].to_numpy() / o - 1)
        rng.append((g["high"].max() - g["low"].min()) / o)
        calm = False
        if p.vol_regime > 0 and len(rng) > 60:
            cur = np.mean(rng[-p.lookback - 1:-1])
            past = [np.mean(rng[j - p.lookback:j]) for j in range(max(p.lookback, len(rng) - 251), len(rng) - 1)]
            calm = cur < np.quantile(past, p.vol_regime)
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
                state = 1 if C[i] > up[i] else -1 if C[i] < lo[i] else 0
                if states is not None:
                    states[int(T[i])] = state
                if cm[i] <= p.last and not calm:
                    want = state
                    if want and confirm is not None and confirm.get(int(T[i]), 0) != want:
                        want = 0
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
    tick: float = TICK


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


@dataclass
class ON:
    """Overnight hold: enter at the 16:00 close (last RTH bar), exit at the next RTH 09:30 open.
    cond: 'all' | 'down' (today's RTH open->close < 0) | 'up'. dow: entry weekdays allowed (0=Mon).
    direction: 1 long, -1 short. Skips nights that cross a contract roll (adj changes)."""
    cond: str = "all"
    dow: tuple = (0, 1, 2, 3, 4)
    direction: int = 1
    commission: float = 2.25
    slippage_ticks: int = 1
    tick: float = TICK


def run_on(df, p=ON(), point_value=20.0):
    adj = df.sort_values("time")["adj"].to_numpy() if "adj" in df else None
    df = _rth(df)
    if adj is not None:
        df["adj0"] = adj[: len(df)] if len(adj) == len(df) else np.nan
    trades = []
    days = [g.reset_index(drop=True) for _, g in df.groupby("day", sort=True)]
    for a, b in zip(days[:-1], days[1:]):
        ca = a[a["cm"] == 960]
        if not len(ca) or b["cm"].iloc[0] != 575:
            continue
        if (pd.Timestamp(b["day"].iloc[0]) - pd.Timestamp(a["day"].iloc[0])).days > 4:
            continue
        if pd.Timestamp(a["day"].iloc[0]).dayofweek not in p.dow:
            continue
        r = ca["close"].iloc[0] / a["open"].iloc[0] - 1
        if (p.cond == "down" and r >= 0) or (p.cond == "up" and r <= 0):
            continue
        if a["contract"].iloc[-1] != b["contract"].iloc[0] if "contract" in a else False:
            continue
        _trade(trades, p.direction, ca["time"].iloc[0], ca["close"].iloc[0], b["time"].iloc[0], b["open"].iloc[0], p, point_value)
    return trades


@dataclass
class TOM:
    """Turn of the month: long from the close of trading day `pre` before month end (pre=2 -> 2nd-to-last day)
    to the close of trading day `post` of the new month. Uses back-adjusted closes (multi-day hold across rolls)."""
    pre: int = 2
    post: int = 3
    commission: float = 2.25
    slippage_ticks: int = 1
    tick: float = TICK


def run_tom(df, p=TOM(), point_value=20.0):
    d = df.sort_values("time")
    t = pd.to_datetime(d["time"], unit="s", utc=True).dt.tz_convert(NY)
    om = t.dt.hour * 60 + t.dt.minute
    c = d[(om == 955)].assign(day=t[om == 955].dt.date)          # the 15:55 bar closes at 16:00
    c["ym"] = [x.year * 12 + x.month for x in c["day"]]
    trades = []
    months = [g for _, g in c.groupby("ym", sort=True)]
    for a, b in zip(months[:-1], months[1:]):
        if len(a) < p.pre or len(b) < p.post:
            continue
        e, x = a.iloc[-p.pre], b.iloc[p.post - 1]
        _trade(trades, 1, e["time"], e["close"], x["time"], x["close"], p, point_value)
    return trades


@dataclass
class SPR:
    """NQ-ES intraday relative value. s = rNQ - rES since the 09:30 open; band = k x mean |s| at that time of day over
    the last `lookback` days. Every `every` minutes from 10:00: |s| > band -> mode 1 follows (long the leader),
    mode -1 fades. Exit when s crosses back inside half the band (or 16:00). Dollar-neutral: 1 NQ vs h ES."""
    k: float = 1.0
    lookback: int = 14
    every: int = 30
    mode: int = 1
    commission: float = 2.25
    slippage_ticks: int = 1


def run_spread(nq, es, p=SPR(), pv_nq=20.0, pv_es=50.0):
    a, b = _rth(nq), _rth(es)
    m = a.merge(b[["time", "open", "close"]], on="time", suffixes=("", "_es"))
    trades, hist = [], []
    for day, g in m.groupby("day", sort=True):
        g = g.reset_index(drop=True)
        if g["cm"].iloc[0] != 575 or len(g) < 60:
            continue
        o1, o2 = g["open"].iloc[0], g["open_es"].iloc[0]
        slot = np.clip(((g["cm"] - 575) // 5).to_numpy(), 0, 77)
        s = (g["close"] / o1 - g["close_es"] / o2).to_numpy()
        if len(hist) >= p.lookback:
            band = p.k * np.nanmean(np.vstack(hist[-p.lookback:]), axis=0)[slot]
            h = (o1 * pv_nq) / (o2 * pv_es)
            C1, C2, T, cm = g["close"].to_numpy(), g["close_es"].to_numpy(), g["time"].to_numpy(), g["cm"].to_numpy()
            pos = 0
            for i in range(len(g)):
                if cm[i] > 960:
                    break
                last_bar = cm[i] == 960
                if pos and (last_bar or (cm[i] % p.every == 0 and abs(s[i]) < band[i] / 2)):
                    pnl = pos * ((C1[i] - e1) * pv_nq - h * (C2[i] - e2) * pv_es)
                    cost = 2 * p.slippage_ticks * 0.25 * (pv_nq + h * pv_es) + 2 * p.commission * (1 + h)
                    trades.append(dict(entry_time=int(t0), exit_time=int(T[i]), dir=pos, pnl=round(pnl - cost, 2)))
                    pos = 0
                if not pos and not last_bar and cm[i] >= 600 and cm[i] <= 930 and cm[i] % p.every == 0 and abs(s[i]) > band[i]:
                    pos = int(np.sign(s[i])) * p.mode
                    e1, e2, t0 = C1[i], C2[i], T[i]
        row = np.full(78, np.nan)
        row[slot] = np.abs(s)
        hist.append(row)
    return trades
