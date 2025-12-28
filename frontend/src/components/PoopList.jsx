import { useEffect, useState } from 'react';
import './PoopList.css';

function PoopItem({ poop }) {
  const [age, setAge] = useState(poop.age_seconds || 0);

  useEffect(() => {
    const interval = setInterval(() => {
      setAge(prev => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const minutes = Math.floor(age / 60);
  const seconds = Math.floor(age % 60);

  return (
    <div className="poop-item">
      <div className="poop-info">
        <span className="poop-id">Poop {poop.id.substring(0, 8)}</span>
        <span className="poop-age">{minutes}m {seconds}s</span>
      </div>
      <div className="poop-location">
        Location: ({Math.round(poop.location[0])}, {Math.round(poop.location[1])})
      </div>
    </div>
  );
}

export function PoopList({ poops }) {
  if (!poops || poops.length === 0) {
    return (
      <div className="poop-list-container">
        <h2>Active Poops</h2>
        <div className="empty-state">No active poops detected</div>
      </div>
    );
  }

  return (
    <div className="poop-list-container">
      <h2>Active Poops</h2>
      <div className="poop-list">
        {poops.map(poop => (
          <PoopItem key={poop.id} poop={poop} />
        ))}
      </div>
    </div>
  );
}
