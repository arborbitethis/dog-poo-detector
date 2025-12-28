"""Demo script to simulate poop detection and cleanup workflow."""

import cv2
import yaml
import logging
import time
import numpy as np
from pathlib import Path

# Import our components
import sys
sys.path.append('backend')

from detector import Detection
from poop_tracker import PoopTracker, PoopInstance
from frame_annotator import FrameAnnotator
from web_server import WebServer
from state_manager import StateManager


def load_config(config_path: str = "config/config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


class DemoSimulator:
    """Simulates poop detection and cleanup workflow."""

    def __init__(self, image_path: str):
        """Initialize demo simulator."""
        self.logger = logging.getLogger(__name__)

        # Load image
        self.logger.info(f"Loading image: {image_path}")
        self.base_frame = cv2.imread(image_path)
        if self.base_frame is None:
            raise ValueError(f"Could not load image: {image_path}")

        self.height, self.width = self.base_frame.shape[:2]
        self.logger.info(f"Image size: {self.width}x{self.height}")

        # Load config
        self.config = load_config()

        # Initialize components
        self.frame_annotator = FrameAnnotator()
        self.web_server = WebServer(self.config['web_server'])
        self.poop_tracker = PoopTracker(
            self.config['tracking'],
            event_callback=self.web_server.broadcast_event_sync
        )
        self.state_manager = StateManager(self.config['alerts'])

        # Start web server
        self.web_server.start()
        self.logger.info("Web server started - Open http://localhost:8080")

    def create_dog_detection(self, x: int, y: int, w: int, h: int) -> Detection:
        """Create a simulated dog detection."""
        return Detection(
            class_id=16,
            class_name='dog',
            confidence=0.95,
            bbox=(x, y, x + w, y + h)
        )

    def create_poop_detection(self, x: int, y: int, size: int = 30) -> Detection:
        """Create a simulated poop detection."""
        return Detection(
            class_id=99,  # Custom class
            class_name='poop',
            confidence=0.85,
            bbox=(x - size//2, y - size//2, x + size//2, y + size//2)
        )

    def create_person_detection(self, x: int, y: int, w: int, h: int) -> Detection:
        """Create a simulated person detection."""
        return Detection(
            class_id=0,
            class_name='person',
            confidence=0.92,
            bbox=(x, y, x + w, y + h)
        )

    def update_and_display(self, detections: list, delay: float = 2.0):
        """Update tracker, annotate frame, and send to web server."""
        # Update tracker
        self.poop_tracker.update(detections, [])

        # Get current state
        current_state = self.poop_tracker.get_state()

        # Update state manager
        self.state_manager.update(current_state)

        # Annotate frame
        annotated_frame = self.frame_annotator.annotate(
            self.base_frame.copy(),
            detections,
            current_state
        )

        # Update web server
        self.web_server.update_frame(annotated_frame)
        self.web_server.update_state(current_state)

        # Display locally
        cv2.imshow('Demo - Dog Poop Detector', annotated_frame)
        cv2.waitKey(int(delay * 1000))

    def run_demo(self):
        """Run the complete demo workflow."""
        self.logger.info("Starting demo simulation...")
        self.logger.info("Open http://localhost:8080 to view dashboard")

        print("\n" + "="*60)
        print("DOG POOP DETECTOR - DEMO MODE")
        print("="*60)
        print("Dashboard: http://localhost:8080")
        print("="*60 + "\n")

        time.sleep(2)  # Give user time to open browser

        # SCENE 1: Dog enters and poops (multiple locations)
        print("SCENE 1: Dog enters the yard...")
        dog_x, dog_y = self.width // 3, self.height // 2
        detections = [self.create_dog_detection(dog_x, dog_y, 120, 80)]
        self.update_and_display(detections, delay=2)

        print("SCENE 2: Dog is in pooping posture (simulating)...")
        # In real system, event_detector would detect this
        # For demo, we'll just show dog in position
        self.update_and_display(detections, delay=2)

        print("SCENE 3: First poop appears!")
        poop1_x, poop1_y = dog_x + 50, dog_y + 60
        detections.append(self.create_poop_detection(poop1_x, poop1_y))
        self.update_and_display(detections, delay=3)

        print("SCENE 4: Dog moves to another location...")
        dog_x2, dog_y2 = self.width // 2, self.height // 3
        detections = [
            self.create_dog_detection(dog_x2, dog_y2, 120, 80),
            self.create_poop_detection(poop1_x, poop1_y)  # First poop still there
        ]
        self.update_and_display(detections, delay=2)

        print("SCENE 5: Second poop appears!")
        poop2_x, poop2_y = dog_x2 + 50, dog_y2 + 60
        detections.append(self.create_poop_detection(poop2_x, poop2_y))
        self.update_and_display(detections, delay=3)

        print("SCENE 6: Dog leaves, both poops remain...")
        detections = [
            self.create_poop_detection(poop1_x, poop1_y),
            self.create_poop_detection(poop2_x, poop2_y)
        ]
        self.update_and_display(detections, delay=3)

        print("SCENE 7: Poops aging (waiting 5 seconds)...")
        for i in range(5):
            print(f"  Waiting... {i+1}/5 seconds")
            self.update_and_display(detections, delay=1)

        print("SCENE 8: Human approaches first poop...")
        person_x, person_y = poop1_x - 100, poop1_y - 150
        detections = [
            self.create_person_detection(person_x, person_y, 80, 200),
            self.create_poop_detection(poop1_x, poop1_y),
            self.create_poop_detection(poop2_x, poop2_y)
        ]
        self.update_and_display(detections, delay=2)

        print("SCENE 9: Human picks up first poop (poop disappears)...")
        # Simulate cleanup - poop near person disappears
        for i in range(self.config['tracking']['cleanup_confirm_frames'] + 5):
            detections = [
                self.create_person_detection(person_x, person_y, 80, 200),
                # First poop gone - only second remains
                self.create_poop_detection(poop2_x, poop2_y)
            ]
            self.update_and_display(detections, delay=0.2)
            if i == 0:
                print("  First poop is being picked up...")
            if i == self.config['tracking']['cleanup_confirm_frames']:
                print("  First poop confirmed cleaned!")

        print("SCENE 10: Human moves to second poop...")
        person_x2, person_y2 = poop2_x - 100, poop2_y - 150
        detections = [
            self.create_person_detection(person_x2, person_y2, 80, 200),
            self.create_poop_detection(poop2_x, poop2_y)
        ]
        self.update_and_display(detections, delay=2)

        print("SCENE 11: Human picks up second poop...")
        for i in range(self.config['tracking']['cleanup_confirm_frames'] + 5):
            detections = [
                self.create_person_detection(person_x2, person_y2, 80, 200),
                # Second poop gone
            ]
            self.update_and_display(detections, delay=0.2)
            if i == 0:
                print("  Second poop is being picked up...")
            if i == self.config['tracking']['cleanup_confirm_frames']:
                print("  Second poop confirmed cleaned!")

        print("SCENE 12: All clean! Human leaves...")
        detections = []
        self.update_and_display(detections, delay=2)

        print("\n" + "="*60)
        print("DEMO COMPLETE!")
        print("="*60)
        print(f"Final Stats:")
        state = self.poop_tracker.get_state()
        print(f"  Active Poops: {len(state['active_poops'])}")
        print(f"  Cleaned: {state['cleaned_count']}")
        print(f"  Total Deposits: {state['total_deposits']}")
        print("="*60)
        print("\nWeb server still running at http://localhost:8080")
        print("Press 'q' in the image window to quit")
        print("="*60 + "\n")

        # Keep window open
        while True:
            key = cv2.waitKey(100)
            if key == ord('q'):
                break

        cv2.destroyAllWindows()
        self.web_server.stop()


def main():
    """Run demo."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Check if image exists
    image_path = "IMG_3490.jpeg"
    if not Path(image_path).exists():
        print(f"Error: Image not found: {image_path}")
        print("Please ensure IMG_3490.jpeg is in the current directory")
        return

    # Run demo
    demo = DemoSimulator(image_path)
    demo.run_demo()


if __name__ == "__main__":
    main()
