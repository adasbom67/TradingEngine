import { Activity, TrendingDown, TrendingUp } from "lucide-react";
import { CriticalEvents } from "./CriticalEvents";
import { Recommendations } from "./Recommendations";

export type RecommendationStrategyView = "CREDIT_SPREADS" | "LONG_STRADDLE";

type RecommendationsWorkspaceProps = {
  activeStrategy: RecommendationStrategyView;
  onStrategyChange: (strategy: RecommendationStrategyView) => void;
};

const strategies = [
  {
    id: "CREDIT_SPREADS" as const,
    label: "Credit Spreads",
    description: "Directional Bull Put and Bear Call opportunities",
    icon: TrendingUp,
    badge: "2 directions",
  },
  {
    id: "LONG_STRADDLE" as const,
    label: "Long Straddle",
    description: "Direction-neutral Critical Events opportunities",
    icon: Activity,
    badge: "Critical Events",
  },
];

export function RecommendationsWorkspace({
  activeStrategy,
  onStrategyChange,
}: RecommendationsWorkspaceProps) {
  return (
    <section className="recommendations-parent-workspace">
      <div className="strategy-workspace-heading">
        <div>
          <p className="eyebrow">STRATEGY RESEARCH</p>
          <h2>Recommendation strategies</h2>
          <p>Select a strategy family to scan, inspect, and monitor independently.</p>
        </div>
        <div className="strategy-direction-key" aria-label="Available strategy directions">
          <span><TrendingUp size={14} /> Bullish</span>
          <span><TrendingDown size={14} /> Bearish</span>
          <span><Activity size={14} /> Direction-neutral</span>
        </div>
      </div>

      <div className="recommendation-strategy-tabs" role="tablist" aria-label="Recommendation strategies">
        {strategies.map(({ id, label, description, icon: Icon, badge }) => (
          <button
            type="button"
            role="tab"
            aria-selected={activeStrategy === id}
            className={activeStrategy === id ? "strategy-tab active" : "strategy-tab"}
            key={id}
            onClick={() => onStrategyChange(id)}
          >
            <Icon size={20} />
            <span><strong>{label}</strong><small>{description}</small></span>
            <b>{badge}</b>
          </button>
        ))}
      </div>

      <div className="recommendation-strategy-content" role="tabpanel">
        {activeStrategy === "CREDIT_SPREADS" ? <Recommendations /> : <CriticalEvents />}
      </div>
    </section>
  );
}
