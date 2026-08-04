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
import type { DashboardData, Health, Page } from "./types";
import { Dashboard } from "./pages/Dashboard";
import { Backtesting } from "./pages/Backtesting";
import { Recommendations } from "./pages/Recommendations";
import { ComingSoon } from "./components/common/ComingSoon";

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

  useEffect(() => {
    const refresh = () => {
      fetch("http://127.0.0.1:8001/api/version")
        .then((response) => response.json())
        .then((data) => setVersion(data.version))
        .catch(() => setVersion("offline"));
      fetch("http://127.0.0.1:8001/api/health")
        .then((response) => response.json())
        .then(setHealth)
        .catch(() => setHealth(null));
      fetch("http://127.0.0.1:8001/api/dashboard")
        .then((response) => response.json())
        .then(setDashboard)
        .catch(() => setDashboard(null));
    };
    refresh();
    const timer = window.setInterval(refresh, 30000);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">TE</span>
          <div><strong>TradingEngine</strong><small>Workstation</small></div>
        </div>
        <nav>
          {pages.map(({ label, icon: Icon }) => (
            <button key={label} onClick={() => setPage(label)} className={page === label ? "nav-item active" : "nav-item"}>
              <Icon size={18} /><span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-footer"><span className="status-dot"/><span>Read-only mode</span></div>
      </aside>
      <main>
        <header className="topbar">
          <div><p className="eyebrow">{page === "Dashboard" ? "TRADING DAY WORKSPACE" : "RESEARCH WORKSPACE"}</p><h1>{page === "Dashboard" ? "Command Center" : page}</h1></div>
          <div className="version">v{version}</div>
        </header>
        {page === "Dashboard" ? <Dashboard health={health} dashboard={dashboard}/> : page === "Backtesting" ? <Backtesting/> : page === "Recommendations" ? <Recommendations/> : <ComingSoon page={page}/>}
      </main>
    </div>
  );
}
