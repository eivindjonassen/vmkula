import pytest
from unittest.mock import MagicMock, patch
from src.ai_agent import AIAgent


def test_generate_prediction_basic():
    """Test AI prediction generation with mock success."""
    agent = AIAgent()
    # Mock data
    matchup = {
        "home_team": {
            "name": "USA",
            "avg_xg": 2.1,
            "clean_sheets": 2,
            "form_string": "W-W-D",
        },
        "away_team": {
            "name": "England",
            "avg_xg": 1.8,
            "clean_sheets": 1,
            "form_string": "D-W-L",
        },
    }

    # Mock Gemini response
    mock_response = MagicMock()
    mock_response.text = '{"winner": "USA", "win_probability": 0.55, "predicted_home_score": 2, "predicted_away_score": 1, "reasoning": "Higher xG and better form."}'

    with patch.object(agent, "call_gemini", return_value=mock_response):
        prediction = agent.generate_prediction(matchup)

    assert prediction["winner"] == "USA"
    assert prediction["win_probability"] == 0.55
    assert prediction["predicted_home_score"] == 2
    assert prediction["predicted_away_score"] == 1
    assert "Higher xG" in prediction["reasoning"]


def test_parse_markdown_json():
    """Test parsing markdown-wrapped JSON responses."""
    agent = AIAgent()
    wrapped_json = '```json\n{"winner": "Draw"}\n```'
    # Assuming internal method _parse_response
    parsed = agent._parse_response(wrapped_json)
    assert parsed["winner"] == "Draw"


def test_retry_strategy_success_on_retry():
    """CRITICAL TEST: Retry strategy - success on second attempt."""
    agent = AIAgent()
    matchup = {"home_team": {"name": "USA"}, "away_team": {"name": "England"}}

    mock_call = MagicMock(
        side_effect=[Exception("Gemini Error"), MagicMock(text='{"winner": "England"}')]
    )

    with patch.object(agent, "call_gemini", mock_call):
        prediction = agent.generate_prediction(matchup)

    assert prediction["winner"] == "England"
    assert mock_call.call_count == 2


def test_fallback_to_rule_based():
    """CRITICAL TEST: Fallback to rule-based prediction after 2 failures."""
    agent = AIAgent()
    matchup = {
        "home_team": {"name": "USA", "avg_xg": 2.5},
        "away_team": {"name": "England", "avg_xg": 1.0},
    }

    # Mock failures
    mock_call = MagicMock(side_effect=Exception("Gemini Permanent Error"))

    with patch.object(agent, "call_gemini", mock_call):
        # We also need to mock rule_based_prediction if it's complex,
        # but here we want to test that it is CALLED.
        with patch.object(
            agent,
            "rule_based_prediction",
            return_value={"winner": "USA", "confidence": "low"},
        ) as mock_fallback:
            prediction = agent.generate_prediction(matchup)

    assert prediction["winner"] == "USA"
    assert prediction["confidence"] == "low"
    assert mock_call.call_count == 2
    mock_fallback.assert_called_once()


def test_rule_based_logic():
    """Test rule-based prediction logic using xG differential."""
    agent = AIAgent()
    matchup = {
        "home_team": {"name": "USA", "avg_xg": 2.0},
        "away_team": {"name": "England", "avg_xg": 1.0},
    }

    prediction = agent.rule_based_prediction(matchup)

    # 2.0 vs 1.0 -> USA should win in rule-based
    assert prediction["winner"] == "USA"
    assert prediction["win_probability"] > 0.5
    assert prediction["confidence"] == "low"
