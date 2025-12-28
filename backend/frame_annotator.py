"""Frame annotation module for drawing poop locations and detections."""

import cv2
import numpy as np
from typing import List, Dict
from datetime import datetime


class FrameAnnotator:
    """Annotates video frames with poop locations and detection information."""

    # Color definitions (BGR format for OpenCV)
    COLOR_PENDING = (0, 255, 255)  # Yellow
    COLOR_ACTIVE = (0, 0, 255)     # Red
    COLOR_CLEANED = (0, 255, 0)    # Green
    COLOR_DOG = (255, 128, 0)      # Blue
    COLOR_PERSON = (128, 255, 128) # Light green

    def __init__(self):
        """Initialize frame annotator."""
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.5
        self.thickness = 2

    def annotate(self, frame: np.ndarray, detections: List, tracker_state: Dict) -> np.ndarray:
        """
        Annotate frame with detections and poop tracking information.

        Args:
            frame: Input frame as numpy array
            detections: List of Detection objects from current frame
            tracker_state: Current state from PoopTracker

        Returns:
            Annotated frame
        """
        # Create a copy to avoid modifying original
        annotated = frame.copy()

        # Draw detection bounding boxes (dogs and persons)
        for detection in detections:
            if detection.class_name == 'dog':
                self._draw_detection(annotated, detection, self.COLOR_DOG, "Dog")
            elif detection.class_name == 'person':
                self._draw_detection(annotated, detection, self.COLOR_PERSON, "Person")

        # Draw active poops
        for poop in tracker_state.get('active_poops', []):
            age_seconds = (datetime.now() - poop.first_seen).total_seconds()
            self._draw_poop(annotated, poop, self.COLOR_ACTIVE, age_seconds)

        # Draw pending poops
        for poop in tracker_state.get('pending_poops', []):
            self._draw_poop(annotated, poop, self.COLOR_PENDING, 0)

        # Draw status overlay
        self._draw_status_overlay(annotated, tracker_state)

        return annotated

    def _draw_detection(self, frame: np.ndarray, detection, color: tuple, label: str):
        """Draw a detection bounding box."""
        x1, y1, x2, y2 = [int(v) for v in detection.bbox]

        # Draw rectangle
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        # Draw label background
        label_text = f"{label} {detection.confidence:.2f}"
        (text_width, text_height), _ = cv2.getTextSize(
            label_text, self.font, self.font_scale, self.thickness
        )

        cv2.rectangle(
            frame,
            (x1, y1 - text_height - 10),
            (x1 + text_width, y1),
            color,
            -1
        )

        # Draw label text
        cv2.putText(
            frame,
            label_text,
            (x1, y1 - 5),
            self.font,
            self.font_scale,
            (255, 255, 255),
            self.thickness
        )

    def _draw_poop(self, frame: np.ndarray, poop, color: tuple, age_seconds: float):
        """Draw a poop instance marker."""
        x, y = [int(v) for v in poop.location]

        # Draw circle at location
        cv2.circle(frame, (x, y), 15, color, -1)
        cv2.circle(frame, (x, y), 15, (255, 255, 255), 2)

        # Draw age label
        if poop.status == 'active':
            age_minutes = int(age_seconds // 60)
            age_secs = int(age_seconds % 60)
            label = f"{age_minutes}m {age_secs}s"
        elif poop.status == 'pending':
            label = "PENDING"
        else:
            label = poop.status.upper()

        # Draw label background
        (text_width, text_height), _ = cv2.getTextSize(
            label, self.font, self.font_scale, self.thickness
        )

        label_x = x - text_width // 2
        label_y = y + 30

        cv2.rectangle(
            frame,
            (label_x - 5, label_y - text_height - 5),
            (label_x + text_width + 5, label_y + 5),
            color,
            -1
        )

        # Draw label text
        cv2.putText(
            frame,
            label,
            (label_x, label_y),
            self.font,
            self.font_scale,
            (255, 255, 255),
            self.thickness
        )

        # Draw bounding box if available
        if poop.bbox != (0, 0, 0, 0):
            x1, y1, x2, y2 = [int(v) for v in poop.bbox]
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    def _draw_status_overlay(self, frame: np.ndarray, tracker_state: Dict):
        """Draw status overlay in top-left corner."""
        active_count = len(tracker_state.get('active_poops', []))
        pending_count = len(tracker_state.get('pending_poops', []))
        cleaned_count = tracker_state.get('cleaned_count', 0)
        total_count = tracker_state.get('total_deposits', 0)

        # Background rectangle
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (300, 130), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # Status text
        status_lines = [
            f"Active: {active_count}",
            f"Pending: {pending_count}",
            f"Cleaned: {cleaned_count}",
            f"Total: {total_count}"
        ]

        y_offset = 35
        for line in status_lines:
            cv2.putText(
                frame,
                line,
                (20, y_offset),
                self.font,
                0.6,
                (255, 255, 255),
                2
            )
            y_offset += 25
