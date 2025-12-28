import { useState } from 'react';
import './VideoFeed.css';

export function VideoFeed() {
  const [error, setError] = useState(false);

  return (
    <div className="video-feed-container">
      <h2>Live Camera Feed</h2>
      <div className="video-wrapper">
        {error ? (
          <div className="video-error">
            <p>Unable to load video feed</p>
            <button onClick={() => setError(false)}>Retry</button>
          </div>
        ) : (
          <img
            src="/video/feed"
            alt="Live camera feed"
            onError={() => setError(true)}
            className="video-stream"
          />
        )}
      </div>
    </div>
  );
}
