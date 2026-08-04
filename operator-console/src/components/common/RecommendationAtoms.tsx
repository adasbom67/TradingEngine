export function DecisionBadge({ decision }: { decision: string }) {
  return <span className={`decision-badge ${decision.toLowerCase()}`}>{decision}</span>;
}

export function Detail({ label, value }: { label: string; value: string }) {
  return <div className="detail-item"><small>{label}</small><strong>{value}</strong></div>;
}

function formatDelta(value: number | null) {
  if (value === null || Number.isNaN(value)) return "N/A";
  return `${value >= 0 ? "+" : ""}${value.toFixed(3)}`;
}

