"""Botmax v1 research engine: every idea from the alttrading.ai free scripts, rebuilt without their bugs.

Setups (each gives entry / stop / target, one position at a time):
  orb    - opening-range breakout (ATX ORB Sniper, Mike's ORB, B1 description): 5m close crosses the
           09:30-orb_end NY range, market entry next bar.
  sweep  - liquidity sweep reversal (TX Price Action, Asia Fibonacci, Tom's Reversal): a session level
           (Asia / London / PDH-PDL) is taken, then a close-based break of the last confirmed swing in the
           other direction; limit entry at a fib retracement of the sweep->BOS leg.
Filters (direction gates, all from completed bars only):
  regime - 1h SMA fast vs slow + slope (Regime Detection, fixed: no lookahead, symmetric slope test)
  hbias  - last completed hour's colour run >= 2 (Tom's hourly bias, fixed: no lookahead_on)
  vwap   - RTH-anchored VWAP side
  tsmom  - daily close vs close N days ago

Fills use research/engine.py's Broker (TradingView emulator: next-bar fills, 1 tick slippage,
limit needs 1 tick through, $2.25/side). Times are America/New_York.
"""
from dataclasses import dataclass, replace
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

import engine as e0
from engine import Broker, Result, TICK, rtick

NY = ZoneInfo("America/New_York")


@dataclass
class P:
    setup: str = "orb"               # orb | sweep | both | b1 | fade | p1
    # ORB
    orb_end: str = "09:45"
    orb_trade_end: str = "11:30"
    orb_stop: str = "range"          # range | mid | bar
    orb_entry: str = "market"        # market | retest
    # sweep
    sweep_win: tuple = ("08:30", "11:00")
    levels: tuple = ("asia", "london", "pd")
    piv: int = 1                     # fractal half-width (1 = 3-bar fractal like TX Price Action)
    mss_window: int = 12
    fib: float = 0.5                 # entry = high - fib * (high - sweep low) for longs
    entry_wait: int = 8
    stop_buf: int = 4                # ticks
    # B1 acceptance: ORB break, then a retest that holds the level
    acc_window: int = 12             # bars after the break to see the retest
    retest_tol: float = 0.25         # retest = low within x ATR of the level (longs)
    b1_stop: str = "retest"          # retest (retest bar extreme) | mid (range midpoint)
    b1_vol: bool = False             # require 5m ATR above its 20-bar mean at the break
    # ORB reclaim fade: break fails back inside the range -> trade back to the range
    fade_bars: int = 6               # the reclaim close must come within this many bars of the break
    fade_tp: str = "mid"             # mid | opp (opposite side of the range)
    # P1 volatility-scaled pivots: anchor +/- k * step * daily ATR
    p1_anchor: str = "open"          # open (09:30 RTH open) | close (previous CME day close)
    p1_step: float = 0.5
    p1_mode: str = "reject"          # reject (touch + close back) | accept (close through)
    p1_win: tuple = ("09:35", "15:00")
    # common
    rr: float = 2.0
    max_stop_atr: float = 4.0
    min_stop_atr: float = 0.3
    max_trades: int = 2
    flat_at: str = "15:55"
    # filters
    regime: bool = False
    reg_fast: int = 13
    reg_slow: int = 34
    hbias: bool = False
    vwap: bool = False
    tsmom: int = 0                   # 0 = off, else lookback in days
    vwapmode: bool = False           # VWAP slope picks the playbook: trend day -> only continuation setups
    vs_len: int = 12                 #   in the slope direction; flat day -> only mean-reversion setups
    vs_thr: float = 1.0              #   trend day = |vwap - vwap[vs_len]| > vs_thr * ATR
    # costs
    commission: float = 2.25
    slippage_ticks: int = 1
    fill_limit_ticks: int = 1


def _mins(s):
    return int(s[:2]) * 60 + int(s[3:])


def _in(tmin, a, b):
    a, b = _mins(a), _mins(b)
    if b == 0:
        b = 1440
    return (tmin >= a) & (tmin < b) if a < b else (tmin >= a) | (tmin < b)


def _known_at_close(df, key, values):
    """Spread a per-group (e.g. hourly) value onto 5m bars from the first bar AFTER its group ends.

    Same timing as Pine's request.security(tf, expr[1], lookahead_on): the completed HTF bar's value
    becomes visible on the first chart bar of the next HTF bar.
    """
    out = pd.Series(np.nan, index=df.index)
    last_idx = df.groupby(key, sort=False).tail(1).index
    out.loc[last_idx] = values.reindex(df.loc[last_idx, key]).to_numpy()
    return out.ffill().shift(1).to_numpy()


def prepare(df, p):
    df = df.sort_values("time").reset_index(drop=True).copy()
    t = pd.to_datetime(df["time"], unit="s", utc=True).dt.tz_convert(NY)
    tmin = (t.dt.hour * 60 + t.dt.minute).to_numpy()
    df["tmin"] = tmin
    df["tday"] = (t + pd.Timedelta(hours=6)).dt.date             # CME day starts 18:00 NY
    df["newDay"] = df["tday"] != df["tday"].shift(1)
    df["dow"] = (t + pd.Timedelta(hours=6)).dt.dayofweek
    h, l, c = (df[k].to_numpy() for k in ("high", "low", "close"))
    tr = np.maximum.reduce([h - l, np.abs(h - np.roll(c, 1)), np.abs(l - np.roll(c, 1))])
    tr[0] = h[0] - l[0]
    df["atr"] = pd.Series(tr).ewm(alpha=1 / 14, adjust=False).mean().to_numpy()

    # daily levels (previous CME day) and daily momentum
    daily = df.groupby("tday").agg(dh=("high", "max"), dl=("low", "min"), dc=("close", "last"))
    df = df.join(daily[["dh", "dl"]].shift(1).rename(columns=dict(dh="pdh", dl="pdl")), on="tday")
    dtr = np.maximum.reduce([daily.dh - daily.dl, (daily.dh - daily.dc.shift()).abs(), (daily.dl - daily.dc.shift()).abs()])
    daily["datr"] = pd.Series(dtr, index=daily.index).ewm(alpha=1 / 14, adjust=False).mean()
    df["datr"] = df["tday"].map(daily["datr"].shift(1))            # yesterday's daily ATR(14)
    df["pdc"] = df["tday"].map(daily["dc"].shift(1))
    df["atr_ma"] = pd.Series(df["atr"]).rolling(20).mean().to_numpy()
    if p.tsmom:
        mom = np.sign(daily["dc"] - daily["dc"].shift(p.tsmom))
        df["tsmom"] = df["tday"].map(mom.shift(1))          # today's bars only know yesterday's close
    # hourly regime from completed hours
    hour_key = t.dt.floor("h")
    df["hkey"] = hour_key
    hourly = df.groupby("hkey").agg(o=("open", "first"), c=("close", "last"))
    fast, slow = hourly["c"].rolling(p.reg_fast).mean(), hourly["c"].rolling(p.reg_slow).mean()
    reg = np.where((fast > slow) & (fast > fast.shift(3)), 1, np.where((fast < slow) & (fast < fast.shift(3)), -1, 0))
    df["regime"] = _known_at_close(df, "hkey", pd.Series(reg, index=hourly.index))
    # hourly colour run (Tom's bias), from completed hours only
    col = np.sign(hourly["c"] - hourly["o"])
    run = col.groupby((col != col.shift()).cumsum()).cumcount() + 1
    df["hbias"] = _known_at_close(df, "hkey", (col * (run >= 2)).astype(float))
    # RTH-anchored VWAP
    rth = _in(tmin, "09:30", "16:00")
    tp = (df["high"] + df["low"] + df["close"]) / 3
    v = df["volume"].fillna(0).where(rth, 0)
    g = df["tday"]
    cv = v.groupby(g).cumsum()
    df["vwap"] = ((tp * v).groupby(g).cumsum() / cv.replace(0, np.nan)).where(rth).to_numpy()
    slope = df["vwap"] - df.groupby("tday")["vwap"].shift(p.vs_len)
    df["vmode"] = np.where(slope > p.vs_thr * df["atr"], 1, np.where(slope < -p.vs_thr * df["atr"], -1, 0))
    df.loc[slope.isna(), "vmode"] = 0
    df["inP1"] = _in(tmin, *p.p1_win)
    df["rthOpen"] = rth & ~pd.Series(rth).shift(1, fill_value=False).to_numpy()
    # fractals, confirmed piv bars late (value appears on the confirming bar)
    n = p.piv
    ph, pl = np.full(len(df), np.nan), np.full(len(df), np.nan)
    for i in range(2 * n, len(df)):
        k = i - n
        if h[k] > h[k - n:k].max() and h[k] >= h[k + 1:i + 1].max():
            ph[i] = h[k]
        if l[k] < l[k - n:k].min() and l[k] <= l[k + 1:i + 1].min():
            pl[i] = l[k]
    df["ph"], df["pl"] = ph, pl
    df["inAsia"] = _in(tmin, "20:00", "00:00")
    df["inLondon"] = _in(tmin, "02:00", "05:00")
    df["inORB"] = _in(tmin, "09:30", p.orb_end)
    df["orbTrade"] = _in(tmin, p.orb_end, p.orb_trade_end)
    df["inSweep"] = _in(tmin, *p.sweep_win)
    df["isFlat"] = _in(tmin, p.flat_at, "18:00")
    return df


def run(df, p=P(), point_value=20.0):
    e0.POINT_VALUE = point_value
    df = prepare(df, p)
    A = {k: df[k].to_numpy() for k in df.columns if k not in ("tday", "hkey")}
    O, H, L, C, T = A["open"], A["high"], A["low"], A["close"], A["time"]
    res = Result()
    bk = Broker(p, T, res)

    def allowed(d, i, kind="trend"):
        if p.vwapmode:
            vm = A["vmode"][i]
            if kind == "trend" and vm != d:
                return False
            if kind == "mr" and vm != 0:
                return False
        if p.regime and A["regime"][i] != d:
            return False
        if p.hbias and A["hbias"][i] != d:
            return False
        if p.vwap and not np.isnan(A["vwap"][i]) and np.sign(C[i] - A["vwap"][i]) != d:
            return False
        if p.tsmom and A["tsmom"][i] != d:
            return False
        return True

    lv = {}                                   # name -> [price, is_high, active]
    asia = lon = None
    orbH = orbL = np.nan
    orb_done = {1: False, -1: False}
    trades_today = 0
    lastPH = lastPL = np.nan
    sw = None                                 # active sweep state dict
    pend = None                               # pending order dict(dir, kind, price, stop, tp, bar, tag)
    stop = tp = np.nan
    prev_pos = 0
    f = dict(orb_sig=0, sweeps=0, bos=0, orders=0, filled=0, filtered=0)
    brk = {}                                  # ORB break tracker for b1 / fade: dir -> state
    anchor, p1_used = np.nan, set()

    for i in range(len(df)):
        ntr = len(res.trades)
        bk.process(i, O[i], H[i], L[i], C[i])
        same_bar = len(res.trades) > ntr and prev_pos == 0     # opened and closed inside bar i
        if A["newDay"][i]:
            trades_today, orb_done = 0, {1: False, -1: False}
            orbH = orbL = np.nan
            sw = None
            brk, p1_used, anchor = {}, set(), np.nan
            if "pd" in p.levels and not np.isnan(A["pdh"][i]):
                lv["PDH"], lv["PDL"] = [A["pdh"][i], True, True], [A["pdl"][i], False, True]
        # session ranges
        for name, flag, key in (("Asia", A["inAsia"], "asia"), ("London", A["inLondon"], "london")):
            if flag[i] and not (i and flag[i - 1]):
                lv[name + " H"], lv[name + " L"] = [H[i], True, False], [L[i], False, False]
            elif flag[i]:
                lv[name + " H"][0] = max(lv[name + " H"][0], H[i])
                lv[name + " L"][0] = min(lv[name + " L"][0], L[i])
            elif i and flag[i - 1] and key in p.levels:
                lv[name + " H"][2] = lv[name + " L"][2] = True
        if A["inORB"][i]:
            orbH = H[i] if np.isnan(orbH) else max(orbH, H[i])
            orbL = L[i] if np.isnan(orbL) else min(orbL, L[i])
        if not np.isnan(A["ph"][i]):
            lastPH = A["ph"][i]
        if not np.isnan(A["pl"][i]):
            lastPL = A["pl"][i]
        atr = A["atr"][i]
        flat = bk.pos == 0
        can_trade = flat and pend is None and trades_today < p.max_trades
        new = None

        # ---- setup: ORB ----
        if p.setup in ("orb", "both") and A["orbTrade"][i] and not np.isnan(orbH) and i:
            for d, lvl in ((1, orbH), (-1, orbL)):
                crossed = (C[i] > lvl >= C[i - 1]) if d == 1 else (C[i] < lvl <= C[i - 1])
                if crossed and not orb_done[d]:
                    orb_done[d] = True
                    f["orb_sig"] += 1
                    if not can_trade or new:
                        continue
                    if not allowed(d, i):
                        f["filtered"] += 1
                        continue
                    sl = {"range": orbL if d == 1 else orbH, "mid": (orbH + orbL) / 2,
                          "bar": L[i] if d == 1 else H[i]}[p.orb_stop] - d * p.stop_buf * TICK
                    px = C[i] if p.orb_entry == "market" else lvl
                    new = dict(dir=d, kind="market" if p.orb_entry == "market" else "limit",
                               price=px, stop=rtick(sl), tag="ORB")

        # ---- setup: sweep -> BOS -> fib retrace ----
        if p.setup in ("sweep", "both"):
            for name, (px, is_high, active) in lv.items():
                if not active:
                    continue
                if (H[i] > px) if is_high else (L[i] < px):
                    lv[name][2] = False
                    d = -1 if is_high else 1
                    if sw is None and A["inSweep"][i] and can_trade:
                        bos = lastPL if d == -1 else lastPH
                        if not np.isnan(bos):
                            sw = dict(dir=d, ext=H[i] if d == -1 else L[i], bos=bos, bar=i, tag=name,
                                      far=L[i] if d == -1 else H[i])
                            f["sweeps"] += 1
            if sw is not None and sw["bar"] != i:
                d = sw["dir"]
                if (d == 1 and L[i] < sw["ext"]) or (d == -1 and H[i] > sw["ext"]):
                    sw["ext"] = L[i] if d == 1 else H[i]            # deeper sweep: re-anchor
                    nb = lastPH if d == 1 else lastPL
                    if not np.isnan(nb):
                        sw["bos"] = nb
                sw["far"] = max(sw["far"], H[i]) if d == 1 else min(sw["far"], L[i])
                if (C[i] > sw["bos"]) if d == 1 else (C[i] < sw["bos"]):
                    f["bos"] += 1
                    leg = abs(sw["far"] - sw["ext"])
                    entry = rtick(sw["far"] - d * p.fib * leg)
                    sl = rtick(sw["ext"] - d * p.stop_buf * TICK)
                    if can_trade and not new and allowed(d, i, "mr"):
                        new = dict(dir=d, kind="limit", price=entry, stop=sl, tag="SWEEP " + sw["tag"])
                    elif can_trade and not new:
                        f["filtered"] += 1
                    sw = None
                elif i - sw["bar"] > p.mss_window or not A["inSweep"][i]:
                    sw = None

        # ---- setups: B1 acceptance and ORB reclaim fade (share one break tracker) ----
        if p.setup in ("b1", "fade") and not np.isnan(orbH) and i and not A["inORB"][i]:
            if A["orbTrade"][i]:
                for d, lvl in ((1, orbH), (-1, orbL)):
                    crossed = (C[i] > lvl >= C[i - 1]) if d == 1 else (C[i] < lvl <= C[i - 1])
                    if crossed and d not in brk:
                        vol_ok = not p.b1_vol or A["atr"][i] > A["atr_ma"][i]
                        brk[d] = dict(bar=i, lvl=lvl, ext=H[i] if d == 1 else L[i], live=True, vol=vol_ok)
                        f["orb_sig"] += 1
            for d, b in brk.items():
                if not b["live"] or b["bar"] == i:
                    continue
                b["ext"] = max(b["ext"], H[i]) if d == 1 else min(b["ext"], L[i])
                back_in = (C[i] < b["lvl"]) if d == 1 else (C[i] > b["lvl"])
                age = i - b["bar"]
                if p.setup == "b1":
                    if back_in or age > p.acc_window or not A["orbTrade"][i]:
                        b["live"] = False
                        continue
                    touched = (L[i] <= b["lvl"] + p.retest_tol * atr) if d == 1 else (H[i] >= b["lvl"] - p.retest_tol * atr)
                    if touched and b["vol"]:
                        b["live"] = False
                        if can_trade and not new and allowed(d, i, "trend"):
                            sl = (L[i] if d == 1 else H[i]) if p.b1_stop == "retest" else (orbH + orbL) / 2
                            new = dict(dir=d, kind="market", price=C[i], stop=rtick(sl - d * p.stop_buf * TICK), tag="B1")
                else:                                               # fade the failed break
                    if age > p.fade_bars:
                        b["live"] = False
                        continue
                    if back_in:
                        b["live"] = False
                        fd = -d
                        if can_trade and not new and allowed(fd, i, "mr"):
                            tgt = (orbH + orbL) / 2 if p.fade_tp == "mid" else (orbL if d == 1 else orbH)
                            new = dict(dir=fd, kind="market", price=C[i], tag="FADE",
                                       stop=rtick(b["ext"] + d * p.stop_buf * TICK), tp=rtick(tgt))

        # ---- setup: P1 volatility-scaled pivots ----
        if p.setup == "p1":
            if A["rthOpen"][i]:
                anchor = O[i] if p.p1_anchor == "open" else A["pdc"][i]
            unit = A["datr"][i] * p.p1_step
            if A["inP1"][i] and not np.isnan(anchor) and not np.isnan(unit) and unit > 0:
                for j in (1, 2, 3, -1, -2, -3):
                    lvl = anchor + j * unit
                    if j in p1_used:
                        continue
                    up = j > 0
                    if p.p1_mode == "reject":
                        hit = (H[i] >= lvl and C[i] < lvl) if up else (L[i] <= lvl and C[i] > lvl)
                        d, kind = (-1 if up else 1), "mr"
                        sl = (H[i] if up else L[i]) + (1 if up else -1) * p.stop_buf * TICK
                    else:
                        hit = (C[i] > lvl >= C[i - 1]) if up else (C[i] < lvl <= C[i - 1])
                        d, kind = (1 if up else -1), "trend"
                        sl = (L[i] if up else H[i]) - d * p.stop_buf * TICK
                    if hit:
                        p1_used.add(j)
                        if can_trade and not new and allowed(d, i, kind):
                            new = dict(dir=d, kind="market", price=C[i], stop=rtick(sl), tag=f"P1 {j:+d}")

        # ---- execution ----
        if new is not None:
            d = new["dir"]
            risk = (new["price"] - new["stop"]) * d
            fixed_tp = "tp" in new and (new["tp"] - new["price"]) * d > 0
            if p.min_stop_atr * atr <= risk <= p.max_stop_atr * atr and ("tp" not in new or fixed_tp):
                if not fixed_tp:
                    new["tp"] = rtick(new["price"] + d * p.rr * risk)
                new["bar"] = i
                pend = new
                stop, tp = new["stop"], new["tp"]
                bk.entry = dict(dir=d, kind=new["kind"], price=new["price"], tag=new["tag"])
                f["orders"] += 1
        if pend is not None and bk.pos == 0 and i > pend["bar"]:
            d = pend["dir"]
            ran = (H[i] >= pend["tp"]) if d == 1 else (L[i] <= pend["tp"])
            dead = (L[i] <= pend["stop"]) if d == 1 else (H[i] >= pend["stop"])
            if i - pend["bar"] >= p.entry_wait or ran or dead or A["isFlat"][i]:
                bk.entry, pend = None, None
        if (bk.pos != 0 and prev_pos == 0) or same_bar:
            trades_today += 1
            f["filled"] += 1
            pend = None
        if bk.pos != 0 or pend is not None:
            bk.bracket = dict(stop=stop, limit=tp)
        if A["isFlat"][i]:
            bk.entry, pend = None, None
            bk.close_next = bk.pos != 0
        prev_pos = bk.pos

    res.funnel = f
    return res


def stats(trades, rr_risk=None):
    t = pd.DataFrame(trades)
    if t.empty:
        return dict(n=0, net=0.0, wr=None, pf=None, avg=None, dd=0.0)
    w, l = t[t.pnl > 0], t[t.pnl <= 0]
    eq = t.pnl.cumsum()
    return dict(n=len(t), net=round(t.pnl.sum()), wr=round(len(w) / len(t), 2),
                pf=round(w.pnl.sum() / -l.pnl.sum(), 2) if len(l) and l.pnl.sum() < 0 else 99.0,
                avg=round(t.pnl.mean()), dd=round((eq.cummax() - eq).max()))


def split_stats(res, split_time):
    tr = res.trades
    return (stats([x for x in tr if x["entry_time"] < split_time]),
            stats([x for x in tr if x["entry_time"] >= split_time]))
