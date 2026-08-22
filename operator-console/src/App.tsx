import {
  Activity,
  BarChart3,
  BookOpen,
  BriefcaseBusiness,
  Gauge,
  Settings,
  ShieldCheck,
} from "lucide-react";
import { useEffect, useState } from "react";
import type { CriticalEventAlert, CriticalEventMonitorStatus, DashboardData, Health, Page } from "./types";
import { Dashboard } from "./pages/Dashboard";
import { Backtesting } from "./pages/Backtesting";
import { RecommendationsWorkspace, type RecommendationStrategyView } from "./pages/RecommendationsWorkspace";
import { PaperTrading } from "./pages/PaperTrading";
import { ComingSoon } from "./components/common/ComingSoon";
import { apiUrl } from "./api/client";

const pages: Array<{ label: Page; icon: typeof Gauge }> = [
  { label: "Dashboard", icon: Gauge },
  { label: "Backtesting", icon: BookOpen },
  { label: "Optimization", icon: BarChart3 },
  { label: "Walk Forward", icon: BarChart3 },
  { label: "Recommendations", icon: Activity },
  { label: "Paper Trading", icon: Activity },
  { label: "Live Trading", icon: Activity },
  { label: "Portfolio", icon: BriefcaseBusiness },
  { label: "Operations", icon: ShieldCheck },
  { label: "Settings", icon: Settings },
];

export function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [version, setVersion] = useState("…");
  const [page, setPage] = useState<Page>("Dashboard");
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [criticalAlert, setCriticalAlert] = useState<CriticalEventAlert | null>(null);
  const [recommendationStrategy, setRecommendationStrategy] = useState<RecommendationStrategyView>("CREDIT_SPREADS");

  useEffect(() => {
    const refresh = () => {
      fetch(apiUrl("/api/version"))
        .then((response) => response.json())
        .then((data) => setVersion(data.version))
        .catch(() => setVersion("offline"));

      fetch(apiUrl("/api/health"))
        .then((response) => response.json())
        .then(setHealth)
        .catch(() => setHealth(null));

      fetch(apiUrl("/api/dashboard"))
        .then((response) => response.json())
        .then(setDashboard)
        .catch(() => setDashboard(null));
    };

    refresh();
    const timer = window.setInterval(refresh, 30000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    let lastAlertId = window.sessionStorage.getItem("critical-event-last-alert");
    const refresh = () => fetch(apiUrl("/api/critical-events/monitor"))
      .then((response) => response.json())
      .then((status: CriticalEventMonitorStatus) => {
        const newest = status.alerts.length ? status.alerts[status.alerts.length - 1] : undefined;
        if (newest && newest.id !== lastAlertId) {
          lastAlertId = newest.id;
          window.sessionStorage.setItem("critical-event-last-alert", newest.id);
          setCriticalAlert(newest);
          playCriticalAlert();
        }
      }).catch(() => undefined);
    refresh();
    const timer = window.setInterval(refresh, 15000);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">TE</span>
          <div>
            <strong>TradingEngine</strong>
            <small>Workstation</small>
          </div>
        </div>

        <nav>
          {pages.map(({ label, icon: Icon }) => (
            <button
              key={label}
              onClick={() => setPage(label)}
              className={page === label ? "nav-item active" : "nav-item"}
            >
              <Icon size={18} />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <span className="status-dot" />
          <span>Read-only mode</span>
        </div>
      </aside>

      <main>
        <header className="topbar">
          <div>
            <p className="eyebrow">
              {page === "Dashboard"
                ? "TRADING DAY WORKSPACE"
                : page === "Paper Trading"
                  ? "SIMULATION WORKSPACE"
                  : "RESEARCH WORKSPACE"}
            </p>
            <h1>{page === "Dashboard" ? "Command Center" : page}</h1>
          </div>
          <div className="version">v{version}</div>
        </header>

        {page === "Dashboard" ? (
          <Dashboard health={health} dashboard={dashboard} />
        ) : page === "Backtesting" ? (
          <Backtesting />
        ) : page === "Recommendations" ? (
          <RecommendationsWorkspace activeStrategy={recommendationStrategy} onStrategyChange={setRecommendationStrategy} />
        ) : page === "Paper Trading" ? (
          <PaperTrading />
        ) : (
          <ComingSoon page={page} />
        )}
      </main>
      {criticalAlert && <div className="global-critical-alert" role="alert"><div><p className="eyebrow">CONFIRMED CRITICAL EVENT</p><strong>{criticalAlert.symbol} · {criticalAlert.score}/10</strong><span>{criticalAlert.option.expiration} · ${criticalAlert.option.strike.toFixed(0)} ATM straddle</span></div><button type="button" onClick={() => { setPage("Recommendations"); setRecommendationStrategy("LONG_STRADDLE"); setCriticalAlert(null); }}>Review</button><button type="button" onClick={() => setCriticalAlert(null)}>Dismiss</button></div>}
    </div>
  );
}

function playCriticalAlert() {
  const AudioContextClass = window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AudioContextClass) return;
  const context = new AudioContextClass();
  [0, .22, .44].forEach((delay) => {
    const oscillator = context.createOscillator(); const gain = context.createGain();
    oscillator.frequency.value = 880; gain.gain.setValueAtTime(.2, context.currentTime + delay); gain.gain.exponentialRampToValueAtTime(.001, context.currentTime + delay + .16);
    oscillator.connect(gain); gain.connect(context.destination); oscillator.start(context.currentTime + delay); oscillator.stop(context.currentTime + delay + .16);
  });
}
