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


# ============================================================================
# ADDITIONAL TEST CASES - Edge Cases & Boundary Conditions
# ============================================================================


def test_cold_start_no_history():
    """EDGE CASE: First prediction for match - no history exists."""
    publisher = FirestorePublisher()
    match_id = 1
    new_prediction = {"winner": "USA", "reasoning": "Strong form"}

    # Mock empty history (cold start)
    mock_db = MagicMock()
    publisher.db = mock_db
    mock_db.collection().document().collection().order_by().limit().get.return_value = []

    should_save = publisher.should_save_prediction_history(match_id, new_prediction)

    assert should_save is True


def test_diff_check_only_winner_changed():
    """EDGE CASE: Only winner changed, reasoning identical - should save."""
    publisher = FirestorePublisher()
    match_id = 1
    new_prediction = {"winner": "England", "reasoning": "Strong form"}

    # Mock latest history - same reasoning, different winner
    mock_latest = MagicMock()
    mock_latest.to_dict.return_value = {"winner": "USA", "reasoning": "Strong form"}

    mock_db = MagicMock()
    publisher.db = mock_db
    mock_db.collection().document().collection().order_by().limit().get.return_value = [
        mock_latest
    ]

    should_save = publisher.should_save_prediction_history(match_id, new_prediction)

    assert should_save is True


def test_diff_check_only_reasoning_changed():
    """EDGE CASE: Only reasoning changed, winner identical - should save."""
    publisher = FirestorePublisher()
    match_id = 1
    new_prediction = {"winner": "USA", "reasoning": "Improved stats"}

    # Mock latest history - same winner, different reasoning
    mock_latest = MagicMock()
    mock_latest.to_dict.return_value = {"winner": "USA", "reasoning": "Strong form"}

    mock_db = MagicMock()
    publisher.db = mock_db
    mock_db.collection().document().collection().order_by().limit().get.return_value = [
        mock_latest
    ]

    should_save = publisher.should_save_prediction_history(match_id, new_prediction)

    assert should_save is True


def test_diff_check_missing_winner_in_new_prediction():
    """EDGE CASE: New prediction missing winner field - handle gracefully."""
    publisher = FirestorePublisher()
    match_id = 1
    new_prediction = {"reasoning": "Strong form"}  # Missing winner

    # Mock latest history with winner
    mock_latest = MagicMock()
    mock_latest.to_dict.return_value = {"winner": "USA", "reasoning": "Strong form"}

    mock_db = MagicMock()
    publisher.db = mock_db
    mock_db.collection().document().collection().order_by().limit().get.return_value = [
        mock_latest
    ]

    should_save = publisher.should_save_prediction_history(match_id, new_prediction)

    # Should save because winner changed (USA -> None)
    assert should_save is True


def test_diff_check_missing_reasoning_in_new_prediction():
    """EDGE CASE: New prediction missing reasoning field - handle gracefully."""
    publisher = FirestorePublisher()
    match_id = 1
    new_prediction = {"winner": "USA"}  # Missing reasoning

    # Mock latest history with reasoning
    mock_latest = MagicMock()
    mock_latest.to_dict.return_value = {"winner": "USA", "reasoning": "Strong form"}

    mock_db = MagicMock()
    publisher.db = mock_db
    mock_db.collection().document().collection().order_by().limit().get.return_value = [
        mock_latest
    ]

    should_save = publisher.should_save_prediction_history(match_id, new_prediction)

    # Should save because reasoning changed ("Strong form" -> None)
    assert should_save is True


def test_diff_check_malformed_history_entry():
    """EDGE CASE: History entry missing winner/reasoning fields."""
    publisher = FirestorePublisher()
    match_id = 1
    new_prediction = {"winner": "USA", "reasoning": "Strong form"}

    # Mock malformed history entry (missing fields)
    mock_latest = MagicMock()
    mock_latest.to_dict.return_value = {}  # Empty dict

    mock_db = MagicMock()
    publisher.db = mock_db
    mock_db.collection().document().collection().order_by().limit().get.return_value = [
        mock_latest
    ]

    should_save = publisher.should_save_prediction_history(match_id, new_prediction)

    # Should save because fields don't match (None != "USA")
    assert should_save is True


def test_publish_snapshot_missing_optional_fields():
    """EDGE CASE: Snapshot without favorites/dark_horses - should work."""
    publisher = FirestorePublisher()
    snapshot = {
        "groups": {"A": []},
        "bracket": [],
        "ai_summary": "Summary text",
        # No favorites or dark_horses
    }

    mock_db = MagicMock()
    publisher.db = mock_db

    publisher.publish_snapshot(snapshot)

    # Should still publish successfully
    call_args = mock_db.collection().document().set.call_args[0][0]
    assert call_args["ai_summary"] == "Summary text"
    assert "updated_at" in call_args
    assert "favorites" not in call_args or call_args.get("favorites") is None


def test_publish_snapshot_empty_groups():
    """EDGE CASE: Empty groups dictionary - boundary condition."""
    publisher = FirestorePublisher()
    snapshot = {
        "groups": {},
        "bracket": [],
        "ai_summary": "",
    }

    mock_db = MagicMock()
    publisher.db = mock_db

    publisher.publish_snapshot(snapshot)

    call_args = mock_db.collection().document().set.call_args[0][0]
    assert call_args["groups"] == {}
    assert "updated_at" in call_args


def test_save_history_includes_timestamp():
    """BOUNDARY: Verify timestamp is added to history entry."""
    publisher = FirestorePublisher()
    match_id = 1
    prediction = {"winner": "USA", "reasoning": "Strong"}

    mock_db = MagicMock()
    publisher.db = mock_db

    publisher.save_prediction_history(match_id, prediction)

    # Get the call arguments
    call_args = (
        mock_db.collection().document().collection().document().set.call_args[0][0]
    )
    assert "timestamp" in call_args
    assert call_args["winner"] == "USA"
    assert call_args["reasoning"] == "Strong"


def test_match_id_edge_cases():
    """BOUNDARY: Test match_id edge cases (0, very large number)."""
    publisher = FirestorePublisher()

    mock_db = MagicMock()
    publisher.db = mock_db

    # Test match_id = 0
    publisher.save_prediction_history(0, {"winner": "USA"})
    mock_db.collection("matches").document.assert_any_call("0")

    # Test very large match_id
    publisher.save_prediction_history(999999, {"winner": "USA"})
    mock_db.collection("matches").document.assert_any_call("999999")


def test_diff_check_null_values_in_history():
    """EDGE CASE: History entry has None/null values."""
    publisher = FirestorePublisher()
    match_id = 1
    new_prediction = {"winner": "USA", "reasoning": "Strong form"}

    # Mock history with null values
    mock_latest = MagicMock()
    mock_latest.to_dict.return_value = {"winner": None, "reasoning": None}

    mock_db = MagicMock()
    publisher.db = mock_db
    mock_db.collection().document().collection().order_by().limit().get.return_value = [
        mock_latest
    ]

    should_save = publisher.should_save_prediction_history(match_id, new_prediction)

    # Should save because values changed (None -> "USA", None -> "Strong form")
    assert should_save is True


def test_diff_check_both_predictions_null():
    """EDGE CASE: Both old and new predictions have null winner/reasoning."""
    publisher = FirestorePublisher()
    match_id = 1
    new_prediction = {"winner": None, "reasoning": None}

    # Mock history with null values
    mock_latest = MagicMock()
    mock_latest.to_dict.return_value = {"winner": None, "reasoning": None}

    mock_db = MagicMock()
    publisher.db = mock_db
    mock_db.collection().document().collection().order_by().limit().get.return_value = [
        mock_latest
    ]

    should_save = publisher.should_save_prediction_history(match_id, new_prediction)

    # Should NOT save because values are identical (None == None)
    assert should_save is False


def test_publish_snapshot_very_large_data():
    """BOUNDARY: Test large snapshot (approaching 1MB Firestore limit)."""
    publisher = FirestorePublisher()

    # Create large snapshot with many teams and matches
    large_groups = {
        chr(65 + i): [{"team": f"Team{j}"} for j in range(100)] for i in range(12)
    }
    large_bracket = [{"match": i} for i in range(1000)]

    snapshot = {
        "groups": large_groups,
        "bracket": large_bracket,
        "ai_summary": "x" * 10000,  # 10KB summary
    }

    mock_db = MagicMock()
    publisher.db = mock_db

    # Should handle large data without errors
    publisher.publish_snapshot(snapshot)

    call_args = mock_db.collection().document().set.call_args[0][0]
    assert len(call_args["groups"]) == 12
    assert len(call_args["bracket"]) == 1000


def test_timestamp_format_is_iso8601():
    """VALIDATION: Ensure timestamps use ISO8601 format."""
    publisher = FirestorePublisher()
    match_id = 1
    prediction = {"winner": "USA"}

    mock_db = MagicMock()
    publisher.db = mock_db

    publisher.save_prediction_history(match_id, prediction)

    call_args = (
        mock_db.collection().document().collection().document().set.call_args[0][0]
    )

    # Check timestamp format (ISO8601: YYYY-MM-DDTHH:MM:SS.ssssss)
    timestamp = call_args["timestamp"]
    assert "T" in timestamp
    assert len(timestamp.split("T")) == 2
    # Basic validation - should not raise exception
    from datetime import datetime

    datetime.fromisoformat(timestamp)


def test_diff_check_whitespace_differences():
    """EDGE CASE: Whitespace differences in reasoning should trigger save."""
    publisher = FirestorePublisher()
    match_id = 1
    new_prediction = {"winner": "USA", "reasoning": "Strong form"}

    # Mock history with extra whitespace
    mock_latest = MagicMock()
    mock_latest.to_dict.return_value = {
        "winner": "USA",
        "reasoning": "Strong  form",
    }  # Double space

    mock_db = MagicMock()
    publisher.db = mock_db
    mock_db.collection().document().collection().order_by().limit().get.return_value = [
        mock_latest
    ]

    should_save = publisher.should_save_prediction_history(match_id, new_prediction)

    # Should save because strings are different
    assert should_save is True
