import pytest
from unittest.mock import MagicMock, patch
from src.firestore_publisher import FirestorePublisher


def test_publish_snapshot_basic():
    """Test publishing to predictions/latest document."""
    publisher = FirestorePublisher()
    snapshot = {
        "groups": {"A": []},
        "bracket": [],
        "ai_summary": "Summary text",
        "favorites": ["USA"],
        "dark_horses": ["Norway"],
    }

    # Mock Firestore client
    mock_db = MagicMock()
    publisher.db = mock_db

    publisher.publish_snapshot(snapshot)

    # Check if correct document was set
    mock_db.collection.assert_called_with("predictions")
    mock_db.collection().document.assert_called_with("latest")

    # Get the call arguments of set()
    call_args = mock_db.collection().document().set.call_args[0][0]
    assert call_args["ai_summary"] == "Summary text"
    assert "updated_at" in call_args


def test_history_diff_check_skip_identical():
    """CRITICAL TEST: Skip write if prediction unchanged."""
    publisher = FirestorePublisher()
    match_id = 1
    new_prediction = {"winner": "USA", "reasoning": "Strong form"}

    # Mock latest history entry to be identical
    mock_latest = MagicMock()
    mock_latest.to_dict.return_value = {"winner": "USA", "reasoning": "Strong form"}

    # Mock Firestore query
    mock_db = MagicMock()
    publisher.db = mock_db
    mock_db.collection().document().collection().order_by().limit().get.return_value = [
        mock_latest
    ]

    should_save = publisher.should_save_prediction_history(match_id, new_prediction)

    assert should_save is False


def test_history_diff_check_write_on_change():
    """CRITICAL TEST: Write new history entry if prediction differs."""
    publisher = FirestorePublisher()
    match_id = 1
    new_prediction = {"winner": "England", "reasoning": "Improved stats"}

    # Mock latest history entry to be different
    mock_latest = MagicMock()
    mock_latest.to_dict.return_value = {"winner": "USA", "reasoning": "Strong form"}

    mock_db = MagicMock()
    publisher.db = mock_db
    mock_db.collection().document().collection().order_by().limit().get.return_value = [
        mock_latest
    ]

    should_save = publisher.should_save_prediction_history(match_id, new_prediction)

    assert should_save is True


def test_history_path_correct():
    """Test sub-collection path: matches/{match_id}/history/{timestamp}."""
    publisher = FirestorePublisher()
    match_id = 101
    prediction = {"winner": "USA"}

    mock_db = MagicMock()
    publisher.db = mock_db

    publisher.save_prediction_history(match_id, prediction)

    # Check path
    mock_db.collection.assert_any_call("matches")
    mock_db.collection("matches").document.assert_any_call(str(match_id))
    mock_db.collection("matches").document(str(match_id)).collection.assert_called_with(
        "history"
    )
