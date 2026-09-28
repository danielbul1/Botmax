// Dump the chart's loaded OHLCV bars to CSV (UTC epoch seconds), pulling more history first.
// Usage: node tools/export_bars.mjs data/nq_5m_tv.csv [maxRequests]
import { writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
const JACKSON = process.env.TV_MCP_DIR || 'C:/Users/user/tradingview-mcp-jackson';
const { evaluate } = await import(pathToFileURL(`${JACKSON}/src/connection.js`).href);
const MS = `window.TradingViewApi._activeChartWidgetWV.value()._chartWidget.model().mainSeries()`;
const size = () => evaluate(`${MS}.bars().size()`);
const max = Number(process.argv[3] || 40);
let prev = -1;
for (let i = 0; i < max; i++) {
  const n = await size();
  if (n === prev) break;
  prev = n;
  await evaluate(`(function(){var s=${MS};if(s.requestMoreData)s.requestMoreData(2000);})()`);
  await new Promise((r) => setTimeout(r, 1500));
}
const rows = await evaluate(`(function(){var b=${MS}.bars();var o=[];b.each(function(i,v){o.push(v.slice(0,6).join(','));return false;});return o;})()`);
writeFileSync(process.argv[2], 'time,open,high,low,close,volume\n' + rows.join('\n') + '\n');
console.log(`${rows.length} bars, ${new Date(rows[0].split(',')[0] * 1000).toISOString()} -> ${new Date(rows.at(-1).split(',')[0] * 1000).toISOString()}`);
process.exit(0);
