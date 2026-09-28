// Fast backtest loop over the live TradingView chart, via the tradingview-mcp core (CDP).
// No UI clicking, no screenshots: reads the strategy object's report and plot data directly.
//
//   node tools/bt.mjs                                   current inputs -> metrics + funnel
//   node tools/bt.mjs --set '{"Target (R multiple)": 3}' one run with overrides (by input title)
//   node tools/bt.mjs --grid '{"Skip if stop > x ATR": [3,5,8]}'  cartesian grid, one line per run
//   add --trades to include the trade list; add --keep to leave the last inputs applied
import { pathToFileURL } from 'node:url';

const TV_MCP = process.env.TV_MCP_DIR || 'C:/Users/user/Model/tools/tradingview-mcp';
const { evaluate } = await import(pathToFileURL(`${TV_MCP}/src/connection.js`).href);

const args = process.argv.slice(2);
const opt = (k) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : undefined; };
const STUDY = opt('--study') || 'Botmax';

// Page-side helper: find the strategy by title (by title, so only the Botmax strategy is read).
const FIND = `(function(){var m=window.TradingViewApi._activeChartWidgetWV.value()._chartWidget.model().model();
  return m.dataSources().find(function(s){return s.metaInfo&&s.metaInfo().description.indexOf(${JSON.stringify(STUDY)})>=0;});})()`;

async function inputsMeta() {
  return evaluate(`(function(){var s=${FIND};if(!s)return null;return s.metaInfo().inputs.map(function(i){return {id:i.id,name:i.name,defval:i.defval};});})()`);
}

async function currentValues() {
  return evaluate(`(function(){var s=${FIND};var v={};s.getInputValues? null:null;
    var api=window.TradingViewApi._activeChartWidgetWV.value();var st=api.getStudyById(s.id());
    st.getInputValues().forEach(function(x){v[x.id]=x.value;});return v;})()`);
}

async function applyById(byId) {
  await evaluate(`(function(){var s=${FIND};var st=window.TradingViewApi._activeChartWidgetWV.value().getStudyById(s.id());
    var cur=st.getInputValues();var o=${JSON.stringify(byId)};
    cur.forEach(function(x){if(o.hasOwnProperty(x.id))x.value=o[x.id];});st.setInputValues(cur);})()`);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Wait for the strategy to finish recalculating: status leaves "completed" then returns to it.
async function waitRecalc(timeout = 60000) {
  const t0 = Date.now();
  let left = false;
  while (Date.now() - t0 < timeout) {
    const type = await evaluate(`(function(){var s=${FIND};return s&&s.status?s.status().type:null;})()`);
    if (type !== 2) left = true;
    if (type === 2 && (left || Date.now() - t0 > 2500)) return true;
    await sleep(150);
  }
  throw new Error('Timed out waiting for strategy recalculation');
}

async function report(withTrades) {
  return evaluate(`(function(){var s=${FIND};if(!s)return {error:'strategy not on chart'};
    var rd=s.reportData;rd=typeof rd==='function'?rd.call(s):rd;if(rd&&typeof rd.value==='function')rd=rd.value();
    var out={};
    if(rd&&rd.performance){var a=rd.performance.all||{};var p=rd.performance;
      out.metrics={trades:a.totalTrades,netProfit:a.netProfit,profitFactor:a.profitFactor,winRate:a.percentProfitable,
        avgTrade:a.avgTrade,avgWin:a.avgWinTrade,avgLoss:a.avgLosTrade,maxDD:p.maxStrategyDrawDown,
        maxDDpct:p.maxStrategyDrawDownPercent,sharpe:p.sharpeRatio,commission:a.commissionPaid,
        long:p.long&&p.long.totalTrades,short:p.short&&p.short.totalTrades};
      var r=rd.settings&&rd.settings.dateRange&&rd.settings.dateRange.backtest;
      if(r)out.range=[new Date(r.from).toISOString().slice(0,10),new Date(r.to).toISOString().slice(0,10)];}
    if(${withTrades ? 'true' : 'false'}&&rd&&rd.trades)out.trades=rd.trades.slice(0,200);
    var mi=s.metaInfo();var names=(mi.plots||[]).map(function(p){return (mi.styles[p.id]||{}).title||p.id;});
    var last=s.data().last();var f={};
    names.forEach(function(n,i){if(n.indexOf('n ')===0)f[n.slice(2)]=last?last.value[i+1]:null;});
    out.funnel=f;return out;})()`);
}

const meta = await inputsMeta();
if (!meta) { console.error(`No study matching "${STUDY}" on the chart.`); process.exit(1); }
const idOf = Object.fromEntries(meta.map((i) => [i.name, i.id]));
const toIds = (byName) => Object.fromEntries(Object.entries(byName).map(([k, v]) => {
  if (!idOf[k]) throw new Error(`Unknown input "${k}". Known: ${meta.map((i) => i.name).join(' | ')}`);
  return [idOf[k], v];
}));

const withTrades = args.includes('--trades');
const original = await currentValues();
const runs = [];
if (opt('--grid')) {
  const grid = JSON.parse(opt('--grid'));
  let combos = [{}];
  for (const [k, vals] of Object.entries(grid)) combos = combos.flatMap((c) => vals.map((v) => ({ ...c, [k]: v })));
  runs.push(...combos);
} else runs.push(opt('--set') ? JSON.parse(opt('--set')) : null);

try {
  for (const r of runs) {
    if (r) { await applyById(toIds(r)); await waitRecalc(); }
    const res = await report(withTrades);
    console.log(JSON.stringify(r ? { set: r, ...res } : res));
  }
} finally {
  if (runs[0] && !args.includes('--keep')) { await applyById(original); await waitRecalc(); }
}
process.exit(0);
