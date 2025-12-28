"""RTMP stream capture module."""

import cv2
import logging
import time
from typing import Iterator
import numpy as np


class StreamCapture:
    """Handles RTMP stream connection and frame extraction."""

    def __init__(self, config: dict):
        """
        Initialize stream capture.

        Args:
            config: Stream configuration dict with 'url' and 'reconnect_delay'
        """
        self.logger = logging.getLogger(__name__)
        self.url = config['url']
        self.reconnect_delay = config['reconnect_delay']
        self.cap = None
        self._connect()

    def _connect(self):
        """Connect to RTMP stream."""
        self.logger.info(f"Connecting to stream: {self.url}")
        self.cap = cv2.VideoCapture(self.url)

        if not self.cap.isOpened():
            self.logger.error(f"Failed to connect to stream: {self.url}")
            raise ConnectionError(f"Cannot connect to RTMP stream: {self.url}")

        self.logger.info("Stream connected successfully")

    def _reconnect(self):
        """Attempt to reconnect to stream."""
        self.logger.warning(f"Connection lost. Reconnecting in {self.reconnect_delay}s...")
        time.sleep(self.reconnect_delay)

        if self.cap:
            self.cap.release()

        self._connect()

    def get_frames(self) -> Iterator[np.ndarray]:
        """
        Generate frames from the stream.

        Yields:
            numpy.ndarray: Frame from the stream

        Handles reconnection automatically if stream is interrupted.
        """
        while True:
            ret, frame = self.cap.read()

            if not ret:
                self.logger.warning("Failed to read frame")
                self._reconnect()
                continue

            yield frame

    def release(self):
        """Release the stream capture."""
        if self.cap:
            self.cap.release()
            self.logger.info("Stream released")
