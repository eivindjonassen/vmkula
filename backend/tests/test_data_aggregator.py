import pytest
from datetime import datetime
from unittest.mock import MagicMock
from src.data_aggregator import DataAggregator


def test_compute_metrics_basic():
    """Test xG average and metrics calculation with complete data."""
    aggregator = DataAggregator()
    # Mock fixtures with xG data
    fixtures = [
        {"goals_for": 2, "goals_against": 1, "xg": 2.1, "result": "W"},
        {"goals_for": 1, "goals_against": 1, "xg": 1.5, "result": "D"},
        {"goals_for": 0, "goals_against": 2, "xg": 0.8, "result": "L"},
        {"goals_for": 3, "goals_against": 0, "xg": 2.4, "result": "W"},
        {"goals_for": 1, "goals_against": 0, "xg": 1.2, "result": "W"},
    ]

    metrics = aggregator.compute_metrics(fixtures)

    # avg_xg = (2.1 + 1.5 + 0.8 + 2.4 + 1.2) / 5 = 1.6
    assert metrics.avg_xg == pytest.approx(1.6)
    assert metrics.clean_sheets == 2
    assert (
        metrics.form_string == "W-W-L-D-W"
    )  # Most recent first (assuming index 4 is most recent)
    assert metrics.data_completeness == 1.0
    assert metrics.confidence == "high"


def test_handle_missing_xg_data():
    """
    CRITICAL TEST: Handle missing xG data.
    Scenario: 5 matches, only 3 have xG data.
    Expected: avg_xg = (2.4 + 0.8 + 2.2) / 3 = 1.8
    Expected: data_completeness = 0.6 (3/5)
    Expected: confidence = "medium"
    """
    aggregator = DataAggregator()
    fixtures = [
        {"goals_for": 2, "goals_against": 1, "xg": 2.4, "result": "W"},
        {"goals_for": 1, "goals_against": 2, "xg": None, "result": "L"},  # Missing
        {"goals_for": 0, "goals_against": 1, "xg": 0.8, "result": "L"},
        {"goals_for": 1, "goals_against": 1, "xg": None, "result": "D"},  # Missing
        {"goals_for": 2, "goals_against": 0, "xg": 2.2, "result": "W"},
    ]

    metrics = aggregator.compute_metrics(fixtures)

    assert metrics.avg_xg == pytest.approx(1.8)
    assert metrics.data_completeness == 0.6
    assert metrics.confidence == "medium"


def test_fallback_mode_no_xg():
    """Test fallback mode when NO xG data available."""
    aggregator = DataAggregator()
    fixtures = [
        {"goals_for": 1, "goals_against": 1, "xg": None, "result": "D"},
        {"goals_for": 2, "goals_against": 0, "xg": None, "result": "W"},
    ]

    metrics = aggregator.compute_metrics(fixtures)

    assert metrics.avg_xg is None
    assert metrics.fallback_mode == "traditional_form"
    assert metrics.confidence == "low"


def test_clean_sheets_count():
    """Test clean sheets count (matches with goals_against=0)."""
    aggregator = DataAggregator()
    fixtures = [
        {"goals_for": 2, "goals_against": 0, "result": "W"},
        {"goals_for": 0, "goals_against": 0, "result": "D"},
        {"goals_for": 1, "goals_against": 1, "result": "D"},
    ]
    metrics = aggregator.compute_metrics(fixtures)
    assert metrics.clean_sheets == 2


def test_form_string_generation():
    """Test form string generation pattern."""
    aggregator = DataAggregator()
    fixtures = [
        {"result": "W"},
        {"result": "D"},
        {"result": "L"},
    ]
    metrics = aggregator.compute_metrics(fixtures)
    assert metrics.form_string == "L-D-W"  # Reversed order (latest first)


def test_cache_logic(tmp_path):
    """
    CRITICAL TEST: Use cached data if less than 24 hours old.
    Test cache file naming and expiration.
    """
    import os
    import json
    from datetime import datetime, timedelta

    aggregator = DataAggregator()
    # Mock cache directory using tmp_path
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    aggregator.cache_dir = str(cache_dir)

    team_id = 1
    today = datetime.now().strftime("%Y-%m-%d")
    cache_file = cache_dir / f"team_stats_{team_id}_{today}.json"

    # 1. Test cache miss
    assert aggregator.get_cached_stats(team_id) is None

    # 2. Test cache hit (write mock data)
    mock_stats = {
        "avg_xg": 1.5,
        "clean_sheets": 2,
        "form_string": "W-W",
        "data_completeness": 1.0,
        "confidence": "high",
    }
    with open(cache_file, "w") as f:
        json.dump(mock_stats, f)

    cached = aggregator.get_cached_stats(team_id)
    assert cached is not None
    assert cached["avg_xg"] == 1.5

    # 3. Test cache expiration (mocking file age)
    # Actually, the file naming includes the date {YYYY-MM-DD}.
    # If we check for a different date, it should be a miss.
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    old_cache_file = cache_dir / f"team_stats_{team_id}_{yesterday}.json"
    with open(old_cache_file, "w") as f:
        json.dump(mock_stats, f)

    # If the aggregator only looks for today's file, it will miss yesterday's.
    # Plan says: "data older than 24 hours is refetched".
    # If we use the date in filename, it's naturally expired when the day changes.
    assert aggregator.get_cached_stats(team_id) is not None  # still hits today's

    # Removing today's to check miss on yesterday's
    os.remove(cache_file)
    assert aggregator.get_cached_stats(team_id) is None


def test_save_to_cache(tmp_path):
    """Test saving stats to cache creates directory and file."""
    aggregator = DataAggregator()
    cache_dir = tmp_path / "new_cache"
    aggregator.cache_dir = str(cache_dir)

    team_id = 1
    stats = {"avg_xg": 1.5, "clean_sheets": 2}

    aggregator.save_to_cache(team_id, stats)

    assert cache_dir.exists()
    today = datetime.now().strftime("%Y-%m-%d")
    cache_file = cache_dir / f"team_stats_{team_id}_{today}.json"
    assert cache_file.exists()


def test_rate_limiting(monkeypatch):
    """CRITICAL TEST: Ensure 0.5 second delay between consecutive requests."""
    import time

    mock_sleep = MagicMock()
    monkeypatch.setattr(time, "sleep", mock_sleep)

    aggregator = DataAggregator()
    # Mocking the actual API call
    aggregator.fetch_from_api = MagicMock(return_value={"status": "ok"})

    # Call twice
    aggregator.fetch_team_stats(1)
    aggregator.fetch_team_stats(2)

    # Check if sleep was called with 0.5
    mock_sleep.assert_any_call(0.5)


def test_retry_exponential_backoff(monkeypatch):
    """Test exponential backoff on 429 errors (wait 1s, 2s, 4s)."""
    import time

    mock_sleep = MagicMock()
    monkeypatch.setattr(time, "sleep", mock_sleep)

    aggregator = DataAggregator()

    # Mock API to fail with 429 twice, then succeed
    mock_api = MagicMock(
        side_effect=[
            Exception("429 Rate Limit"),
            Exception("429 Rate Limit"),
            {"status": "ok"},
        ]
    )
    aggregator.fetch_from_api = mock_api

    result = aggregator.fetch_team_stats(1)

    assert result == {"status": "ok"}
    assert mock_api.call_count == 3
    # Wait 1s, then 2s
    mock_sleep.assert_any_call(1)
    mock_sleep.assert_any_call(2)


def test_max_retries_failure(monkeypatch):
    """Test failure after max retries exceeded."""
    import time

    mock_sleep = MagicMock()
    monkeypatch.setattr(time, "sleep", mock_sleep)

    aggregator = DataAggregator()

    # Mock API to always fail
    mock_api = MagicMock(side_effect=Exception("500 Server Error"))
    aggregator.fetch_from_api = mock_api

    with pytest.raises(Exception, match="Max retries exceeded"):
        aggregator.fetch_team_stats(1)

    assert mock_api.call_count == 4  # Initial + 3 retries
