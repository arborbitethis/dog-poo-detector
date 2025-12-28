"""Pooping event detection module."""

import logging
from typing import List, Dict, Tuple
from collections import deque
from datetime import datetime, timedelta


class DogTrack:
    """Represents a tracked dog over time."""

    def __init__(self, detection):
        """Initialize dog track from detection."""
        self.positions = deque(maxlen=90)  # ~3 seconds at 30fps
        self.last_update = datetime.now()
        self.add_position(detection)

    def add_position(self, detection):
        """Add new position to track."""
        self.positions.append({
            'center': detection.center,
            'bbox': detection.bbox,
            'aspect_ratio': detection.aspect_ratio,
            'timestamp': datetime.now()
        })
        self.last_update = datetime.now()

    def is_stale(self, max_age_seconds: float = 1.0) -> bool:
        """Check if track is stale (not updated recently)."""
        age = (datetime.now() - self.last_update).total_seconds()
        return age > max_age_seconds

    def get_average_movement(self) -> float:
        """Calculate average movement over tracked positions."""
        if len(self.positions) < 2:
            return float('inf')

        total_movement = 0
        for i in range(1, len(self.positions)):
            x1, y1 = self.positions[i-1]['center']
            x2, y2 = self.positions[i]['center']
            distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            total_movement += distance

        return total_movement / (len(self.positions) - 1)

    def get_average_aspect_ratio(self) -> float:
        """Get average aspect ratio over tracked positions."""
        if not self.positions:
            return 1.0

        return sum(p['aspect_ratio'] for p in self.positions) / len(self.positions)

    def get_track_duration(self) -> float:
        """Get duration of track in seconds."""
        if len(self.positions) < 2:
            return 0.0

        return (self.positions[-1]['timestamp'] - self.positions[0]['timestamp']).total_seconds()

    def get_ground_location(self) -> Tuple[float, float]:
        """Get location on ground below dog (bottom center of bbox)."""
        if not self.positions:
            return (0, 0)

        last_bbox = self.positions[-1]['bbox']
        x1, y1, x2, y2 = last_bbox
        center_x = (x1 + x2) / 2
        bottom_y = y2

        return (center_x, bottom_y)


class EventDetector:
    """Detects pooping and cleanup events using behavioral heuristics."""

    def __init__(self, config: dict):
        """
        Initialize event detector.

        Args:
            config: Pooping detection configuration with 'stationary_threshold', 'aspect_ratio_threshold'
        """
        self.logger = logging.getLogger(__name__)
        self.stationary_threshold = config['stationary_threshold']
        self.aspect_ratio_threshold = config['aspect_ratio_threshold']

        self.dog_tracks: Dict[int, DogTrack] = {}
        self.next_track_id = 0
        self.movement_threshold = 5.0  # pixels per frame for stationary detection

    def process(self, detections: List) -> List[Tuple[float, float]]:
        """
        Process detections to identify pooping events.

        Args:
            detections: List of Detection objects

        Returns:
            List of ground locations where pooping events are detected
        """
        dog_detections = [d for d in detections if d.class_name == 'dog']
        pooping_events = []

        # Update tracks with new detections
        self._update_tracks(dog_detections)

        # Check each track for pooping behavior
        for track_id, track in list(self.dog_tracks.items()):
            if self._is_pooping(track):
                ground_location = track.get_ground_location()
                pooping_events.append(ground_location)
                self.logger.info(f"Pooping event detected for track {track_id} at {ground_location}")

        # Clean up stale tracks
        self.dog_tracks = {
            tid: track for tid, track in self.dog_tracks.items()
            if not track.is_stale()
        }

        return pooping_events

    def _update_tracks(self, dog_detections: List):
        """
        Update dog tracks with new detections.

        Args:
            dog_detections: List of dog detections
        """
        # Simple nearest-neighbor matching
        matched_tracks = set()
        matched_detections = set()

        for track_id, track in self.dog_tracks.items():
            if not track.positions:
                continue

            last_center = track.positions[-1]['center']
            best_distance = float('inf')
            best_detection_idx = None

            for i, detection in enumerate(dog_detections):
                if i in matched_detections:
                    continue

                distance = self._distance(last_center, detection.center)
                if distance < best_distance and distance < 100:  # 100 pixel threshold
                    best_distance = distance
                    best_detection_idx = i

            if best_detection_idx is not None:
                track.add_position(dog_detections[best_detection_idx])
                matched_tracks.add(track_id)
                matched_detections.add(best_detection_idx)

        # Create new tracks for unmatched detections
        for i, detection in enumerate(dog_detections):
            if i not in matched_detections:
                self.dog_tracks[self.next_track_id] = DogTrack(detection)
                self.next_track_id += 1

    def _is_pooping(self, track: DogTrack) -> bool:
        """
        Determine if a dog track indicates pooping behavior.

        Args:
            track: DogTrack to analyze

        Returns:
            True if dog appears to be pooping
        """
        # Need sufficient track duration
        if track.get_track_duration() < self.stationary_threshold:
            return False

        # Check if dog is stationary
        avg_movement = track.get_average_movement()
        if avg_movement > self.movement_threshold:
            return False

        # Check if dog is in squatting posture (aspect ratio)
        avg_aspect_ratio = track.get_average_aspect_ratio()
        if avg_aspect_ratio > self.aspect_ratio_threshold:
            return False

        return True

    def _distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points."""
        x1, y1 = point1
        x2, y2 = point2
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
