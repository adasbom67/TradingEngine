import { useEffect, useState } from "react";
import { Archive, BarChart3, Database, RefreshCw } from "lucide-react";
import { apiUrl } from "../api/client";
import type { CriticalEventArchiveStatus, CriticalEventBacktestResponse } from "../types";

const ETF_UNIVERSE = ["SPY", "QQQ", "IWM", "DIA"];

export function CriticalEventResearch() {
  const [periodYears, setPeriodYears] = useState(5);
  const [minimumScore, setMinimumScore] = useState(4);
  const [ivMarkup, setIvMarkup] = useState(1.15);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("Configure a historical validation run.");
  const [result, setResult] = useState<CriticalEventBacktestResponse | null>(null);
  const [archive, setArchive] = useState<CriticalEventArchiveStatus | null>(null);

  function refreshArchive() {
    fetch(apiUrl("/api/critical-events/archive"))
      .then((response) => response.json())
      .then(setArchive)
      .catch(() => undefined);
  }

  useEffect(refreshArchive, []);

  async function runBacktest() {
    setLoading(true);
    setMessage("Loading daily history and evaluating look-ahead-safe signals…");
    try {
      const response = await fetch(apiUrl("/api/critical-events/backtest"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbols: ETF_UNIVERSE,
          period_years: periodYears,
          minimum_signal_score: minimumScore,
          entry_dte: 32,
          implied_volatility_markup: ivMarkup,
        }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : "Historical validation failed.");
      setResult(payload);
      const errors = payload.diagnostics.filter((item: { status: string }) => item.status === "ERROR").length;
      setMessage(`${payload.results.length} ETFs completed · ${errors} errors`);
    } catch (caught) {
      setMessage(caught instanceof Error ? caught.message : "Historical validation failed.");
    } finally {
      setLoading(false);
    }
  }

  return <section className="critical-research-page">
    <article className="card research-configuration">
      <div><small>Historical universe</small><strong>{ETF_UNIVERSE.join(" · ")}</strong></div>
      <label>History<select value={periodYears} onChange={(event) => setPeriodYears(Number(event.target.value))}>{[2, 3, 5, 10, 20].map((value) => <option value={value} key={value}>{value} years</option>)}</select></label>
      <label>Daily proxy floor<select value={minimumScore} onChange={(event) => setMinimumScore(Number(event.target.value))}>{[0, 1, 2, 3, 4, 5, 6].map((value) => <option value={value} key={value}>{value}/6</option>)}</select></label>
      <label>IV proxy markup<input type="number" min="0.5" max="3" step="0.05" value={ivMarkup} onChange={(event) => setIvMarkup(Number(event.target.value))} /></label>
      <button className="primary" type="button" disabled={loading} onClick={runBacktest}><BarChart3 size={16} />{loading ? "Running…" : "Run validation"}</button>
    </article>

    <div className="critical-status"><RefreshCw size={15} className={loading ? "spin" : ""} /><span>{message}</span></div>

    <ArchiveStatus archive={archive} onRefresh={refreshArchive} />

    {!result && <article className="card empty-result"><BarChart3 size={26} /><h2>Historical validation</h2><p>Test whether daily compression, pressure, and ignition proxies preceded sufficient movement and modeled straddle returns.</p></article>}

    {result && <>
      {result.diagnostics.some((item) => item.status === "ERROR") && <article className="card critical-errors"><h3>Backtest errors</h3>{result.diagnostics.filter((item) => item.status === "ERROR").map((item) => <p key={item.symbol}><strong>{item.symbol}</strong><span>{item.message}</span></p>)}</article>}
      <div className="research-result-grid">{result.results.map((item) => {
        const horizon = item.horizons["20"];
        const holdout = item.walk_forward.testing.horizon_20;
        return <article className="card research-result" key={item.symbol}>
          <div className="research-result-heading"><div><small>{item.period.start} to {item.period.end}</small><h2>{item.symbol}</h2></div><strong>{item.signal_count} signals</strong></div>
          <div className="research-metrics">
            <div><small>20-day breakeven rate</small><strong>{percent(horizon.breakeven_rate)}</strong></div>
            <div><small>Modeled win rate</small><strong>{percent(horizon.modeled_win_rate)}</strong></div>
            <div><small>Average modeled P/L</small><strong className={horizon.average_modeled_pnl >= 0 ? "positive-text" : "negative-text"}>{money(horizon.average_modeled_pnl)}</strong></div>
            <div><small>Unseen 30% win rate</small><strong>{percent(holdout.modeled_win_rate)}</strong></div>
          </div>
          <div className="execution-sensitivity">
            <small>20-day execution-cost sensitivity · commissions included in every case</small>
            <div>{Object.entries(horizon.execution_sensitivity).map(([name, scenario]) => <span key={name}><b>{executionLabel(name)}</b><strong>{percent(scenario.modeled_win_rate)}</strong><em>{money(scenario.average_modeled_pnl)}</em></span>)}</div>
          </div>
          <div className="table-scroll"><table><thead><tr><th>Score</th><th>Samples</th><th>BE rate</th><th>Win rate</th><th>Avg P/L</th></tr></thead><tbody>{item.by_score.map((row) => <tr key={row.score}><td>{row.score}/6</td><td>{row.count}</td><td>{percent(row.horizons["20"].breakeven_rate)}</td><td>{percent(row.horizons["20"].modeled_win_rate)}</td><td>{money(row.horizons["20"].average_modeled_pnl)}</td></tr>)}</tbody></table></div>
        </article>;
      })}</div>
      <div className="critical-disclosure">{result.disclosure}</div>
    </>}
  </section>;
}

function ArchiveStatus({ archive, onRefresh }: { archive: CriticalEventArchiveStatus | null; onRefresh: () => void }) {
  return <article className="card archive-status">
    <div className="archive-heading"><div><Archive size={20} /><span><small>Forward option-quote archive</small><strong>{archive?.enabled === false ? "DISABLED" : "ACTIVE"}</strong></span></div><button type="button" onClick={onRefresh}><RefreshCw size={14} />Refresh</button></div>
    {archive?.enabled !== false && <div className="archive-metrics">
      <div><small>Snapshots</small><strong>{archive?.snapshot_count ?? 0}</strong></div>
      <div><small>Contracts</small><strong>{archive?.contract_count ?? 0}</strong></div>
      <div><small>Disk used</small><strong>{formatBytes(archive?.physical_bytes ?? 0)}</strong></div>
      <div><small>Storage cap</small><strong>{formatBytes(archive?.maximum_bytes ?? 0)}</strong></div>
      <div><small>Current annualized</small><strong>{formatBytes(archive?.projected_annual_bytes ?? 0)}</strong></div>
      <div><small>Retention</small><strong>{archive?.retention_days ?? 0} days</strong></div>
    </div>}
    <p><Database size={14} />{archive?.scope ?? "Storage status is loading."}</p>
  </article>;
}

const percent = (value: number) => `${(value * 100).toFixed(1)}%`;
const money = (value: number) => `${value >= 0 ? "+" : "-"}$${Math.abs(value).toFixed(2)}`;
const executionLabel = (name: string) => ({
  ZERO_SPREAD: "No spread allowance",
  MODEST_2C_PER_LEG: "$0.02/leg",
  CONSERVATIVE_5C_PER_LEG: "$0.05/leg",
}[name] ?? name);
function formatBytes(bytes: number) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** index).toFixed(index > 1 ? 1 : 0)} ${units[index]}`;
}
