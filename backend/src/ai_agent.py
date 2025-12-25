"""
AI prediction service using Google Gemini with fallback to rule-based predictions.

Implements:
- JSON mode for stable response parsing
- Retry strategy (max 1 retry, 2 total attempts)
- Rule-based fallback on Gemini failures
- Markdown-wrapped JSON parsing
"""

import json
import time
from typing import Dict, Any, Optional

try:
    from google import genai
    from google.genai import types

    GENAI_VERSION = "new"
except ImportError:
    import google.generativeai as genai

    GENAI_VERSION = "legacy"

from src.config import config


class AIAgent:
    """Generate match predictions using Gemini AI with rule-based fallback."""

    def __init__(self):
        """Initialize Gemini AI client with JSON response mode."""
        if GENAI_VERSION == "new":
            # New google.genai SDK
            self.client = genai.Client(api_key=config.GEMINI_API_KEY or "test-key")
            self.model_name = "gemini-2.0-flash-exp"
        else:
            # Legacy google.generativeai SDK
            genai.configure(api_key=config.GEMINI_API_KEY or "test-key")
            self.model = genai.GenerativeModel(
                "gemini-1.5-pro",
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.7,
                },
            )

    def generate_prediction(self, matchup: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate match prediction with retry and fallback strategy.

        Retry Strategy:
        - Max 1 retry (2 total attempts)
        - 1 second backoff between attempts
        - After 2 failures: call rule_based_prediction()

        Args:
            matchup: Dictionary with home_team and away_team data containing:
                - name: str
                - avg_xg: Optional[float]
                - clean_sheets: int
                - form_string: str (e.g., "W-W-D")

        Returns:
            Prediction dictionary with:
                - winner: str (team name or "Draw")
                - win_probability: float
                - predicted_home_score: int
                - predicted_away_score: int
                - reasoning: str
                - confidence: str (only for rule-based fallback)
        """
        max_retries = 1

        for attempt in range(max_retries + 1):
            try:
                response = self.call_gemini(matchup)
                parsed = self._parse_response(response.text)

                # Validate response has required fields
                self._validate_prediction(parsed)
                return parsed

            except Exception as e:
                if attempt == max_retries:
                    # Final attempt failed - use rule-based fallback
                    return self.rule_based_prediction(matchup)

                # Backoff before retry
                time.sleep(1)

        # Should never reach here, but satisfy type checker
        return self.rule_based_prediction(matchup)

    def call_gemini(self, matchup: Dict[str, Any]) -> Any:
        """
        Call Gemini API with structured prompt.

        This method is designed to be mockable for testing.

        Args:
            matchup: Match data with team statistics

        Returns:
            Gemini response object with .text attribute

        Raises:
            Exception: On API failures
        """
        home = matchup["home_team"]
        away = matchup["away_team"]

        # Build prompt with aggregated statistics
        prompt = f"""Predict the outcome of this World Cup 2026 match:

Home Team: {home["name"]}
- Average xG: {home.get("avg_xg", "N/A")}
- Clean Sheets: {home.get("clean_sheets", 0)}
- Recent Form: {home.get("form_string", "Unknown")}

Away Team: {away["name"]}
- Average xG: {away.get("avg_xg", "N/A")}
- Clean Sheets: {away.get("clean_sheets", 0)}
- Recent Form: {away.get("form_string", "Unknown")}

Provide prediction as JSON with this exact schema:
{{
  "winner": "team name or Draw",
  "win_probability": 0.0-1.0,
  "predicted_home_score": integer,
  "predicted_away_score": integer,
  "reasoning": "brief explanation (max 200 chars)"
}}"""

        if GENAI_VERSION == "new":
            # New SDK: use generate_content with JSON response schema
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7,
                ),
            )

            # Wrap in object with .text attribute for compatibility
            class ResponseWrapper:
                def __init__(self, text):
                    self.text = text

            return ResponseWrapper(response.text)
        else:
            # Legacy SDK
            return self.model.generate_content(prompt)

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON response, handling markdown code blocks.

        Gemini may wrap JSON in ```json ... ``` blocks even in JSON mode.

        Args:
            response_text: Raw response text

        Returns:
            Parsed JSON dictionary

        Raises:
            json.JSONDecodeError: If parsing fails
        """
        text = response_text.strip()

        # Strip markdown code blocks if present
        if text.startswith("```json"):
            text = text.replace("```json", "", 1)
        if text.startswith("```"):
            text = text.replace("```", "", 1)
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]

        text = text.strip()
        return json.loads(text)

    def _validate_prediction(self, prediction: Dict[str, Any]) -> None:
        """
        Validate prediction has required fields.

        Args:
            prediction: Parsed prediction dictionary

        Raises:
            ValueError: If required fields are missing
        """
        # Winner is mandatory, others can have defaults
        if "winner" not in prediction:
            raise ValueError("Missing required field: winner")

        # Fill in defaults for missing optional fields
        prediction.setdefault("win_probability", 0.5)
        prediction.setdefault("predicted_home_score", 1)
        prediction.setdefault("predicted_away_score", 1)
        prediction.setdefault("reasoning", "AI prediction")

    def rule_based_prediction(self, matchup: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback prediction using xG differential.

        Logic:
        - Compare avg_xg values
        - Higher xG = predicted winner
        - If xG unavailable or tied: predict Draw
        - Confidence always "low" for rule-based predictions

        Args:
            matchup: Match data with team statistics

        Returns:
            Prediction dictionary with confidence="low"
        """
        home = matchup["home_team"]
        away = matchup["away_team"]

        home_xg = home.get("avg_xg")
        away_xg = away.get("avg_xg")

        # Handle missing xG data
        if home_xg is None or away_xg is None:
            return {
                "winner": "Draw",
                "win_probability": 0.33,
                "predicted_home_score": 1,
                "predicted_away_score": 1,
                "reasoning": "Insufficient data for prediction",
                "confidence": "low",
            }

        # Compare xG values
        xg_diff = home_xg - away_xg

        if abs(xg_diff) < 0.3:
            # Close match - predict draw
            return {
                "winner": "Draw",
                "win_probability": 0.4,
                "predicted_home_score": 1,
                "predicted_away_score": 1,
                "reasoning": f"Evenly matched teams (xG diff: {xg_diff:.2f})",
                "confidence": "low",
            }
        elif xg_diff > 0:
            # Home team favored
            prob = min(0.5 + (xg_diff * 0.1), 0.75)
            return {
                "winner": home["name"],
                "win_probability": prob,
                "predicted_home_score": 2,
                "predicted_away_score": 1,
                "reasoning": f"Higher xG average ({home_xg:.2f} vs {away_xg:.2f})",
                "confidence": "low",
            }
        else:
            # Away team favored
            prob = min(0.5 + (abs(xg_diff) * 0.1), 0.75)
            return {
                "winner": away["name"],
                "win_probability": prob,
                "predicted_home_score": 1,
                "predicted_away_score": 2,
                "reasoning": f"Higher xG average ({away_xg:.2f} vs {home_xg:.2f})",
                "confidence": "low",
            }
