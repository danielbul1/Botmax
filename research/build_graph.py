"""Build the indicator knowledge graph with Jev ("connect the dots").

Design follows TypeSafe's own guidance (entity-alignment, self-consistency and
feature-discovery cookbooks): narrow typed questions, worded levels instead of
fitted thresholds, uncertain answers routed to review, and code owning policy.

Stage 1  profile   one request per node: dimension, role, lag, codeability,
                   evidence, repaint risk, data needs.
Stage 2  coverage  one request per node: which shortlisted concepts does this
                   script/concept already use? -> what the market has already
                   combined, so we can find combinations nobody builds.
Stage 3  edges     every shortlisted pair judged in BOTH directions: typed
                   relation (incl. sequence: precondition/follows), synergy,
                   same-mechanism. Direction swap doubles as a consistency check.
Stage 4  analysis  (code) merge directions, flag uncertain/inconsistent edges,
                   novelty per pair, and beam-search full setups
                   filter -> bias -> location -> trigger -> risk.

Outputs research/graph.json. Jev answers are cached in research/cache/ so
reruns only pay for new or changed questions.
"""
import asyncio
import hashlib
import itertools
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from typesafe_sdk import AsyncTypeSafeClient, Choice, Noul, Score

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT.parent / ".env")
CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)
CONCURRENCY = 8
EDGE_BATCH = 6       # candidate partners judged per request
UNCERTAIN = (0.30, 0.70)

NODE_FIELDS = ["name", "source", "what_it_does", "inputs", "core_math", "outputs",
               "signal_type", "timeframes", "repaints", "weaknesses"]

DIMENSIONS = {
    "trend": "Direction and persistence of price movement (moving averages, supertrend, regression slope).",
    "momentum": "Speed or acceleration of price change (RSI, MACD, rate of change, oscillators).",
    "volatility": "Size of price ranges and their expansion or contraction (ATR, bands, squeezes).",
    "market_structure": "Sequence of swing highs and lows, and breaks of them (BOS, CHoCH, pivots).",
    "liquidity": "Where resting stop orders likely sit and whether they were swept (equal highs/lows, prior highs/lows, stop hunts).",
    "imbalance_zones": "Price areas left inefficient or where large orders originated (FVGs, order blocks, supply/demand).",
    "volume_flow": "Traded volume, its distribution across price, or buy/sell pressure (volume profile, VWAP, delta).",
    "time_session": "Time-of-day or calendar effects (killzones, session opens, opening range).",
    "mean_reversion": "Statistical stretch away from a fair value and the pull back to it (z-score, channels, kernels).",
    "regime": "Whether the market is trending or ranging, or which volatility state it is in (Hurst, choppiness, efficiency ratio).",
}
ROLES = {
    "filter": "Allows or blocks trading based on market condition or time, without choosing direction.",
    "bias": "Sets the directional context or higher-timeframe bias; decides which side to trade.",
    "location": "Marks where to look for a trade: a price level or zone of interest.",
    "trigger": "Fires the precise entry moment on a specific bar.",
    "risk": "Places stops, targets, trailing exits or position size.",
}
CHAIN = ["filter", "bias", "location", "trigger", "risk"]

RELATIONS = {
    "duplicate": "They compute essentially the same thing; using both adds nothing.",
    "alternative": "Different methods for the same job in a trade; a system would pick one of them.",
    "precondition": "`a` must happen or be checked first, and `b` only makes sense after it (a feeds into b).",
    "follows": "`b` must happen or be checked first, and `a` only makes sense after it (b feeds into a).",
    "confirming": "Independent evidence for the same signal at the same moment; agreement raises confidence.",
    "gating": "One of them decides when or whether the other should be used, without choosing direction.",
    "conflicting": "They rest on incompatible assumptions or typically signal opposite actions.",
    "unrelated": "No meaningful interaction.",
}
FLIP = {"precondition": "follows", "follows": "precondition"}


def node_state(n):
    return {k: n.get(k) for k in NODE_FIELDS}


def cache_key(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:24]


async def ask(client, sem, state, questions, tag):
    """Cached Jev call. Returns a plain dict of answers."""
    key = cache_key({"s": state, "q": {k: v.model_dump() for k, v in questions.items()}})
    path = CACHE / f"{tag}-{key}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    for attempt in range(4):
        try:
            async with sem:
                r = await client.system_one(state=state, questions=questions)
            break
        except Exception as exc:  # timeouts / transient errors: back off, retry
            if attempt == 3:
                print(f"  giving up on {tag} request: {exc!r}")
                return None
            await asyncio.sleep(2 ** attempt)
    out = {}
    for k, a in r.nouls.items():
        out[k] = {"p": a.noul}
    for k, a in r.choices.items():
        out[k] = {"choice": a.choice, "probs": dict(a.probabilities), "conf": a.confidence}
    for k, a in r.scores.items():
        out[k] = {"score": a.score, "conf": a.confidence}
    path.write_text(json.dumps(out), encoding="utf-8")
    return out


# ---------- questions ----------

def profile_questions():
    return {
        "dimension": Choice(
            instructions="Which single dimension of the market does `indicator` primarily measure? Judge by its `core_math`, not its name.",
            criteria=DIMENSIONS),
        "secondary": Choice(
            instructions="Besides its primary focus, which second dimension does `indicator` most meaningfully use? Pick 'none' if it relies on one dimension only.",
            criteria={**DIMENSIONS, "none": "It relies on one dimension only."}),
        "role": Choice(
            instructions="In a complete rule-based trading plan, which job is `indicator` best suited for?",
            criteria=ROLES),
        "lag": Score(
            instructions="How early does `indicator` react relative to the price move it describes?",
            criteria=["Leading: it marks a level or condition before price reacts there",
                      "Coincident: it reacts on the bar the move happens",
                      "Short lag: confirms a few bars after the move starts",
                      "Long lag: confirms only well after the move is established"]),
        "codeable": Score(
            instructions="How precisely could a programmer implement `indicator` in Pine Script using only its description in `core_math`?",
            criteria=["Not implementable: mechanism undisclosed or vague",
                      "Partly: key parameters or rules would have to be guessed",
                      "Mostly: a reasonable implementation with a few assumptions",
                      "Exactly: rules are fully objective and specified"]),
        "evidence": Score(
            instructions="How much credible evidence is described that `indicator` has a real predictive edge, beyond popularity or marketing claims?",
            criteria=["None described, or only marketing claims",
                      "Anecdotal: trader testimony or cherry-picked charts",
                      "Some: a logical market mechanism or informal backtests",
                      "Strong: academic research or robust published backtests"]),
        "lookahead_free": Noul(
            instructions="Once a bar has closed, is `indicator`'s signal for that bar final, so it never changes or disappears when later bars arrive? Signals confirmed after a fixed delay that then never change count as final.",
            criteria={"true": "Signals are final after confirmation.",
                      "false": "Signals can be redrawn, moved or deleted afterwards (repainting)."}),
        "is_composite": Noul(
            instructions="Is `indicator` a toolkit or system that combines several distinct concepts, rather than a single concept or calculation?"),
        "needs_volume": Noul(instructions="Does `indicator` require real traded volume data to work?"),
        "needs_htf": Noul(instructions="Does `indicator` require data from a higher timeframe than the chart?"),
    }


def coverage_questions(concepts):
    return {c["id"]: Noul(
        instructions={"concept": {"name": c["name"], "definition": c["what_it_does"]},
                      "question": "Does `indicator` itself compute or use `concept` as part of its logic?"})
        for c in concepts}


def edge_questions(slots):
    qs = {}
    for s in slots:
        qs[f"{s}|relation"] = Choice(
            instructions=f"How does `a` relate to `candidates.{s}` inside one rule-based trading system? In the options, `b` means `candidates.{s}`.",
            criteria=RELATIONS)
        qs[f"{s}|synergy"] = Score(
            instructions=f"How well would `a` and `candidates.{s}` work together in one rule-based trading system, each doing a distinct job?",
            criteria=["Conflicting: they contradict or fight each other",
                      "Neutral: no meaningful interaction",
                      "Useful: one clearly improves the other",
                      "Strong: together they form a coherent setup neither makes alone"])
        qs[f"{s}|same_mechanism"] = Noul(
            instructions=f"Do `a` and `candidates.{s}` derive their signal from the same underlying calculation on the same inputs?")
    return qs


# ---------- analysis (code owns policy) ----------

def merge_edges(raw):
    """Combine the a->b and b->a judgments of each pair."""
    by_pair = {}
    for e in raw:
        by_pair.setdefault(frozenset((e["a"], e["b"])), []).append(e)
    merged = []
    for pair, views in by_pair.items():
        a, b = sorted(pair)
        probs = {r: 0.0 for r in RELATIONS}
        choices = []
        for v in views:
            flip = v["a"] != a  # express everything as a->b
            for r, p in v["relation"]["probs"].items():
                probs[FLIP.get(r, r) if flip else r] += p / len(views)
            c = v["relation"]["choice"]
            choices.append(FLIP.get(c, c) if flip else c)
        syn = [v["synergy"]["score"] for v in views]
        same = [v["same_mechanism"]["p"] for v in views]
        relation = max(probs, key=probs.get)
        synergy = sum(syn) / len(syn)
        same_mech = sum(same) / len(same)
        review = []
        if len(set(choices)) > 1:
            review.append("direction views disagree on relation: " + "/".join(choices))
        if len(syn) > 1 and abs(syn[0] - syn[1]) >= 1.0:
            review.append("direction views disagree on synergy")
        if UNCERTAIN[0] < same_mech < UNCERTAIN[1]:
            review.append("same_mechanism uncertain")
        if probs[relation] < 0.5:
            review.append("no dominant relation")
        merged.append({"a": a, "b": b, "relation": relation,
                       "relation_probs": {k: round(v, 3) for k, v in probs.items()},
                       "synergy": round(synergy, 3), "same_mechanism": round(same_mech, 3),
                       "review": review})
    return merged


def novelty(edges, nodes, short_ids):
    """How often existing scripts already combine each pair (from coverage)."""
    uses = {sid: set() for sid in short_ids}
    for n in nodes:
        for sid, p in n.get("covers", {}).items():
            if p >= UNCERTAIN[1]:
                uses[sid].add(n["id"])
    for e in edges:
        both = uses[e["a"]] & uses[e["b"]]
        e["combined_in"] = sorted(both)
        e["novelty"] = round(1 / (1 + len(both)), 3)


def search_chains(nodes_by_id, short_ids, edges, beam=200, top=25):
    """Beam search for full setups: one node per role, in CHAIN order."""
    E = {frozenset((e["a"], e["b"])): e for e in edges}
    by_role = {r: [i for i in short_ids if nodes_by_id[i]["jev"]["role"]["choice"] == r] for r in CHAIN}

    def pair_value(x, y):
        e = E.get(frozenset((x, y)))
        if not e:
            return 0.0
        p = e["relation_probs"]
        v = (e["synergy"] - 1.0)              # neutral = 0, strong = +2
        v -= 3 * (p["duplicate"] + p["alternative"]) + 2 * p["conflicting"]
        v -= 2 * e["same_mechanism"]
        v += 0.5 * e["novelty"]
        return v

    beams = [((), 0.0)]
    for role in CHAIN:
        cands = by_role[role]
        if not cands:
            continue
        nxt = []
        for chain, score in beams:
            for c in cands:
                gain = sum(pair_value(c, x) for x in chain)
                j = nodes_by_id[c]["jev"]
                gain += 0.5 * j["evidence"]["score"] / 3 + 0.5 * j["codeable"]["score"] / 3
                nxt.append((chain + (c,), score + gain))
        beams = sorted(nxt, key=lambda t: t[1], reverse=True)[:beam]
    return [{"chain": list(c), "score": round(s, 3)} for c, s in beams[:top]]


async def main(shortlist_size):
    nodes = []
    for f in sorted((ROOT / "nodes").glob("*.json")):
        nodes += json.loads(f.read_text(encoding="utf-8"))
    by_id = {n["id"]: n for n in nodes}
    print(f"{len(nodes)} nodes loaded")

    sem = asyncio.Semaphore(CONCURRENCY)
    async with AsyncTypeSafeClient(timeout=60.0) as client:
        # Stage 1: profiles
        pq = profile_questions()
        profiles = await asyncio.gather(*[
            ask(client, sem, {"indicator": node_state(n)}, pq, "profile") for n in nodes])
        missing = [n["id"] for n, p in zip(nodes, profiles) if p is None]
        if missing:
            sys.exit(f"profiles failed for {missing}; rerun (answers so far are cached)")
        for n, p in zip(nodes, profiles):
            n["jev"] = p
        print("stage 1 done: profiles")

        # Policy: shortlist atomic concepts we can code exactly without
        # repainting, with a quota per role so every job in a trade is covered.
        # Evidence is deliberately not used here (untested != useless; testing
        # is our job) -- it only weighs in when ranking chains.
        def rank(n):
            j = n["jev"]
            return (j["codeable"]["score"] / 3) * 0.6 + j["lookahead_free"]["p"] * 0.4
        atomic = [n for n in nodes if n["jev"]["is_composite"]["p"] < UNCERTAIN[1]]
        per_role = {r: sorted([n for n in atomic if n["jev"]["role"]["choice"] == r],
                              key=rank, reverse=True) for r in CHAIN}
        total = sum(len(v) for v in per_role.values())
        short = []
        for r, ranked in per_role.items():
            quota = max(3, round(shortlist_size * len(ranked) / total))
            short += ranked[:quota]
        short_ids = [n["id"] for n in short]
        print(f"shortlist: {len(short_ids)} nodes " +
              str({r: sum(1 for n in short if n['jev']['role']['choice'] == r) for r in CHAIN}))

        # Stage 2: coverage (what existing scripts already combine)
        cq = coverage_questions(short)
        cover = await asyncio.gather(*[
            ask(client, sem, {"indicator": node_state(n)}, cq, "cover") for n in nodes])
        for n, c in zip(nodes, cover):
            if c is None:
                continue
            n["covers"] = {k: v["p"] for k, v in c.items() if k != n["id"]}
        print("stage 2 done: coverage")

        # Stage 3: edges, both directions
        tasks = []
        for a in short_ids:
            partners = [b for b in short_ids if b != a]
            for i in range(0, len(partners), EDGE_BATCH):
                slots = {f"c{k}": b for k, b in enumerate(partners[i:i + EDGE_BATCH])}
                state = {"a": node_state(by_id[a]),
                         "candidates": {s: node_state(by_id[b]) for s, b in slots.items()}}
                tasks.append((a, slots, ask(client, sem, state, edge_questions(list(slots)), "edge")))
        results = await asyncio.gather(*[t[2] for t in tasks])
        raw = []
        failed = sum(1 for r in results if r is None)
        if failed:
            print(f"  {failed} edge requests failed; rerun to fill them in")
        for (a, slots, _), res in zip(tasks, results):
            if res is None:
                continue
            for s, b in slots.items():
                raw.append({"a": a, "b": b, "relation": res[f"{s}|relation"],
                            "synergy": res[f"{s}|synergy"], "same_mechanism": res[f"{s}|same_mechanism"]})
        print(f"stage 3 done: {len(raw)} directed judgments")

    # Stage 4: analysis
    edges = merge_edges(raw)
    novelty(edges, nodes, short_ids)
    chains = search_chains(by_id, short_ids, edges)
    n_review = sum(1 for e in edges if e["review"])
    print(f"stage 4 done: {len(edges)} edges, {n_review} flagged for review, {len(chains)} chains")

    out = {"nodes": nodes, "shortlist": short_ids, "edges": edges, "chains": chains,
           "dimensions": DIMENSIONS, "roles": ROLES, "relations": RELATIONS}
    (ROOT / "graph.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote research/graph.json")


if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 50))
