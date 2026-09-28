// Push a local .pine file into the open TradingView Pine editor and update it on the chart.
// Refuses unless the editor already holds a Botmax script, so it can't overwrite anything else.
// Usage: node tools/push_pine.mjs pine/botmax_v0.pine
import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

const JACKSON = process.env.TV_MCP_DIR || 'C:/Users/user/tradingview-mcp-jackson';
const pine = await import(pathToFileURL(`${JACKSON}/src/core/pine.js`).href);

const { evaluate } = await import(pathToFileURL(`${JACKSON}/src/connection.js`).href);

// TV Desktop 3.x shows Pine as a floating dialog that Jackson's opener doesn't find; open it via the sidebar button.
const hasEditor = () => evaluate(`!!document.querySelector('.monaco-editor.pine-editor-monaco')`);
if (!(await hasEditor())) {
  await evaluate(`(function(){var b=document.querySelector('[data-name="pine-dialog-button"]');if(b)b.click();})()`);
  for (let i = 0; i < 40 && !(await hasEditor()); i++) await new Promise((r) => setTimeout(r, 150));
}

const source = readFileSync(process.argv[2], 'utf8').replace(/\r\n/g, '\n');
const current = await pine.getSource();
const text = current.source ?? current.code ?? JSON.stringify(current);
if (!/Botmax/.test(text.slice(0, 2000))) {
  console.error('ABORT: the open editor script is not a Botmax script.');
  process.exit(1);
}
await pine.setSource({ source });
const res = await pine.smartCompile();
console.log(JSON.stringify(res));
process.exit(res.has_errors ? 1 : 0);
