"""Botmax v0 in Python: same rules as pine/botmax_v0.pine, with TradingView's broker emulator.

Lets us backtest on years of data (IBKR) instead of TradingView's ~1 month of 5m bars.
Parity with TradingView is checked by research/parity.py on bars exported from the chart.

Emulator rules copied from TradingView (strategy() settings in v0):
  - orders are placed at bar close and work from the next bar (process_orders_on_close=false)
  - intrabar path: O->H->L->C if the high is closer to the open than the low, else O->L->H->C
  - limit orders fill only if price trades 1 tick through the limit (backtest_fill_limits_assumption=1),
    or at the open if the bar gaps through
  - market and stop orders get 1 tick adverse slippage; commission $2.25 per contract per side
"""
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

NY = ZoneInfo("America/New_York")
TICK = 0.25
POINT_VALUE = 20.0


@dataclass
class Params:
    kz: tuple = ("08:30", "11:00")
    asia: tuple = ("20:00", "00:00")
    london: tuple = ("02:00", "05:00")
    eod: tuple = ("15:55", "16:00")
    use_asia: bool = True
    use_london: bool = True
    use_pd: bool = True
    reclaim_bars: int = 3
    mss_window: int = 15
    piv_len: int = 2
    min_fvg_atr: float = 0.15
    entry_mode: str = "ce"          # ce | edge | market
    entry_wait: int = 10
    stop_buf: int = 4
    max_stop_atr: float = 3.0
    rr: float = 2.0
    max_trades: int = 2
    bias: str = "off"               # off | tsmom
    ts_len: int = 20
    commission: float = 2.25
    slippage_ticks: int = 1
    fill_limit_ticks: int = 1


def rtick(x):
    return np.floor(x / TICK + 0.5) * TICK   # math.round_to_mintick rounds half up


def _in(tmin, sess):
    a, b = (int(s[:2]) * 60 + int(s[3:]) for s in sess)
    if b == 0:
        b = 24 * 60
    return (tmin >= a) & (tmin < b) if a < b else (tmin >= a) | (tmin < b)


def prepare(df, p):
    """Add session flags, trading day, ATR, pivots and daily levels. df: time (UTC s), open, high, low, close."""
    df = df.sort_values("time").reset_index(drop=True).copy()
    t = pd.to_datetime(df["time"], unit="s", utc=True).dt.tz_convert(NY)
    tmin = (t.dt.hour * 60 + t.dt.minute).to_numpy()
    df["inKZ"] = _in(tmin, p.kz)
    df["inAsia"] = _in(tmin, p.asia)
    df["inLondon"] = _in(tmin, p.london)
    df["isEod"] = _in(tmin, p.eod)
    df["tday"] = (t + pd.Timedelta(hours=6)).dt.date      # CME trading day starts 18:00 New York
    df["newDay"] = df["tday"] != df["tday"].shift(1)
    h, l, c = df["high"].to_numpy(), df["low"].to_numpy(), df["close"].to_numpy()
    tr = np.maximum.reduce([h - l, np.abs(h - np.roll(c, 1)), np.abs(l - np.roll(c, 1))])
    tr[0] = h[0] - l[0]
    atr = np.full(len(df), np.nan)                          # ta.atr(14) = RMA(TR, 14), seeded with SMA
    if len(df) >= 14:
        atr[13] = tr[:14].mean()
        for i in range(14, len(df)):
            atr[i] = (atr[i - 1] * 13 + tr[i]) / 14
    df["atr"] = atr
    daily = df.groupby("tday").agg(dh=("high", "max"), dl=("low", "min"), dc=("close", "last"))
    daily["pdh"], daily["pdl"], daily["dClose1"] = daily["dh"].shift(1), daily["dl"].shift(1), daily["dc"].shift(1)
    daily["dCloseN"] = daily["dc"].shift(p.ts_len + 1)
    df = df.join(daily[["pdh", "pdl", "dClose1", "dCloseN"]], on="tday")
    n = p.piv_len                                           # ta.pivotlow/high(n, n), confirmed n bars late
    pl, ph = np.full(len(df), np.nan), np.full(len(df), np.nan)
    for i in range(2 * n, len(df)):
        k = i - n
        if l[k] < l[k - n:k].min() and l[k] <= l[k + 1:i + 1].min():
            pl[i] = l[k]
        if h[k] > h[k - n:k].max() and h[k] >= h[k + 1:i + 1].max():
            ph[i] = h[k]
    df["pl"], df["ph"] = pl, ph
    return df


@dataclass
class Level:
    name: str
    is_high: bool
    price: float = np.nan
    active: bool = False


@dataclass
class Result:
    trades: list = field(default_factory=list)
    funnel: dict = field(default_factory=dict)
    events: list = field(default_factory=list)


class Broker:
    """One position at a time, one pending entry, one stop/limit bracket."""

    def __init__(self, p, T, res):
        self.p, self.T, self.res = p, T, res
        self.slip, self.thru = p.slippage_ticks * TICK, p.fill_limit_ticks * TICK
        self.pos, self.px, self.bar, self.tag = 0, np.nan, None, ""
        self.entry = None        # dict(dir, kind, price, tag)
        self.bracket = None      # dict(stop, limit)
        self.close_next = False

    def _close(self, i, price, why):
        pnl = (price - self.px) * self.pos * POINT_VALUE - 2 * self.p.commission
        self.res.trades.append(dict(entry_time=int(self.T[self.bar]), exit_time=int(self.T[i]), dir=self.pos,
                                    entry=self.px, exit=price, pnl=round(pnl, 2), why=why, level=self.tag))
        self.pos = 0

    def _exit_at(self, i, a, b, first):
        """Check the bracket on the path segment a->b (first: a is the bar open, gaps fill there)."""
        if not self.bracket or self.pos == 0:
            return
        d, stop, lim = self.pos, self.bracket["stop"], self.bracket["limit"]
        if first:
            if (d == 1 and a <= stop) or (d == -1 and a >= stop):
                return self._close(i, a - d * self.slip, "SL")
            if (d == 1 and a >= lim + self.thru) or (d == -1 and a <= lim - self.thru):
                return self._close(i, a, "TP")
            return
        lo, hi = min(a, b), max(a, b)
        hit_stop = lo <= stop if d == 1 else hi >= stop
        hit_lim = hi >= lim + self.thru if d == 1 else lo <= lim - self.thru
        if hit_stop and hit_lim:           # both on one segment: whichever the path reaches first
            hit_lim = (abs(lim - a) < abs(stop - a))
            hit_stop = not hit_lim
        if hit_stop:
            self._close(i, stop - d * self.slip, "SL")
        elif hit_lim:
            self._close(i, lim, "TP")

    def process(self, i, O, H, L, C):
        if self.close_next and self.pos != 0:
            self._close(i, O - self.pos * self.slip, "EOD")
        self.close_next = False
        path = [O, H, L, C] if (H - O) <= (O - L) else [O, L, H, C]
        start = 0
        if self.entry is not None and self.pos == 0:
            e, d = self.entry, self.entry["dir"]
            fill, seg = None, 0
            if e["kind"] == "market":
                fill = O + d * self.slip
            elif (d == 1 and O <= e["price"] - self.thru) or (d == -1 and O >= e["price"] + self.thru):
                fill = O
            else:
                for s in range(1, 4):
                    lo, hi = min(path[s - 1], path[s]), max(path[s - 1], path[s])
                    if (d == 1 and lo <= e["price"] - self.thru) or (d == -1 and hi >= e["price"] + self.thru):
                        fill, seg = e["price"], s
                        break
            if fill is None:
                return
            self.pos, self.px, self.bar, self.tag, self.entry = d, fill, i, e["tag"], None
            # after the fill, continue along the rest of this bar's path
            self._exit_at(i, fill, path[seg] if seg else fill, False)
            for s in range(max(seg, 0) + 1, 4):
                self._exit_at(i, path[s - 1], path[s], False)
            return
        if self.pos != 0:
            self._exit_at(i, O, O, True)
            for s in range(1, 4):
                self._exit_at(i, path[s - 1], path[s], False)


def run(df, p=Params()):
    df = prepare(df, p)
    O, H, L, C = (df[k].to_numpy() for k in ("open", "high", "low", "close"))
    T = df["time"].to_numpy()
    inKZa, inAa, inLa, eoda, nda = (df[k].to_numpy() for k in ("inKZ", "inAsia", "inLondon", "isEod", "newDay"))
    atra, pla, pha = df["atr"].to_numpy(), df["pl"].to_numpy(), df["ph"].to_numpy()
    pdha, pdla, dc1, dcn = (df[k].to_numpy() for k in ("pdh", "pdl", "dClose1", "dCloseN"))

    res = Result()
    bk = Broker(p, T, res)
    asiaH, asiaL = Level("Asia H", True), Level("Asia L", False)
    lonH, lonL = Level("London H", True), Level("London L", False)
    pdH, pdL = Level("PDH", True), Level("PDL", False)
    levels = [asiaH, asiaL, lonH, lonL, pdH, pdL]

    st, d, lvlPx, ext, sweepBar, lvlName = 0, 0, np.nan, np.nan, 0, ""
    fvgTop = fvgBot = np.nan
    fvgBar = None
    entryPx = stopPx = tpPx = np.nan
    orderBar = None
    tradesToday = 0
    lastPL = lastPH = np.nan
    f = dict(taken_in_window=0, sweeps=0, reclaimed=0, mss_fvg=0, orders=0, filled=0)
    prev_pos = 0

    def track(hi, lo, i, flag, prevflag, enabled):
        if flag and not prevflag:
            hi.price, lo.price, hi.active, lo.active = H[i], L[i], False, False
        elif flag:
            hi.price, lo.price = max(hi.price, H[i]), min(lo.price, L[i])
        elif prevflag and enabled:
            hi.active = lo.active = True

    for i in range(len(df)):
        bk.process(i, O[i], H[i], L[i], C[i])          # fills during bar i

        # ---- script at bar i close (same order as the Pine source) ----
        track(asiaH, asiaL, i, inAa[i], i > 0 and inAa[i - 1], p.use_asia)
        track(lonH, lonL, i, inLa[i], i > 0 and inLa[i - 1], p.use_london)
        if nda[i] and i > 0:
            tradesToday = 0
            if p.use_pd and not np.isnan(pdha[i]):
                pdH.price, pdH.active = pdha[i], True
                pdL.price, pdL.active = pdla[i], True
        if not np.isnan(pla[i]):
            lastPL = pla[i]
        if not np.isnan(pha[i]):
            lastPH = pha[i]

        atr, inKZ = atra[i], inKZa[i]
        bias = (1 if dc1[i] > dcn[i] else -1) if p.bias == "tsmom" else 0
        flat = bk.pos == 0
        sweepEvt = mssEvt = False

        for lv in levels:
            if lv.active and not np.isnan(lv.price):
                if (H[i] > lv.price) if lv.is_high else (L[i] < lv.price):
                    lv.active = False
                    if inKZ:
                        f["taken_in_window"] += 1
                    dd = -1 if lv.is_high else 1
                    if st == 0 and flat and inKZ and tradesToday < p.max_trades and bias in (0, dd):
                        st, d, lvlPx, lvlName = 1, dd, lv.price, lv.name
                        ext = H[i] if lv.is_high else L[i]
                        sweepBar, fvgBar, sweepEvt = i, None, True
                        f["sweeps"] += 1

        if st in (1, 2):
            ext = max(ext, H[i]) if d == -1 else min(ext, L[i])
            if i >= 2 and not np.isnan(atr):
                if d == -1 and H[i] < L[i - 2] and (L[i - 2] - H[i]) >= p.min_fvg_atr * atr:
                    fvgTop, fvgBot, fvgBar = L[i - 2], H[i], i
                if d == 1 and L[i] > H[i - 2] and (L[i] - H[i - 2]) >= p.min_fvg_atr * atr:
                    fvgTop, fvgBot, fvgBar = L[i], H[i - 2], i
        if st == 1:
            if (C[i] < lvlPx) if d == -1 else (C[i] > lvlPx):
                st = 2
                f["reclaimed"] += 1
            elif i - sweepBar >= p.reclaim_bars:
                st = 0
        if st == 2:
            mss = (C[i] < lastPL) if d == -1 else (C[i] > lastPH)   # NaN compares False, like Pine's na check
            if mss and fvgBar is not None:
                mssEvt = True
                f["mss_fvg"] += 1
                buf = p.stop_buf * TICK
                stopPx = rtick(ext + buf if d == -1 else ext - buf)
                entryPx = {"ce": rtick((fvgTop + fvgBot) / 2), "edge": fvgBot if d == -1 else fvgTop,
                           "market": C[i]}[p.entry_mode]
                risk = abs(entryPx - stopPx)
                valid = stopPx > entryPx if d == -1 else stopPx < entryPx
                if valid and 0 < risk <= p.max_stop_atr * atr:
                    tpPx = rtick(entryPx + d * p.rr * risk)
                    st, orderBar = 3, i
                    f["orders"] += 1
                else:
                    st = 0
            elif i - sweepBar > p.mss_window:
                st = 0

        # ---- execution layer: orders placed at this close ----
        if st == 3 and flat and i == orderBar:
            bk.entry = dict(dir=d, kind="market" if p.entry_mode == "market" else "limit", price=entryPx, tag=lvlName)
        if st == 3 and flat and orderBar is not None and i > orderBar:
            ran = L[i] <= tpPx if d == -1 else H[i] >= tpPx
            invalid = H[i] >= stopPx if d == -1 else L[i] <= stopPx
            if i - orderBar >= p.entry_wait or ran or invalid or not inKZ:
                bk.entry = None
                st = 0
        if bk.pos != 0 and prev_pos == 0:
            tradesToday += 1
            f["filled"] += 1
            st = 0
        if st == 3 or bk.pos != 0:
            bk.bracket = dict(stop=stopPx, limit=tpPx)
        if eoda[i]:
            bk.entry = None
            bk.close_next = bk.pos != 0
            st = 0
        if sweepEvt or mssEvt:
            res.events.append(dict(time=int(T[i]), sweep=sweepEvt, mss=mssEvt, dir=d))
        prev_pos = bk.pos

    res.funnel = f
    return res


def summarize(res):
    t = pd.DataFrame(res.trades)
    if t.empty:
        return dict(trades=0, net=0.0, **res.funnel)
    wins, losses = t[t.pnl > 0], t[t.pnl <= 0]
    eq = t.pnl.cumsum()
    return dict(trades=len(t), net=round(t.pnl.sum(), 2), win_rate=round(len(wins) / len(t), 3),
                pf=round(wins.pnl.sum() / -losses.pnl.sum(), 2) if len(losses) and losses.pnl.sum() < 0 else None,
                avg=round(t.pnl.mean(), 2), max_dd=round((eq.cummax() - eq).max(), 2), **res.funnel)
