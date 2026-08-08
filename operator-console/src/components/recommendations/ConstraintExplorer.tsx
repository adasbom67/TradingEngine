import "./ConstraintExplorer.css";

type Props = {
  distribution: Record<string, number>;
  filterRejections: Record<string, number>;
  minimumDelta?: number | null;
  maximumDelta?: number | null;
};

const ORDER = ["<0.05","0.05-0.10","0.10-0.15","0.15-0.20","0.20-0.25","0.25-0.30","0.30-0.40",">=0.40","missing"];

export function ConstraintExplorer({distribution,filterRejections,minimumDelta,maximumDelta}: Props) {
  const rows = ORDER.map((label)=>[label, Number(distribution[label] ?? 0)] as const).filter(([,count])=>count>0);
  if (!rows.length) return null;
  const total = rows.reduce((s,[,c])=>s+c,0);
  const peak = Math.max(...rows.map(([,c])=>c),1);
  return <article className="card constraint-explorer">
    <div className="constraint-explorer-heading">
      <div><p className="eyebrow">CONSTRAINT EXPLORER</p><h3>Absolute put-delta distribution</h3><p>Raw option contracts seen before liquidity and spread-building rules.</p></div>
      <div className="constraint-current-range"><span>Current delta window</span><strong>{minimumDelta == null ? "—" : minimumDelta.toFixed(2)} → {maximumDelta == null ? "—" : maximumDelta.toFixed(2)}</strong></div>
    </div>
    <div className="constraint-explorer-summary">
      <div><span>Contracts observed</span><strong>{total.toLocaleString()}</strong></div>
      <div><span>Below minimum</span><strong>{Number(filterRejections.delta_below_minimum ?? 0).toLocaleString()}</strong></div>
      <div><span>Above maximum</span><strong>{Number(filterRejections.delta_above_maximum ?? 0).toLocaleString()}</strong></div>
    </div>
    <div className="delta-distribution">
      {rows.map(([label,count])=><div className="delta-bin" key={label}>
        <div className="delta-bin-label"><span>{label}</span><strong>{count.toLocaleString()}</strong></div>
        <div className="delta-bin-track"><span style={{width:`${Math.max((count/peak)*100,2)}%`}}/></div>
        <small>{((count/total)*100).toFixed(1)}%</small>
      </div>)}
    </div>
    <p className="constraint-explorer-note">Relaxing delta only moves contracts past the delta screen. Liquidity, width, credit and risk rules still apply afterward.</p>
  </article>;
}
