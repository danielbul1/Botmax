# Botmax

Research-driven Pine Script algo for NQ futures, built by Claude + Jev (TypeSafe).

## Layout
- `research/nodes/` — catalogs: LuxAlgo (65), ICT (43), other top algos (53). One node per indicator/concept.
- `research/PLAYBOOK.md` — how to build and validate Pine v6 algos properly (repainting, ICT coding rules, backtest hygiene).
- `research/build_graph.py` — Jev pipeline: profiles every node, then judges every shortlisted pair in both directions (typed relation, synergy, same mechanism) and searches for full setups.
- `research/graph.json` — the resulting knowledge graph.
- `research/cache/` — cached Jev answers (reruns are free for unchanged questions).
- `pine/botmax_v0.pine` — first strategy: liquidity sweep -> MSS + FVG reversal (NQ 5m, NY killzone).
- `pine/botmax_v1.pine` — alttrading.ai free-library concepts rebuilt clean as switchable modules
  (ORB, sweep -> BOS -> fib retrace; filters: 1h regime, hourly colour run, RTH VWAP, daily momentum).
- `research/engine_v1.py` — Python twin of v1 (same fill model as `engine.py`); `research/search_v1.py` grid
  (IS = first 65%, OOS = rest, NQ + ES) -> `research/search_v1_results.csv`. Findings: `research/V1_FINDINGS.md`.
- `tools/yahoo_download.py` — free ~60 days of 5m NQ/ES from Yahoo into `data/`.

## Setup
```
python -m venv .venv && .venv/Scripts/pip install typesafe-sdk python-dotenv
cp .env.example .env   # add TYPESAFE_API_KEY
.venv/Scripts/python research/build_graph.py 70
```

## Fast TradingView loop (no screenshots)
Needs TradingView Desktop running with `--remote-debugging-port=9222` and the `tradingview-mcp` (tradesdontlie) checkout at `C:/Users/user/Model/tools/tradingview-mcp` (or `TV_MCP_DIR`).
- `node tools/push_pine.mjs pine/botmax_v0.pine` — load the file into the open Botmax script and save (refuses non-Botmax scripts).
- `node tools/bt.mjs` — metrics + setup funnel in ~0.2 s. `--set '{"<input title>": v}'`, `--grid '{"<input title>": [..]}'`, `--trades`.
