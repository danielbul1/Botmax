// Download quarterly futures contracts (expired included) from the open TradingView chart, 5m bars,
// one CSV per contract in data/tv_contracts/<ROOT><M><YYYY>.csv. Resumes: existing files are skipped.
// The chart's session setting is used as is (set it to RTH first for RTH-only research).
// Usage: node tools/tv_contracts.mjs NQ 2011 2026 [CME_MINI]
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

const TV_MCP = process.env.TV_MCP_DIR || 'C:/Users/user/Model/tools/tradingview-mcp';
const chart = await import(pathToFileURL(`${TV_MCP}/src/core/chart.js`).href);
const { evaluate } = await import(pathToFileURL(`${TV_MCP}/src/connection.js`).href);

const [root, y0, y1, exch = 'CME_MINI'] = process.argv.slice(2);
const OUT = 'data/tv_contracts';
mkdirSync(OUT, { recursive: true });
const MS = `window.TradingViewApi._activeChartWidgetWV.value()._chartWidget.model().mainSeries()`;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function loadAll() {
  let prev = -1;
  for (let i = 0; i < 12; i++) {
    const n = await evaluate(`${MS}.bars().size()`);
    if (n === prev) break;
    prev = n;
    await evaluate(`(function(){var s=${MS};if(s.requestMoreData)s.requestMoreData(2000);})()`);
    await sleep(1500);
  }
}

for (let y = Number(y0); y <= Number(y1); y++) {
  for (const m of ['H', 'M', 'U', 'Z']) {
    const name = `${root}${m}${y}`;
    const file = `${OUT}/${name}.csv`;
    if (existsSync(file)) continue;
    await chart.setSymbol({ symbol: `${exch}:${name}` });
    await chart.setTimeframe({ timeframe: '5' });
    let ok = false;
    for (let i = 0; i < 40; i++) {
      const sym = await evaluate(`${MS}.symbol()`).catch(() => '');
      const n = await evaluate(`${MS}.bars().size()`).catch(() => 0);
      if (String(sym).includes(name) && n > 0) { ok = true; break; }
      await sleep(500);
    }
    if (!ok) { console.log(`${name}: no data`); continue; }
    await sleep(1500);
    await loadAll();
    const rows = await evaluate(`(function(){var b=${MS}.bars();var o=[];b.each(function(i,v){o.push(v.slice(0,6).join(','));return false;});return o;})()`);
    writeFileSync(file, 'time,open,high,low,close,volume\n' + rows.join('\n') + '\n');
    const d = (r) => new Date(r.split(',')[0] * 1000).toISOString().slice(0, 10);
    console.log(`${name}: ${rows.length} bars ${d(rows[0])} -> ${d(rows.at(-1))}`);
  }
}
process.exit(0);
