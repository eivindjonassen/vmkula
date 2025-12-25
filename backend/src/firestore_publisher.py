"""
Firestore publisher for tournament predictions.

Implements:
- Publish tournament snapshots to predictions/latest
- Diff check before writing prediction history (cost optimization)
- Timestamp tracking for updates
"""

from datetime import datetime
from typing import Dict, Any, Optional
from google.cloud import firestore
from src.config import config


class FirestorePublisher:
    """Publish tournament predictions to Firestore with history tracking."""

    def __init__(self):
        """Initialize Firestore client."""
        # Initialize Firestore client
        # In test environment, db will be mocked
        try:
            self.db = firestore.Client(project=config.FIRESTORE_PROJECT_ID)
        except Exception:
            # Allow tests to mock this
            self.db = None

    def publish_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """
        Publish tournament snapshot to predictions/latest document.

        Args:
            snapshot: Tournament snapshot with:
                - groups: Dict[str, List[team standings]]
                - bracket: List[bracket matches]
                - ai_summary: str
                - favorites: List[str] (optional)
                - dark_horses: List[str] (optional)
        """
        # Add timestamp
        snapshot_with_timestamp = {
            **snapshot,
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Publish to predictions/latest
        doc_ref = self.db.collection("predictions").document("latest")
        doc_ref.set(snapshot_with_timestamp)

    def should_save_prediction_history(
        self, match_id: int, new_prediction: Dict[str, Any]
    ) -> bool:
        """
        Check if prediction has changed (diff check for cost optimization).

        Only save to history if winner OR reasoning has changed.

        Args:
            match_id: Match ID
            new_prediction: New prediction dictionary with winner and reasoning

        Returns:
            True if prediction should be saved to history, False otherwise
        """
        # Fetch latest history entry
        history_ref = (
            self.db.collection("matches")
            .document(str(match_id))
            .collection("history")
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(1)
        )

        latest_entries = history_ref.get()

        # Cold start: no history yet
        if not latest_entries:
            return True

        # Compare with latest entry
        latest_entry = latest_entries[0].to_dict()
        latest_winner = latest_entry.get("winner")
        latest_reasoning = latest_entry.get("reasoning")

        new_winner = new_prediction.get("winner")
        new_reasoning = new_prediction.get("reasoning")

        # Save if either winner OR reasoning has changed
        if latest_winner != new_winner or latest_reasoning != new_reasoning:
            return True

        return False

    def save_prediction_history(
        self, match_id: int, prediction: Dict[str, Any]
    ) -> None:
        """
        Save prediction to history sub-collection.

        Path: matches/{match_id}/history/{timestamp}

        Args:
            match_id: Match ID
            prediction: Prediction dictionary to save
        """
        # Add timestamp
        prediction_with_timestamp = {
            **prediction,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Save to sub-collection
        history_ref = (
            self.db.collection("matches")
            .document(str(match_id))
            .collection("history")
            .document()  # Auto-generate document ID
        )

        history_ref.set(prediction_with_timestamp)
