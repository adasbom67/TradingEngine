import { Activity, BarChart3, BookOpen, BriefcaseBusiness, ShieldCheck } from "lucide-react";
import type { DashboardData, Health, PlatformStatus } from "../types";

function statusClass(status: string) {
  if (["HEALTHY", "READY", "CONNECTED", "AVAILABLE", "PASS"].includes(status)) return "good";
  if (["DISABLED", "NOT_CONFIGURED", "AWAITING_SCAN", "NOT_CONNECTED"].includes(status)) return "neutral";
  return "warn";
}

function StatusRow({ label, value }: { label: string; value: PlatformStatus }) {
  return <div className="platform-status-row"><div><strong>{label}</strong><small>{value.message}</small></div><span className={`platform-badge ${statusClass(value.status)}`}>{value.status.replaceAll("_", " ")}</span></div>;
}

export function Dashboard({ health, dashboard }: { health: Health | null; dashboard: DashboardData | null }) {
  const scan = dashboard?.latest_scan;
  return <section className="hero-grid command-center-grid">
    <article className="card span-2 market-overview-live">
      <div className="card-title"><span>Trading day overview</span><BarChart3 size={18}/></div>
      <div className="operating-mode-strip">
        <div><small>Operating mode</small><strong>{dashboard?.operating_mode ?? "RESEARCH"}</strong></div>
        <div><small>Execution</small><strong>{dashboard?.execution_mode ?? "READ ONLY"}</strong></div>
        <div><small>Market data</small><strong>{dashboard?.platform.market_data.status.replaceAll("_", " ") ?? "API unavailable"}</strong></div>
        <div><small>Last refresh</small><strong>{dashboard ? new Date(dashboard.refreshed_at).toLocaleTimeString() : "—"}</strong></div>
      </div>
      {scan ? <div className="latest-scan-hero"><div><p className="eyebrow">Latest recommendation scan</p><h2>{scan.candidate_count} qualified candidates</h2><p>{scan.symbols.join(", ")} · {scan.evaluated_count} evaluated · {new Date(scan.scanned_at).toLocaleString()}</p></div><div className="scan-decision-metrics"><span><b>{scan.trade_count}</b>Trade</span><span><b>{scan.watch_count}</b>Watch</span><span><b>{scan.pass_count}</b>Pass</span></div></div> : <div className="empty-state">Run a Recommendations scan to populate live market and opportunity intelligence.</div>}
    </article>
    <article className="card engine-health-card">
      <div className="card-title"><span>Platform state</span><ShieldCheck size={18}/></div>
      <div className={`health-pill ${health?.healthy ? "good" : "warn"}`}>{dashboard ? "Research mode ready" : "API unavailable"}</div>
      {dashboard ? <div className="platform-status-list"><StatusRow label="API service" value={dashboard.platform.api}/><StatusRow label="Recommendation engine" value={dashboard.platform.recommendation_engine}/><StatusRow label="Schwab broker" value={dashboard.platform.broker}/><StatusRow label="Market data" value={dashboard.platform.market_data}/></div> : null}
    </article>
    <article className="card opportunities-card">
      <div className="card-title"><span>Today's opportunities</span><Activity size={18}/></div>
      {scan ? <><div className="opportunity-count"><strong>{scan.candidate_count}</strong><span>qualified candidates</span></div><div className="opportunity-breakdown"><span>{scan.trade_count} trade</span><span>{scan.watch_count} watch</span><span>{scan.rejected_count} rejected</span></div><p className="card-note">Latest outcome: {scan.outcome.replaceAll("_", " ")}</p></> : <div className="empty-state">No recommendation scan has been saved yet.</div>}
    </article>
    <article className="card"><div className="card-title"><span>Portfolio</span><BriefcaseBusiness size={18}/></div><div className="portfolio-state"><strong>{dashboard?.portfolio.status.replaceAll("_", " ") ?? "Unavailable"}</strong><p>{dashboard?.portfolio.message ?? "Portfolio status requires the API."}</p></div></article>
    <article className="card span-2"><div className="card-title"><span>Alerts & operating safeguards</span><BookOpen size={18}/></div><div className="alert-list">{dashboard?.alerts.map((alert,index)=><div key={`${alert.title}-${index}`}><span className="alert-severity">{alert.severity}</span><div><strong>{alert.title}</strong><p>{alert.message}</p></div></div>) ?? <div className="empty-state">No platform alerts available.</div>}</div></article>
  </section>;
}
