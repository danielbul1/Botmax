# Round 4 — TradingView run (to do on the local machine)

Run this from a local Claude Code session (needs TradingView Desktop + tradingview-mcp; a cloud session can't reach them).
Prompt to paste: "Do research/ROUND4_TASK.md end to end, without asking."

1. `git fetch origin claude/vigilant-cray-oga08e && git checkout claude/vigilant-cray-oga08e`; read `research/V1_FINDINGS.md` and `README.md`.
2. Close TradingView Desktop if open, relaunch it with `--remote-debugging-port=9222` (find the install path), wait until `http://localhost:9222/json` responds.
3. Via the tradingview MCP (tradesdontlie, `TV_MCP_DIR` per README) open NQ1! on 5m and make sure the Botmax script is on the chart.
4. `node tools/push_pine.mjs pine/botmax_v1.pine`; fix any compile errors in the file and retry until it passes.
5. `node tools/bt.mjs --study "Botmax v1"` with Setup = "ORB reclaim fade", on as much history as possible (Deep Backtesting if available).
6. Grid: "Reclaim close within (bars of the break)" [3,6,12] x "Target opposite side of range (off = midpoint)" [true,false].
7. Repeat 5–6 on ES1!.
8. Compare with the tables in `V1_FINDINGS.md`, write a "Round 4 — TradingView" section with all numbers and the conclusion, commit and push to `claude/vigilant-cray-oga08e`.
