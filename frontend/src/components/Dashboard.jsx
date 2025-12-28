import { useState, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { ConnectionStatus } from './ConnectionStatus';
import { VideoFeed } from './VideoFeed';
import { MetricsCard } from './MetricsCard';
import { PoopList } from './PoopList';
import { AlertLog } from './AlertLog';
import './Dashboard.css';

export function Dashboard() {
  const { isConnected, lastMessage } = useWebSocket();
  const [metrics, setMetrics] = useState({
    active_count: 0,
    pending_count: 0,
    cleaned_count: 0,
    total_deposits: 0
  });
  const [activePoops, setActivePoops] = useState([]);
  const [alerts, setAlerts] = useState([]);

  // Fetch initial status
  useEffect(() => {
    fetch('/api/status')
      .then(res => res.json())
      .then(data => {
        setMetrics(data.metrics);
        setActivePoops(data.active_poops || []);
      })
      .catch(error => console.error('Error fetching status:', error));
  }, []);

  // Handle WebSocket messages
  useEffect(() => {
    if (!lastMessage) return;

    const { type, data, timestamp } = lastMessage;

    switch (type) {
      case 'status_update':
        setMetrics(data.metrics);
        setActivePoops(data.active_poops || []);
        break;

      case 'poop_detected':
        addAlert(
          'New Poop Detected!',
          `Location: (${Math.round(data.location[0])}, ${Math.round(data.location[1])})`,
          'poop-detected',
          timestamp
        );
        // Refresh status
        fetchStatus();
        break;

      case 'poop_confirmed':
        addAlert(
          'Poop Confirmed',
          `Poop ${data.id.substring(0, 8)} confirmed as active`,
          'poop-confirmed',
          timestamp
        );
        fetchStatus();
        break;

      case 'poop_cleaned':
        addAlert(
          'Poop Cleaned Up!',
          `Poop ${data.id.substring(0, 8)} has been cleaned`,
          'poop-cleaned',
          timestamp
        );
        fetchStatus();
        break;

      default:
        console.warn('Unknown message type:', type);
    }
  }, [lastMessage]);

  const fetchStatus = () => {
    fetch('/api/status')
      .then(res => res.json())
      .then(data => {
        setMetrics(data.metrics);
        setActivePoops(data.active_poops || []);
      })
      .catch(error => console.error('Error fetching status:', error));
  };

  const addAlert = (title, message, type, timestamp) => {
    const newAlert = {
      title,
      message,
      type,
      timestamp: timestamp || new Date().toISOString()
    };

    setAlerts(prev => [newAlert, ...prev].slice(0, 50)); // Keep last 50 alerts
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>🐕 Dog Poop Detector Dashboard</h1>
        <ConnectionStatus isConnected={isConnected} />
      </header>

      <div className="dashboard-content">
        <div className="main-section">
          <VideoFeed />
        </div>

        <div className="sidebar">
          <MetricsCard metrics={metrics} />
          <PoopList poops={activePoops} />
        </div>
      </div>

      <div className="alerts-section">
        <AlertLog alerts={alerts} />
      </div>
    </div>
  );
}
