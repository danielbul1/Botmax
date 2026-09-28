"""Every indicator x every ICT concept, judged by Jev.

For each (indicator, concept) pair Jev answers three narrow typed questions:
  use      Choice  how the indicator would work inside a strategy built on the concept
  improve  Score   how much adding it would improve that coded strategy
  clean    Noul    whether the two combine into objective, non-repainting Pine rules

Indicators = LuxAlgo + other catalogs (118). Concepts = ICT catalog (43).
Code owns policy: ranking, thresholds and the report. Answers are cached in
research/cache/ (tag "matrix"), so reruns only pay for new or changed pairs.

Outputs research/concept_matrix.json and research/CONCEPT_MATRIX.md.
"""
import asyncio
import json
import sys
from pathlib import Path

from typesafe_sdk import AsyncTypeSafeClient, Choice, Noul, Score

from build_graph import CONCURRENCY, UNCERTAIN, ask, node_state

ROOT = Path(__file__).resolve().parent
BATCH = 6  # concepts judged per request

USES = {
    "implements": "The indicator itself computes this concept, so it can replace a hand-coded version of it.",
    "locates": "It marks where the concept should be applied: the price levels or zones to watch.",
    "confirms": "Independent evidence at the moment the concept fires; agreement raises confidence in the signal.",
    "filters": "It decides when the concept should be traded at all (market regime, volatility or time), without choosing direction.",
    "biases": "It sets the direction the concept should be traded in (higher-timeframe or trend context).",
    "times": "It fires the precise entry bar after the concept has set up.",
    "manages_risk": "It places the stop, target, trailing exit or position size for trades from this concept.",
    "conflicts": "It rests on assumptions that contradict the concept, or typically signals the opposite action.",
    "unrelated": "No meaningful way to use them together.",
}
IMPROVE = [
    "Hurts: adding it would make a strategy built on the concept worse or contradict it",
    "Neutral: adds nothing the concept does not already provide",
    "Useful: clearly improves one step of the concept's trade (context, entry, filter or exit)",
    "Strong: together they form a noticeably better, coherent setup than the concept alone",
]


def pair_questions(slots):
    qs = {}
    for s in slots:
        c = f"`concepts.{s}`"
        qs[f"{s}|use"] = Choice(
            instructions=f"A rule-based strategy is built around the ICT concept {c}. How would `indicator` work inside that strategy? Judge from both mechanisms (`core_math`), not names.",
            criteria=USES)
        qs[f"{s}|improve"] = Score(
            instructions=f"How much would adding `indicator` improve a coded, backtested strategy built around the ICT concept {c}?",
            criteria=IMPROVE)
        qs[f"{s}|clean"] = Noul(
            instructions=f"Can `indicator` and the ICT concept {c} be combined into objective Pine Script rules where every signal is final once its bar closes (no repainting, no future data)?")
    return qs


def load(name):
    return json.loads((ROOT / "nodes" / f"{name}.json").read_text(encoding="utf-8"))


async def main(limit=None):
    concepts = load("ict")
    indicators = load("luxalgo") + load("other")
    if limit:
        indicators = indicators[:limit]
    print(f"{len(indicators)} indicators x {len(concepts)} concepts = {len(indicators) * len(concepts)} pairs")

    tasks = []
    for ind in indicators:
        for i in range(0, len(concepts), BATCH):
            slots = {f"k{j}": c for j, c in enumerate(concepts[i:i + BATCH])}
            state = {"indicator": node_state(ind),
                     "concepts": {s: node_state(c) for s, c in slots.items()}}
            tasks.append((ind, slots, state))

    sem = asyncio.Semaphore(CONCURRENCY)
    done = 0

    async with AsyncTypeSafeClient(timeout=90.0) as client:
        async def run(t):
            nonlocal done
            ind, slots, state = t
            res = await ask(client, sem, state, pair_questions(list(slots)), "matrix")
            done += 1
            if done % 50 == 0 or done == len(tasks):
                print(f"  {done}/{len(tasks)} requests", flush=True)
            return res
        results = await asyncio.gather(*[run(t) for t in tasks])

    pairs, failed = [], 0
    for (ind, slots, _), res in zip(tasks, results):
        if res is None:
            failed += 1
            continue
        for s, c in slots.items():
            u = res[f"{s}|use"]
            pairs.append({
                "indicator": ind["id"], "concept": c["id"],
                "use": u["choice"], "use_conf": round(u["conf"], 3),
                "use_probs": {k: round(v, 3) for k, v in u["probs"].items()},
                "improve": round(res[f"{s}|improve"]["score"], 3),
                "clean": round(res[f"{s}|clean"]["p"], 3),
            })
    if failed:
        print(f"{failed} requests failed; rerun to fill them in (the rest is cached)")

    # ---- policy (code) ----
    # value: improvement, discounted when it can't be coded cleanly; conflicts/unrelated never rank.
    for p in pairs:
        p["value"] = round(p["improve"] * (0.5 + 0.5 * p["clean"]), 3)
        p["review"] = p["use_conf"] < 0.5 or UNCERTAIN[0] < p["clean"] < UNCERTAIN[1]
    usable = [p for p in pairs if p["use"] not in ("conflicts", "unrelated")]

    names = {n["id"]: n["name"] for n in concepts + indicators}
    by_concept = {}
    for p in usable:
        by_concept.setdefault(p["concept"], []).append(p)
    for v in by_concept.values():
        v.sort(key=lambda p: p["value"], reverse=True)
    by_indicator = {}
    for p in usable:
        by_indicator.setdefault(p["indicator"], []).append(p)
    ind_rank = sorted(by_indicator, key=lambda i: sum(p["value"] for p in by_indicator[i]), reverse=True)
    use_counts = {}
    for p in pairs:
        use_counts[p["use"]] = use_counts.get(p["use"], 0) + 1

    out = {"uses": USES, "improve_levels": IMPROVE, "pairs": pairs,
           "top_per_concept": {c: v[:10] for c, v in by_concept.items()}}
    (ROOT / "concept_matrix.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    md = ["# Concept matrix: every indicator x every ICT concept (Jev)", "",
          f"{len(pairs)} pairs judged. Improve is 0-3 (0 hurts, 1 neutral, 2 useful, 3 strong); "
          "clean = probability the pair codes into non-repainting Pine rules; value = improve x (0.5 + 0.5 x clean).", "",
          "## How indicators relate to concepts overall", ""]
    md += [f"- {k}: {v}" for k, v in sorted(use_counts.items(), key=lambda kv: -kv[1])]
    md += ["", "## Best indicators overall (sum of value across all concepts)", ""]
    for i in ind_rank[:20]:
        top = sorted(by_indicator[i], key=lambda p: p["value"], reverse=True)[:3]
        md.append(f"- **{names[i]}**: best with " + "; ".join(f"{names[p['concept']]} ({p['use']}, {p['value']})" for p in top))
    md += ["", "## Top 5 indicators per ICT concept", ""]
    for c in concepts:
        v = by_concept.get(c["id"], [])[:5]
        md.append(f"### {c['name']}")
        md += [f"- {names[p['indicator']]}: {p['use']}, improve {p['improve']}, clean {p['clean']}"
               + (" (review)" if p["review"] else "") for p in v] or ["- nothing usable"]
        md.append("")
    (ROOT / "CONCEPT_MATRIX.md").write_text("\n".join(md), encoding="utf-8")
    print(f"wrote research/concept_matrix.json and research/CONCEPT_MATRIX.md ({len(pairs)} pairs)")


if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else None))
