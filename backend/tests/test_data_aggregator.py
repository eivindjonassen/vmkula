import pytest
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
