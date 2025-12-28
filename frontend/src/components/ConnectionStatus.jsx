import './ConnectionStatus.css';

export function ConnectionStatus({ isConnected }) {
  return (
    <div className="connection-status">
      <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
        {isConnected ? 'Connected' : 'Disconnected'}
      </span>
    </div>
  );
}
