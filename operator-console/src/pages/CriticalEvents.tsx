import { useEffect, useMemo, useState } from "react";
import { Activity, AlertTriangle, Crosshair, RefreshCw } from "lucide-react";
import { apiUrl } from "../api/client";
import type { CriticalEventCandidate, CriticalEventMonitorStatus, CriticalEventResponse } from "../types";
import { CriticalEventResearch } from "./CriticalEventResearch";
import "./CriticalEvents.css";

const scoreLabels: Record<string, string> = {
  compression: "Compression",
  option_value: "Option value",
  pressure: "Pressure",
  ignition: "Ignition",
  liquidity: "Liquidity",
};

const ETF_UNIVERSE = ["SPY", "QQQ", "IWM", "DIA"];

export function CriticalEvents() {
  const [view, setView] = useState<"LIVE" | "RESEARCH">("LIVE");
  return <>
    <div className="critical-subtabs" role="tablist" aria-label="Long Straddle tools">
      <button type="button" role="tab" aria-selected={view === "LIVE"} className={view === "LIVE" ? "active" : ""} onClick={() => setView("LIVE")}>Live scanner</button>
      <button type="button" role="tab" aria-selected={view === "RESEARCH"} className={view === "RESEARCH" ? "active" : ""} onClick={() => setView("RESEARCH")}>Historical validation & data</button>
    </div>
    {view === "LIVE" ? <CriticalEventsLive /> : <CriticalEventResearch />}
  </>;
}

function CriticalEventsLive() {
  const [minimumScore, setMinimumScore] = useState(6);
  const [response, setResponse] = useState<CriticalEventResponse | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("Ready to scan Schwab market data.");
  const [monitor, setMonitor] = useState<CriticalEventMonitorStatus | null>(null);

  useEffect(() => {
    const refresh = () => fetch(apiUrl("/api/critical-events/monitor")).then((item) => item.json()).then(setMonitor).catch(() => undefined);
    refresh();
    const timer = window.setInterval(refresh, 15000);
    return () => window.clearInterval(timer);
  }, []);

  const visible = useMemo(
    () => response?.candidates.filter((item) => item.total_score >= minimumScore) ?? [],
    [response, minimumScore],
  );
  const selected = response?.candidates.find((item) => item.symbol === selectedSymbol) ?? visible[0] ?? null;

  async function runScan() {
    setBusy(true);
    setMessage("Loading Schwab price history and call/put chains…");
    try {
      const apiResponse = await fetch(apiUrl("/api/critical-events/scan"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbols: ETF_UNIVERSE }),
      });
      const payload = await apiResponse.json();
      if (!apiResponse.ok) {
        const detail = typeof payload.detail === "string" ? payload.detail : payload.detail?.message;
        throw new Error(detail ?? "Critical-event scan failed.");
      }
      setResponse(payload);
      setSelectedSymbol(payload.candidates[0]?.symbol ?? null);
      setMessage(`${payload.candidates.length} symbols analyzed · ${payload.diagnostics.filter((item: { status: string }) => item.status === "ERROR").length} errors`);
    } catch (caught) {
      setMessage(caught instanceof Error ? caught.message : "Critical-event scan failed.");
    } finally {
      setBusy(false);
    }
  }

  async function toggleMonitor() {
    const action = monitor?.enabled ? "stop" : "start";
    setMessage(action === "start" ? "Starting continuous monitoring…" : "Stopping monitor…");
    try {
      const apiResponse = await fetch(apiUrl(`/api/critical-events/monitor/${action}`), { method: "POST" });
      const payload = await apiResponse.json();
      if (!apiResponse.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : "Monitor request failed.");
      setMonitor(payload);
      setMessage(payload.message);
      if (action === "start") playAlertTone(0.08);
    } catch (caught) {
      setMessage(caught instanceof Error ? caught.message : "Monitor request failed.");
    }
  }

  return (
    <section className="critical-events-page">
      <div className="critical-controls card">
        <div className="critical-universe"><small>Fixed ETF universe</small><strong>{ETF_UNIVERSE.join(" · ")}</strong></div>
        <label>Display score floor <strong>{minimumScore}/10</strong><input aria-label={`Display score floor ${minimumScore}/10`} type="range" min="0" max="10" value={minimumScore} onChange={(event) => setMinimumScore(Number(event.target.value))} /></label>
        <div className="critical-actions"><button type="button" disabled={busy} onClick={runScan}><RefreshCw size={16} />{busy ? "Scanning…" : "Scan now"}</button><button className="primary" type="button" onClick={toggleMonitor}>{monitor?.enabled ? "Stop monitor" : "Start 15-minute monitor"}</button></div>
      </div>

      <article className={`card monitor-state ${monitor?.state === "ALERT" ? "alert" : ""}`}><div><small>Continuous monitor</small><strong>{monitor?.state ?? "LOADING"}</strong></div><p>{monitor?.message ?? "Reading monitor status…"}</p><small>{monitor?.last_scan_at ? `Last scan ${new Date(monitor.last_scan_at).toLocaleString()}` : "No automated scan yet"} · Email {monitor?.email_configured ? "configured" : "not configured"}</small></article>

      <div className="monitor-rule">Alert rule: {monitor?.configuration.minimum_score ?? 8}/10 + IGNITION + 2/2 value, ignition, and liquidity for {monitor?.configuration.confirmations_required ?? 2} consecutive scans on the same contract.</div>

      <div className="critical-summary">
        <article className="card"><small>Shown candidates</small><strong>{visible.length}</strong></article>
        <article className="card"><small>Best candidate</small><strong>{visible[0]?.symbol ?? "—"}</strong></article>
        <article className="card"><small>Data source</small><strong>{response?.source ?? "Schwab"}</strong></article>
      </div>

      <div className="critical-status"><Activity size={15} /><span>{message}</span></div>
      {response?.diagnostics.some((item) => item.status === "ERROR") && <article className="card critical-errors">
        <h3>Scan errors</h3>
        {response.diagnostics.filter((item) => item.status === "ERROR").map((item) => <p key={item.symbol}><strong>{item.symbol}</strong><span>{item.message}</span></p>)}
      </article>}
      <div className="critical-workspace">
        <article className="card table-card">
          <div className="card-title"><div><p className="eyebrow">RANKED WATCHLIST</p><h2>Critical-event candidates</h2></div></div>
          <div className="table-scroll"><table><thead><tr><th>Symbol</th><th>Score</th><th>Phase</th><th>Option value</th><th>Ignition</th><th>Spread</th></tr></thead>
            <tbody>{visible.map((item) => <tr key={item.symbol} className={selected?.symbol === item.symbol ? "critical-selected" : ""} onClick={() => setSelectedSymbol(item.symbol)}>
              <td><strong>{item.symbol}</strong><small>${item.price.toFixed(2)}</small></td><td className="critical-score">{item.total_score}/{item.score_maximum ?? 10}</td>
              <td><span className={`critical-phase ${item.phase.toLowerCase()}`}>{item.phase}</span></td><td>{item.scores.option_value}/2</td><td>{item.scores.ignition}/2</td><td>{item.option.spread_pct.toFixed(1)}%</td>
            </tr>)}</tbody></table></div>
          {!visible.length && <div className="critical-empty">Run a scan or lower the display score floor.</div>}
        </article>

        <article className="card critical-detail">
          {selected ? <CandidateDetail candidate={selected} /> : <><Crosshair size={24} /><h2>Trade research</h2><p>Select a candidate to inspect its Schwab quotes and score.</p></>}
        </article>
      </div>
      {response && <div className="critical-disclosure"><AlertTriangle size={14} />{response.disclosure}</div>}
    </section>
  );
}

function playAlertTone(volume = 0.22) {
  const AudioContextClass = window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AudioContextClass) return;
  const context = new AudioContextClass();
  const oscillator = context.createOscillator();
  const gain = context.createGain();
  oscillator.frequency.setValueAtTime(880, context.currentTime);
  gain.gain.setValueAtTime(volume, context.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, context.currentTime + 0.55);
  oscillator.connect(gain); gain.connect(context.destination); oscillator.start(); oscillator.stop(context.currentTime + 0.55);
}

function CandidateDetail({ candidate }: { candidate: CriticalEventCandidate }) {
  return <>
    <div className="critical-detail-heading"><div><p className="eyebrow">{candidate.phase}</p><h2>{candidate.symbol}</h2></div><strong>{candidate.total_score}/{candidate.score_maximum ?? 10}</strong></div>
    <section className="critical-contract"><small>Selected research contract · {candidate.alternatives_evaluated ?? 1} alternatives evaluated</small><h3>{candidate.option.expiration} · ${candidate.option.strike.toFixed(0)} ATM straddle</h3><p>Displayed asks ${candidate.option.natural_debit.toFixed(2)} · with estimated commissions ${candidate.option.modeled_entry_debit.toFixed(2)}</p><p>Breakevens ${candidate.option.lower_breakeven.toFixed(2)} / ${candidate.option.upper_breakeven.toFixed(2)} · required move {candidate.option.breakeven_move_pct.toFixed(1)}%</p></section>
    <p className="critical-model-target">{candidate.model_target}</p>
    <div className="critical-score-grid">{Object.entries(candidate.scores).map(([key, value]) => <div key={key}><small>{scoreLabels[key] ?? key}</small><strong>{value}/2</strong></div>)}</div>
    <section className="critical-quotes"><h3>Modeled economics</h3><p>Expected expiration payoff ${Number(candidate.metrics.expected_payoff).toFixed(2)} · expected net value ${Number(candidate.metrics.expected_net_value).toFixed(2)} per spread</p><p>Estimated probability beyond breakevens {(Number(candidate.metrics.probability_of_profit) * 100).toFixed(1)}% · forecast volatility {(Number(candidate.metrics.forecast_volatility) * 100).toFixed(1)}%</p><p>Market IV {candidate.metrics.market_implied_volatility == null ? "Unavailable" : `${(Number(candidate.metrics.market_implied_volatility) * 100).toFixed(1)}%`} · intraday baseline {Number(candidate.metrics.intraday_sample_count)} sessions at {String(candidate.metrics.intraday_slot)}</p></section>
    <section className="critical-quotes"><h3>Schwab leg quotes</h3><p>Call ${candidate.option.call_bid.toFixed(2)} / ${candidate.option.call_ask.toFixed(2)}</p><p>Put ${candidate.option.put_bid.toFixed(2)} / ${candidate.option.put_ask.toFixed(2)}</p><p>Quote {candidate.option.quote_time ? new Date(candidate.option.quote_time).toLocaleString() : "timestamp unavailable"} · {candidate.data_quality.quotes_provisional ? "provisional outside regular hours" : "regular-hours freshness gate passed"}</p></section>
    <ul>{candidate.reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>
  </>;
}
