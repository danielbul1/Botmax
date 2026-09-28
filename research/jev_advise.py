"""Ask Jev how to improve Botmax, and why.

State = what we actually know: the v0 rules, the setup funnel, the backtest grid,
the data limits, and the concept-matrix picks. Each candidate improvement gets
its own request (parallel) with the same questions:
  gain       Score  expected improvement to Botmax's real, out-of-sample results
  step       Choice which step of the trade it improves
  why.*      Noul   one per reason, so "why" is a set of probabilities, not prose
  overfit    Noul   risk it only looks good on this small sample
Plus one overall request: which single thing to do first.
Code ranks and writes research/JEV_ADVICE.md.
"""
import asyncio
import json
from pathlib import Path

from typesafe_sdk import AsyncTypeSafeClient, Choice, Noul, Score

from build_graph import CONCURRENCY, ask

ROOT = Path(__file__).resolve().parent

BOTMAX = {
    "market": "NQ (Nasdaq-100 E-mini futures), 5-minute chart, New York session",
    "rules": [
        "Liquidity levels: Asia session high/low, London session high/low, previous day high/low.",
        "Setup starts only when a level is swept inside 08:30-11:00 New York time.",
        "Price must close back across the swept level within 3 bars (reclaim), otherwise it is a breakout and the setup is dropped.",
        "Within 15 bars of the sweep, price must close through the last internal swing point (market structure shift) and a fair value gap of at least 0.15 ATR must have formed in the new direction.",
        "Entry: limit order at the 50% level of that fair value gap, cancelled after 10 bars or if price hits the target or stop first.",
        "Stop: 4 ticks beyond the sweep extreme. Setup skipped if the stop is wider than 3 ATR.",
        "Target: fixed 2R. Max 2 trades per day, flat at 15:55. Costs: $2.25 per contract per side, 1 tick slippage.",
    ],
    "funnel_last_month": {"levels taken in window": 14, "sweeps": 12, "reclaimed": 8,
                          "market structure shift + FVG": 2, "orders": 0, "filled": 0},
    "backtest_grid_last_month": [
        {"change": "none (defaults)", "trades": 0, "net_usd": 0},
        {"change": "MSS window 15 -> 40 bars", "trades": 2, "net_usd": -2939, "win_rate": 0.0},
        {"change": "stop limit 3 -> 6 ATR", "trades": 1, "net_usd": -14.5},
        {"change": "MSS window 40 bars and stop limit 6 ATR", "trades": 4, "net_usd": -2018, "win_rate": 0.25,
         "avg_win_usd": 935, "avg_loss_usd": 984},
    ],
    "data_limits": "TradingView only gives about one month of 5-minute NQ history on this plan, so each test has very few setups. Longer history is available from Interactive Brokers for an external Python backtest.",
    "concept_matrix_findings": "Jev judged 118 indicators against 43 ICT concepts. ICT concepts supply location and trigger; the recurring gaps are direction (bias), when-to-trade filters and risk management. Top picks: Session VWAP with standard-deviation bands (bias), time-series momentum (bias), ATR/volatility regime filters, volatility-scaled sizing, Chandelier or ATR trailing exits.",
}

CANDIDATES = {
    "more_data": "Rebuild the exact rules in a Python backtester and test them on several years of NQ 5-minute data from Interactive Brokers, keeping TradingView only for final confirmation.",
    "vwap_fade": "Only take a sweep when price is stretched beyond the Session VWAP +/-1 standard deviation band in the sweep direction (sweep of highs above +1 SD for shorts, sweep of lows below -1 SD for longs), and target a return to VWAP.",
    "vwap_trend": "Only take sweeps that trade in the direction of Session VWAP: longs when price is above VWAP, shorts when below.",
    "tsmom_bias": "Only take sweeps in the direction of daily time-series momentum (today's close vs 20 days ago), which is already coded but switched off.",
    "atr_regime": "Only trade when today's volatility is in a normal regime: 5-minute ATR between the 20th and 80th percentile of its last 60 days.",
    "fvg_stop": "Place the stop beyond the fair value gap's first candle instead of beyond the sweep extreme, making risk smaller so fewer setups are skipped for a wide stop and the R multiple improves.",
    "trail_exit": "Replace the fixed 2R target with a partial exit at 1R and an ATR (Chandelier-style) trailing stop on the rest.",
    "wider_mss": "Allow up to 40 bars for the market structure shift instead of 15, since the grid showed it triples the setups that reach the MSS step.",
    "london_window": "Also trade the London killzone (02:00-05:00 New York) with Asia and previous-day levels, roughly doubling the number of setups.",
    "fvg_any_time": "Accept a fair value gap that forms at the sweep bar or up to 3 bars before the market structure shift, instead of only after the sweep.",
}

STEPS = {
    "sample_size": "How reliably we can measure the strategy at all (amount of data or number of trades).",
    "setup_frequency": "How many valid setups reach an order.",
    "setup_quality": "Which setups are taken: avoiding the ones likely to fail.",
    "entry": "The price and moment of entry.",
    "exit_risk": "Stops, targets and position size.",
}
REASONS = {
    "fixes_bottleneck": "It directly fixes the step where the funnel loses most setups, or the reason no trades are placed.",
    "evidence_based": "Its edge is supported by research or a clear market mechanism, not only by popularity.",
    "raises_expectancy": "It is likely to raise average profit per trade after costs, through higher win rate or better reward-to-risk.",
    "more_trades": "It increases the number of trades, which makes results statistically more reliable.",
    "cuts_drawdown": "It is likely to reduce losing streaks and drawdowns.",
    "fits_ict_logic": "It is consistent with the liquidity sweep and reversal logic the strategy is built on.",
}


def candidate_questions():
    qs = {
        "gain": Score(
            instructions="How much would making `candidate` change to `botmax` improve its real, out-of-sample results (net profit after costs and reliability), given everything in `botmax`?",
            criteria=["Hurts: likely makes real results worse",
                      "Neutral: little or no real effect",
                      "Useful: a clear real improvement",
                      "Major: one of the most important changes this strategy needs now"]),
        "step": Choice(instructions="Which part of `botmax` does `candidate` mainly improve?", criteria=STEPS),
        "overfit": Noul(instructions="Given how little data `botmax` has, is there a serious risk that `candidate` only looks good on this small sample and would not hold on new data?"),
    }
    for k, v in REASONS.items():
        qs[f"why.{k}"] = Noul(instructions=f"Does this hold for `candidate` applied to `botmax`? {v}")
    return qs


def first_question():
    return {"first": Choice(
        instructions="Which single change should be made to `botmax` first to get it to the best real results fastest? Consider the funnel, the backtest grid and the data limits.",
        criteria=CANDIDATES)}


async def main():
    sem = asyncio.Semaphore(CONCURRENCY)
    async with AsyncTypeSafeClient(timeout=90.0) as client:
        cq = candidate_questions()
        jobs = [ask(client, sem, {"botmax": BOTMAX, "candidate": {"id": k, "change": v}}, cq, "advise")
                for k, v in CANDIDATES.items()]
        jobs.append(ask(client, sem, {"botmax": BOTMAX}, first_question(), "advise"))
        res = await asyncio.gather(*jobs)

    rows = []
    for (k, v), r in zip(CANDIDATES.items(), res[:-1]):
        why = {w: round(r[f"why.{w}"]["p"], 2) for w in REASONS}
        rows.append({"id": k, "change": v, "gain": round(r["gain"]["score"], 2), "gain_conf": round(r["gain"]["conf"], 2),
                     "step": r["step"]["choice"], "overfit": round(r["overfit"]["p"], 2), "why": why,
                     # policy (code): prefer real gain, penalise overfit risk
                     "priority": round(r["gain"]["score"] * (1 - 0.5 * r["overfit"]["p"]), 2)})
    rows.sort(key=lambda x: x["priority"], reverse=True)
    first = res[-1]["first"]

    out = {"first": first, "ranked": rows}
    (ROOT / "jev_advice.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    md = ["# Jev advice for Botmax", "",
          f"**Do first:** `{first['choice']}` (confidence {first['conf']:.2f})", "",
          "Distribution: " + ", ".join(f"{k} {p:.2f}" for k, p in sorted(first["probs"].items(), key=lambda kv: -kv[1])), "",
          "| # | change | gain 0-3 | step | overfit risk | top reasons (p) |", "|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        top = ", ".join(f"{k} {p}" for k, p in sorted(r["why"].items(), key=lambda kv: -kv[1]) if p >= 0.5)
        md.append(f"| {i} | {r['id']} | {r['gain']} | {r['step']} | {r['overfit']} | {top} |")
    (ROOT / "JEV_ADVICE.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    asyncio.run(main())
