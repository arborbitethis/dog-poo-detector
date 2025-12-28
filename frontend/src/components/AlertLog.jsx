import './AlertLog.css';

function Alert({ alert }) {
  const time = new Date(alert.timestamp).toLocaleTimeString();
  const typeClass = alert.type.replace('_', '-');

  return (
    <div className={`alert alert-${typeClass}`}>
      <div className="alert-time">{time}</div>
      <div className="alert-content">
        <div className="alert-title">{alert.title}</div>
        <div className="alert-message">{alert.message}</div>
      </div>
    </div>
  );
}

export function AlertLog({ alerts }) {
  if (!alerts || alerts.length === 0) {
    return (
      <div className="alert-log-container">
        <h2>Alert Log</h2>
        <div className="empty-state">No alerts yet</div>
      </div>
    );
  }

  return (
    <div className="alert-log-container">
      <h2>Alert Log</h2>
      <div className="alert-log">
        {alerts.map((alert, index) => (
          <Alert key={index} alert={alert} />
        ))}
      </div>
    </div>
  );
}
