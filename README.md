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

## Fast TradingView loop (no screenshots)
Needs TradingView Desktop running with `--remote-debugging-port=9222` and the `tradingview-mcp-jackson` repo at `C:/Users/user/tradingview-mcp-jackson` (or `TV_MCP_DIR`).
- `node tools/push_pine.mjs pine/botmax_v0.pine` — load the file into the open Botmax script and save (refuses non-Botmax scripts).
- `node tools/bt.mjs` — metrics + setup funnel in ~0.2 s. `--set '{"<input title>": v}'`, `--grid '{"<input title>": [..]}'`, `--trades`.

## Walk-forward test on long history (no TradingView)
`research/engine.py` reproduces v0 exactly (`python research/parity.py`: 7/7 signals, 3/3 trades vs TradingView).
`python research/wf.py [data/nq_5m_lse.csv]` runs a small grid over the full history, picks parameters on each
train window and records only the next test window's trades (out-of-sample), then writes `research/WF_REPORT.md`
with a bootstrap p-value next to the fixed defaults. Roll days are skipped (inferred from the gaps when the CSV has no
`contract` column). Data: `LSE_API_KEY=... python tools/lse_download.py NQ.F futures` (10 years of NQ 5m, ~7 min) or
`tools/ibkr_download.py` (TWS/Gateway). Latest result: `research/WF_REPORT.md`.
