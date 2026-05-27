export function ScoreBar({ label, value }) {
  const safeValue = Math.max(0, Math.min(100, Number(value) || 0));

  return (
    <div className="scoreBar">
      <div className="scoreBarTop">
        <span>{label}</span>
        <strong>{safeValue.toFixed(1)}점</strong>
      </div>
      <div className="scoreTrack" aria-hidden="true">
        <span style={{ width: `${safeValue}%` }} />
      </div>
    </div>
  );
}
