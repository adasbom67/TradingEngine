export function Metric({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string;
  tone?: "neutral" | "positive" | "negative";
}) {
  return (
    <article className="card metric-card">
      <small>{label}</small>
      <strong className={`metric-value ${tone}`}>{value}</strong>
    </article>
  );
}

