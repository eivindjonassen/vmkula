"""
AI prediction service using Google Gemini with fallback to rule-based predictions.

Implements:
- JSON mode for stable response parsing
- Retry strategy (max 1 retry, 2 total attempts)
- Rule-based fallback on Gemini failures
- Markdown-wrapped JSON parsing
"""

import json
import logging
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
from src.exceptions import GeminiFailureError

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class AIAgent:
    """Generate match predictions using Gemini AI with rule-based fallback."""

    def __init__(self):
        """Initialize Gemini AI client with JSON response mode and rate limiting."""
        self.last_request_time = 0.0  # Track last API call for rate limiting
        self.min_delay = 0.05  # Tier 1 Paid: 2,000 RPM = 33.3 req/sec, minimal delay

        if GENAI_VERSION == "new":
            # New google.genai SDK (Google AI Studio - Tier 1 Paid)
            self.client = genai.Client(api_key=config.GEMINI_API_KEY or "test-key")

            # Using gemini-2.5-flash for best quality
            # Tier 1 Paid: 2,000 RPM limit (no need for Lite version)
            self.model_name = "gemini-2.5-flash"
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
        home_name = matchup.get("home_team", {}).get("name", "Unknown")
        away_name = matchup.get("away_team", {}).get("name", "Unknown")
        match_id = matchup.get("match_id", "N/A")

        logger.info(
            f"Generating prediction for match {match_id}: {home_name} vs {away_name}"
        )
        start_time = time.time()

        for attempt in range(max_retries + 1):
            try:
                # Rate limiting: ensure minimum delay between requests
                if self.last_request_time > 0:
                    elapsed_since_last = time.time() - self.last_request_time
                    if elapsed_since_last < self.min_delay:
                        sleep_time = self.min_delay - elapsed_since_last
                        logger.debug(f"Rate limiting: sleeping {sleep_time:.1f}s")
                        time.sleep(sleep_time)

                response = self.call_gemini(matchup)
                self.last_request_time = time.time()  # Update last request time
                parsed = self._parse_response(response.text)

                # Validate response has required fields
                self._validate_prediction(parsed)

                elapsed = time.time() - start_time
                logger.info(
                    f"Gemini prediction SUCCESS for match {match_id} (attempt {attempt + 1}, elapsed {elapsed:.2f}s): {parsed.get('winner')}"
                )
                return parsed

            except Exception as e:
                elapsed = time.time() - start_time
                error_msg = str(e)

                # Check if it's a 429 rate limit error
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    # Extract retry delay if provided (default to 30s for rate limits)
                    retry_delay = 30
                    if "retryDelay" in error_msg:
                        # Try to extract delay from error message
                        import re

                        match = re.search(r"'retryDelay': '(\d+)s'", error_msg)
                        if match:
                            retry_delay = int(match.group(1))

                    logger.warning(
                        f"Rate limit hit for match {match_id}, would need to wait {retry_delay}s. Using fallback instead."
                    )
                    # Immediately use fallback instead of waiting
                    fallback = self.rule_based_prediction(matchup)
                    logger.info(
                        f"Rule-based fallback for match {match_id}: {fallback.get('winner')}"
                    )
                    return fallback

                if attempt == max_retries:
                    # Final attempt failed - use rule-based fallback
                    logger.warning(
                        f"Gemini prediction FAILED for match {match_id} after {attempt + 1} attempts (elapsed {elapsed:.2f}s), using rule-based fallback: {e}"
                    )
                    fallback = self.rule_based_prediction(matchup)
                    logger.info(
                        f"Rule-based fallback for match {match_id}: {fallback.get('winner')}"
                    )
                    return fallback

                # Backoff before retry
                logger.warning(
                    f"Gemini prediction failed (attempt {attempt + 1}), retrying in 1s: {e}"
                )
                time.sleep(1)

        # Should never reach here, but satisfy type checker
        return self.rule_based_prediction(matchup)

    def call_gemini(self, matchup: Dict[str, Any]) -> Any:
        """
        Call Gemini API with structured prompt.

        This method is designed to be mockable for testing.

        Args:
            matchup: Match data with team statistics and optional API-Football prediction

        Returns:
            Gemini response object with .text attribute

        Raises:
            GeminiFailureError: On API failures
        """
        home = matchup["home_team"]
        away = matchup["away_team"]
        api_prediction = matchup.get("api_football_prediction")

        # Build FIFA ranking lines if available
        home_fifa = ""
        if home.get("fifa_ranking"):
            home_fifa = f"\n- FIFA-rangering: #{home['fifa_ranking']}"
            if home.get("fifa_points"):
                home_fifa += f" ({home['fifa_points']:.2f} poeng"
                if home.get("fifa_confederation"):
                    home_fifa += f", {home['fifa_confederation']}"
                home_fifa += ")"
        
        away_fifa = ""
        if away.get("fifa_ranking"):
            away_fifa = f"\n- FIFA-rangering: #{away['fifa_ranking']}"
            if away.get("fifa_points"):
                away_fifa += f" ({away['fifa_points']:.2f} poeng"
                if away.get("fifa_confederation"):
                    away_fifa += f", {away['fifa_confederation']}"
                away_fifa += ")"
        
        # Build prompt with aggregated statistics (in Norwegian)
        prompt = f"""Spå resultatet av denne VM 2026-kampen:

Hjemmelag: {home["name"]}
- Gjennomsnittlig xG: {home.get("avg_xg", "N/A")}
- Nullet motstanderen: {home.get("clean_sheets", 0)}
- Siste form: {home.get("form_string", "Ukjent")}{home_fifa}

Bortelag: {away["name"]}
- Gjennomsnittlig xG: {away.get("avg_xg", "N/A")}
- Nullet motstanderen: {away.get("clean_sheets", 0)}
- Siste form: {away.get("form_string", "Ukjent")}{away_fifa}"""

        # Add API-Football prediction data if available
        if api_prediction:
            predictions = api_prediction.get("predictions", {})
            winner = predictions.get("winner", {})
            percent = predictions.get("percent", {})

            prompt += f"""

API-Football statistisk spådom:
- Sannsynlighet for vinner: Hjemme {percent.get("home", "N/A")}%, Uavgjort {percent.get("draw", "N/A")}%, Borte {percent.get("away", "N/A")}%
- Forventet vinner: {winner.get("name", "N/A")}
- Råd: {predictions.get("advice", "N/A")}

Sammenligningsmålinger:
- Form: {api_prediction.get("comparison", {}).get("form", {}).get("home", "N/A")} (hjemme) vs {api_prediction.get("comparison", {}).get("form", {}).get("away", "N/A")} (borte)
- Angrep: {api_prediction.get("comparison", {}).get("att", {}).get("home", "N/A")} vs {api_prediction.get("comparison", {}).get("att", {}).get("away", "N/A")}
- Forsvar: {api_prediction.get("comparison", {}).get("def", {}).get("home", "N/A")} vs {api_prediction.get("comparison", {}).get("def", {}).get("away", "N/A")}

Bruk denne statistiske spådommen som grunnlag, men bruk din analyse av lagform, xG og clean sheets for å forbedre spådommen."""

        prompt += """

Gi spådommen som JSON med nøyaktig dette skjemaet:
{
  "winner": "lagnavn eller Uavgjort",
  "win_probability": 0.0-1.0,
  "predicted_home_score": heltall,
  "predicted_away_score": heltall,
  "reasoning": "kort forklaring på norsk (maks 200 tegn)"
}"""

        logger.debug(f"Calling Gemini API with prompt: {prompt[:100]}...")
        api_start = time.time()

        try:
            if GENAI_VERSION == "new":
                # New SDK: use generate_content with JSON response schema
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.7,
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(
                            disable=True  # Disable AFC - we don't use function calling
                        ),
                    ),
                )

                # Wrap in object with .text attribute for compatibility
                class ResponseWrapper:
                    def __init__(self, text):
                        self.text = text

                api_elapsed = time.time() - api_start
                logger.debug(f"Gemini API response time: {api_elapsed:.2f}s")
                return ResponseWrapper(response.text)
            else:
                # Legacy SDK
                result = self.model.generate_content(prompt)
                api_elapsed = time.time() - api_start
                logger.debug(f"Gemini API response time: {api_elapsed:.2f}s")
                return result

        except Exception as e:
            api_elapsed = time.time() - api_start
            logger.error(f"Gemini API call failed (elapsed {api_elapsed:.2f}s): {e}")
            raise GeminiFailureError(f"Gemini API error: {e}", attempts=1) from e

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

        logger.debug(f"Parsing Gemini response: {text[:100]}...")

        # Strip markdown code blocks if present
        if text.startswith("```json"):
            logger.debug("Stripping ```json code block wrapper")
            text = text.replace("```json", "", 1)
        if text.startswith("```"):
            logger.debug("Stripping ``` code block wrapper")
            text = text.replace("```", "", 1)
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]

        text = text.strip()

        try:
            parsed = json.loads(text)
            logger.debug(f"Successfully parsed JSON response")
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response text: {text}")
            raise

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
        prediction.setdefault("reasoning", "AI-spådom")

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
                "winner": "Uavgjort",
                "win_probability": 0.33,
                "predicted_home_score": 1,
                "predicted_away_score": 1,
                "reasoning": "Utilstrekkelig data for spådom",
                "confidence": "low",
            }

        # Compare xG values
        xg_diff = home_xg - away_xg

        if abs(xg_diff) < 0.3:
            # Close match - predict draw
            return {
                "winner": "Uavgjort",
                "win_probability": 0.4,
                "predicted_home_score": 1,
                "predicted_away_score": 1,
                "reasoning": f"Jevnbyrdige lag (xG diff: {xg_diff:.2f})",
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
                "reasoning": f"Høyere xG-gjennomsnitt ({home_xg:.2f} vs {away_xg:.2f})",
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
                "reasoning": f"Høyere xG-gjennomsnitt ({away_xg:.2f} vs {home_xg:.2f})",
                "confidence": "low",
            }
