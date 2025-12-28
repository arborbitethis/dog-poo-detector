import './MetricsCard.css';

export function MetricsCard({ metrics }) {
  return (
    <div className="metrics-card">
      <h2>Statistics</h2>
      <div className="metrics-grid">
        <div className="metric">
          <span className="metric-label">Active Poops</span>
          <span className="metric-value active">{metrics.active_count || 0}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Pending</span>
          <span className="metric-value pending">{metrics.pending_count || 0}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Cleaned</span>
          <span className="metric-value cleaned">{metrics.cleaned_count || 0}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Total Deposits</span>
          <span className="metric-value total">{metrics.total_deposits || 0}</span>
        </div>
      </div>
    </div>
  );
}
