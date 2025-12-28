"""Poop instance tracking module."""

import logging
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class PoopInstance:
    """Represents a single poop deposit being tracked."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    location: tuple = (0, 0)  # (x, y) center point
    bbox: tuple = (0, 0, 0, 0)  # (x1, y1, x2, y2)
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending | active | cleaned
    deposited_by: Optional[str] = None  # dog tracking ID
    missing_frames: int = 0
    cleanup_candidate_frames: int = 0


class PoopTracker:
    """Maintains persistent tracking of poop instances across frames."""

    def __init__(self, config: dict, event_callback: Optional[Callable] = None):
        """
        Initialize poop tracker.

        Args:
            config: Tracking configuration with 'iou_threshold', 'stale_threshold', 'cleanup_confirm_frames'
            event_callback: Optional callback function for state change events
        """
        self.logger = logging.getLogger(__name__)
        self.iou_threshold = config['iou_threshold']
        self.stale_threshold = config['stale_threshold']
        self.cleanup_confirm_frames = config['cleanup_confirm_frames']
        self.event_callback = event_callback

        self.active_poops: List[PoopInstance] = []
        self.cleaned_count = 0
        self.total_deposits = 0

    def _calculate_iou(self, bbox1: tuple, bbox2: tuple) -> float:
        """
        Calculate Intersection over Union (IoU) between two bounding boxes.

        Args:
            bbox1: First bounding box (x1, y1, x2, y2)
            bbox2: Second bounding box (x1, y1, x2, y2)

        Returns:
            IoU score (0.0 to 1.0)
        """
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2

        # Calculate intersection
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)

        if x2_i < x1_i or y2_i < y1_i:
            return 0.0

        intersection = (x2_i - x1_i) * (y2_i - y1_i)

        # Calculate union
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0.0

    def update(self, detections: List, pooping_events: List):
        """
        Update poop tracking with new detections and pooping events.

        Args:
            detections: List of Detection objects from current frame
            pooping_events: List of pooping event locations from EventDetector
        """
        # Extract poop detections
        poop_detections = [d for d in detections if d.class_name == 'poop']
        person_detections = [d for d in detections if d.class_name == 'person']

        # Match detections to existing tracks
        matched_indices = set()

        for poop in self.active_poops:
            best_iou = 0
            best_detection = None

            for i, detection in enumerate(poop_detections):
                if i in matched_indices:
                    continue

                iou = self._calculate_iou(poop.bbox, detection.bbox)
                if iou > best_iou and iou > self.iou_threshold:
                    best_iou = iou
                    best_detection = (i, detection)

            if best_detection:
                idx, detection = best_detection
                matched_indices.add(idx)

                # Update existing track
                poop.bbox = detection.bbox
                poop.location = detection.center
                poop.last_seen = datetime.now()
                poop.missing_frames = 0
                poop.cleanup_candidate_frames = 0

                # Promote pending to active
                if poop.status == "pending":
                    poop.status = "active"
                    self.logger.info(f"Poop {poop.id} confirmed as active")
                    if self.event_callback:
                        self.event_callback("poop_confirmed", {
                            "id": poop.id,
                            "location": poop.location
                        })
            else:
                # Track not matched in this frame
                poop.missing_frames += 1

                # Check for cleanup by humans
                if self._is_human_nearby(poop, person_detections):
                    poop.cleanup_candidate_frames += 1

                    if poop.cleanup_candidate_frames >= self.cleanup_confirm_frames:
                        poop.status = "cleaned"
                        self.cleaned_count += 1
                        self.logger.info(f"Poop {poop.id} marked as cleaned")
                        if self.event_callback:
                            self.event_callback("poop_cleaned", {
                                "id": poop.id,
                                "location": poop.location
                            })
                else:
                    poop.cleanup_candidate_frames = 0

        # Create new tracks for unmatched detections
        for i, detection in enumerate(poop_detections):
            if i not in matched_indices:
                new_poop = PoopInstance(
                    location=detection.center,
                    bbox=detection.bbox,
                    status="active"
                )
                self.active_poops.append(new_poop)
                self.total_deposits += 1
                self.logger.info(f"New poop detected: {new_poop.id}")
                if self.event_callback:
                    self.event_callback("poop_detected", {
                        "id": new_poop.id,
                        "location": new_poop.location,
                        "bbox": new_poop.bbox
                    })

        # Create pending tracks for pooping events
        for event_location in pooping_events:
            pending_poop = PoopInstance(
                location=event_location,
                status="pending"
            )
            self.active_poops.append(pending_poop)
            self.logger.info(f"Pooping event detected, pending confirmation: {pending_poop.id}")

        # Remove stale or cleaned tracks
        self.active_poops = [
            p for p in self.active_poops
            if p.status != "cleaned" and p.missing_frames < self.stale_threshold
        ]

    def _is_human_nearby(self, poop: PoopInstance, person_detections: List, threshold: float = 100) -> bool:
        """
        Check if a human is near a poop location.

        Args:
            poop: PoopInstance to check
            person_detections: List of person detections
            threshold: Distance threshold in pixels

        Returns:
            True if human is nearby
        """
        poop_x, poop_y = poop.location

        for person in person_detections:
            person_x, person_y = person.center
            distance = ((poop_x - person_x) ** 2 + (poop_y - person_y) ** 2) ** 0.5

            if distance < threshold:
                return True

        return False

    def get_state(self) -> Dict:
        """
        Get current tracking state.

        Returns:
            Dict with active poops, cleaned count, and total deposits
        """
        return {
            "active_poops": [p for p in self.active_poops if p.status == "active"],
            "pending_poops": [p for p in self.active_poops if p.status == "pending"],
            "cleaned_count": self.cleaned_count,
            "total_deposits": self.total_deposits
        }
