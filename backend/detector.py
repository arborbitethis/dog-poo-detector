"""YOLO detection module."""

import logging
from typing import List, Dict
import numpy as np
from ultralytics import YOLO


class Detection:
    """Represents a single detection."""

    def __init__(self, class_id: int, class_name: str, confidence: float, bbox: tuple):
        """
        Initialize detection.

        Args:
            class_id: COCO class ID
            class_name: Class name (e.g., 'dog', 'person', 'poop')
            confidence: Detection confidence score
            bbox: Bounding box as (x1, y1, x2, y2)
        """
        self.class_id = class_id
        self.class_name = class_name
        self.confidence = confidence
        self.bbox = bbox

    @property
    def center(self) -> tuple:
        """Get center point of bounding box."""
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    @property
    def width(self) -> float:
        """Get width of bounding box."""
        return self.bbox[2] - self.bbox[0]

    @property
    def height(self) -> float:
        """Get height of bounding box."""
        return self.bbox[3] - self.bbox[1]

    @property
    def aspect_ratio(self) -> float:
        """Get aspect ratio (height/width)."""
        return self.height / self.width if self.width > 0 else 0


class Detector:
    """YOLO inference wrapper for detecting dogs, poop, and humans."""

    # COCO class IDs
    CLASS_PERSON = 0
    CLASS_DOG = 16

    def __init__(self, config: dict):
        """
        Initialize detector.

        Args:
            config: Detection configuration dict with 'model', 'confidence_threshold', 'inference_interval'
        """
        self.logger = logging.getLogger(__name__)
        self.model_path = config['model']
        self.confidence_threshold = config['confidence_threshold']
        self.inference_interval = config['inference_interval']
        self.frame_count = 0

        self.logger.info(f"Loading YOLO model: {self.model_path}")
        self.model = YOLO(self.model_path)
        self.logger.info("Model loaded successfully")

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Run detection on a frame.

        Args:
            frame: Input frame as numpy array

        Returns:
            List of Detection objects
        """
        self.frame_count += 1

        # Skip frames based on inference interval
        if self.frame_count % self.inference_interval != 0:
            return []

        # Run inference
        results = self.model(frame, verbose=False)

        detections = []
        for result in results:
            boxes = result.boxes

            for box in boxes:
                confidence = float(box.conf[0])

                # Filter by confidence threshold
                if confidence < self.confidence_threshold:
                    continue

                class_id = int(box.cls[0])
                class_name = result.names[class_id]
                bbox = box.xyxy[0].cpu().numpy().tolist()

                # Filter to relevant classes (person, dog, and any custom poop class)
                if class_id in [self.CLASS_PERSON, self.CLASS_DOG] or class_name == 'poop':
                    detections.append(Detection(class_id, class_name, confidence, bbox))

        return detections
