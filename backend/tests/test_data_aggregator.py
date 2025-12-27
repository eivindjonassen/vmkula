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

    # Mock API to fail with 429 twice, then succeed with valid fixture data
    mock_api = MagicMock(
        side_effect=[
            Exception("429 Rate Limit"),
            Exception("429 Rate Limit"),
            {
                "response": [
                    {
                        "teams": {"home": {"id": 1}, "away": {"id": 2}},
                        "goals": {"home": 2, "away": 1},
                    }
                ]
            },
        ]
    )
    aggregator.fetch_from_api = mock_api

    # Pass fetch_xg=False to avoid needing fixture.id in mock response
    result = aggregator.fetch_team_stats(1, fetch_xg=False)

    # Should succeed and return computed metrics (not raw response)
    assert "form_string" in result
    assert "confidence" in result
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


def test_fetch_team_fixtures_both_past_and_upcoming():
    """Test fetching both past and upcoming fixtures."""
    aggregator = DataAggregator()

    # Mock API response for past fixtures
    mock_past_response = {
        "response": [
            {
                "fixture": {
                    "id": 1001,
                    "date": "2024-12-01T19:00:00+00:00",
                    "venue": {"name": "Ullevaal Stadion"},
                    "status": {"short": "FT"},
                },
                "league": {"name": "World Cup - Qualification"},
                "teams": {
                    "home": {"id": 1090, "name": "Norway"},
                    "away": {"id": 1, "name": "England"},
                },
                "goals": {"home": 2, "away": 1},
            },
        ]
    }

    # Mock API response for upcoming fixtures
    mock_upcoming_response = {
        "response": [
            {
                "fixture": {
                    "id": 1002,
                    "date": "2025-01-15T18:00:00+00:00",
                    "venue": {"name": "Wembley Stadium"},
                    "status": {"short": "NS"},
                },
                "league": {"name": "Friendlies"},
                "teams": {
                    "home": {"id": 1, "name": "England"},
                    "away": {"id": 1090, "name": "Norway"},
                },
                "goals": {"home": None, "away": None},
            },
        ]
    }

    # Mock fetch_from_api to return different responses for past and upcoming
    aggregator.fetch_from_api = MagicMock(
        side_effect=[mock_past_response, mock_upcoming_response]
    )

    result = aggregator.fetch_team_fixtures(1090, last=5, next=5)

    assert result["total_count"] == 2
    assert len(result["past_fixtures"]) == 1
    assert len(result["upcoming_fixtures"]) == 1

    # Verify past fixture structure
    past_fixture = result["past_fixtures"][0]
    assert past_fixture["fixture_id"] == 1001
    assert past_fixture["status"] == "FT"
    assert past_fixture["goals"]["home"] == 2
    assert past_fixture["goals"]["away"] == 1
    assert past_fixture["home_team"]["name"] == "Norway"
    assert past_fixture["league"] == "World Cup - Qualification"

    # Verify upcoming fixture structure
    upcoming_fixture = result["upcoming_fixtures"][0]
    assert upcoming_fixture["fixture_id"] == 1002
    assert upcoming_fixture["status"] == "NS"
    assert upcoming_fixture["away_team"]["name"] == "Norway"
    assert upcoming_fixture["league"] == "Friendlies"


def test_fetch_team_fixtures_empty_response():
    """Test handling empty fixture response (no matches found)."""
    aggregator = DataAggregator()

    # Mock empty API responses for both past and upcoming
    mock_empty_response = {"response": []}
    aggregator.fetch_from_api = MagicMock(return_value=mock_empty_response)

    result = aggregator.fetch_team_fixtures(1090, last=5, next=5)

    assert result["total_count"] == 0
    assert len(result["past_fixtures"]) == 0
    assert len(result["upcoming_fixtures"]) == 0


def test_fetch_from_api_supports_last_and_next_params():
    """Test that fetch_from_api correctly handles last and next parameters."""
    import requests
    from unittest.mock import patch

    aggregator = DataAggregator()

    # Mock requests.get to capture the params
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": []}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Call with both last and next parameters
        aggregator.fetch_from_api(772, last=5, next=3)

        # Verify the API was called with correct params
        call_args = mock_get.call_args
        assert call_args[1]["params"]["team"] == 772
        assert call_args[1]["params"]["last"] == 5
        assert call_args[1]["params"]["next"] == 3
