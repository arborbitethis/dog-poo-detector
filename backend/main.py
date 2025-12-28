"""Main entry point for the dog poop detector system."""

import yaml
import logging
from pathlib import Path

from capture import StreamCapture
from detector import Detector
from event_detector import EventDetector
from poop_tracker import PoopTracker
from state_manager import StateManager
from web_server import WebServer
from frame_annotator import FrameAnnotator


def load_config(config_path: str = "config/config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    """Run the dog poop detection system."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Load configuration
    config = load_config()
    logger.info("Configuration loaded")

    # Initialize web server and frame annotator
    web_server = WebServer(config['web_server'])
    frame_annotator = FrameAnnotator()

    # Initialize components
    capture = StreamCapture(config['stream'])
    detector = Detector(config['detection'])
    event_detector = EventDetector(config['pooping_detection'])

    # Initialize poop tracker with event callback
    poop_tracker = PoopTracker(
        config['tracking'],
        event_callback=web_server.broadcast_event_sync
    )
    state_manager = StateManager(config['alerts'])

    # Start web server in background
    web_server.start()
    logger.info("Starting dog poop detection system...")

    try:
        # Main processing loop
        for frame in capture.get_frames():
            # Run YOLO detection
            detections = detector.detect(frame)

            # Detect pooping events
            pooping_events = event_detector.process(detections)

            # Update poop tracking
            poop_tracker.update(detections, pooping_events)

            # Get current state
            current_state = poop_tracker.get_state()

            # Update state and generate alerts
            state_manager.update(current_state)

            # Annotate frame and update web server
            annotated_frame = frame_annotator.annotate(frame, detections, current_state)
            web_server.update_frame(annotated_frame)
            web_server.update_state(current_state)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        capture.release()
        web_server.stop()


if __name__ == "__main__":
    main()
