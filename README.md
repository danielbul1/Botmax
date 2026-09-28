# Botmax

Research-driven Pine Script algo for NQ futures, built by Claude + Jev (TypeSafe).

## Layout
- `research/nodes/` — catalogs: LuxAlgo (65), ICT (43), other top algos (53). One node per indicator/concept.
- `research/PLAYBOOK.md` — how to build and validate Pine v6 algos properly (repainting, ICT coding rules, backtest hygiene).
- `research/build_graph.py` — Jev pipeline: profiles every node, then judges every shortlisted pair in both directions (typed relation, synergy, same mechanism) and searches for full setups.
- `research/graph.json` — the resulting knowledge graph.
- `research/cache/` — cached Jev answers (reruns are free for unchanged questions).
- `pine/botmax_v0.pine` — first strategy: liquidity sweep -> MSS + FVG reversal (NQ 5m, NY killzone).

## Setup
```
python -m venv .venv && .venv/Scripts/pip install typesafe-sdk python-dotenv
cp .env.example .env   # add TYPESAFE_API_KEY
.venv/Scripts/python research/build_graph.py 70
```
