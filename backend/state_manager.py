"""State management and alert generation module."""

import logging
from typing import Dict, Set
from datetime import datetime, timedelta


class StateManager:
    """Manages overall system state and generates alerts."""

    def __init__(self, config: dict):
        """
        Initialize state manager.

        Args:
            config: Alerts configuration with 'new_poop', 'cleanup', 'aged_minutes'
        """
        self.logger = logging.getLogger(__name__)
        self.alert_new_poop = config['new_poop']
        self.alert_cleanup = config['cleanup']
        self.aged_minutes = config['aged_minutes']

        self.known_poop_ids: Set[str] = set()
        self.last_state = {}

    def update(self, tracker_state: Dict):
        """
        Update state and generate alerts.

        Args:
            tracker_state: Current state from PoopTracker
        """
        active_poops = tracker_state.get('active_poops', [])
        cleaned_count = tracker_state.get('cleaned_count', 0)
        total_deposits = tracker_state.get('total_deposits', 0)

        # Check for new poop detections
        if self.alert_new_poop:
            current_ids = {poop.id for poop in active_poops}
            new_ids = current_ids - self.known_poop_ids

            for poop_id in new_ids:
                self._alert_new_poop(poop_id)
                self.known_poop_ids.add(poop_id)

        # Check for cleanups
        if self.alert_cleanup:
            prev_cleaned = self.last_state.get('cleaned_count', 0)
            if cleaned_count > prev_cleaned:
                cleanups = cleaned_count - prev_cleaned
                self._alert_cleanup(cleanups)

        # Check for aged poop
        for poop in active_poops:
            age_minutes = (datetime.now() - poop.first_seen).total_seconds() / 60
            if age_minutes >= self.aged_minutes:
                self._alert_aged_poop(poop)

        # Update state snapshot
        self.last_state = {
            'active_count': len(active_poops),
            'cleaned_count': cleaned_count,
            'total_deposits': total_deposits
        }

        # Log current status
        self._log_status(tracker_state)

    def _alert_new_poop(self, poop_id: str):
        """Generate alert for new poop detection."""
        self.logger.warning(f"ALERT: New poop detected! ID: {poop_id}")
        # TODO: Send notification (email, SMS, push notification, etc.)

    def _alert_cleanup(self, count: int):
        """Generate alert for poop cleanup."""
        self.logger.info(f"ALERT: Poop cleaned up! Count: {count}")
        # TODO: Send notification

    def _alert_aged_poop(self, poop):
        """Generate alert for aged uncleaned poop."""
        age_minutes = (datetime.now() - poop.first_seen).total_seconds() / 60
        self.logger.warning(
            f"ALERT: Poop {poop.id} has been uncleaned for {age_minutes:.1f} minutes! "
            f"Location: {poop.location}"
        )
        # TODO: Send notification

    def _log_status(self, tracker_state: Dict):
        """Log current system status."""
        active_count = len(tracker_state.get('active_poops', []))
        pending_count = len(tracker_state.get('pending_poops', []))
        cleaned_count = tracker_state.get('cleaned_count', 0)
        total_deposits = tracker_state.get('total_deposits', 0)

        self.logger.info(
            f"Status - Active: {active_count}, Pending: {pending_count}, "
            f"Cleaned: {cleaned_count}, Total: {total_deposits}"
        )

    def get_summary(self) -> Dict:
        """
        Get summary of current state.

        Returns:
            Dict with state summary
        """
        return self.last_state.copy()
