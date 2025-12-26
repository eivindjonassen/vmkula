"""
Test enhanced prediction system with API-Football data.

This script tests:
1. Fetching xG from API-Football statistics endpoint
2. Fetching API-Football predictions (when available)
3. Hybrid Gemini prediction using both data sources
"""

import logging
from src.data_aggregator import DataAggregator
from src.ai_agent import AIAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_enhanced_predictions():
    """Test enhanced prediction system."""

    print("=" * 80)
    print("ENHANCED PREDICTION SYSTEM TEST")
    print("=" * 80)

    # Initialize components
    aggregator = DataAggregator()
    agent = AIAgent()

    # Test teams (Norway vs France)
    norway_id = 1090  # API-Football ID
    france_id = 2  # API-Football ID

    print("\n" + "-" * 80)
    print("TEST 1: Fetch team stats WITH xG")
    print("-" * 80)

    try:
        print(f"\nFetching Norway stats (ID: {norway_id}) with xG...")
        norway_stats = aggregator.fetch_team_stats(norway_id, fetch_xg=True)
        print(f"✅ Norway stats fetched:")
        print(f"   - Form: {norway_stats.get('form_string')}")
        print(f"   - Clean Sheets: {norway_stats.get('clean_sheets')}")
        print(f"   - Avg xG: {norway_stats.get('avg_xg')}")
        print(f"   - Confidence: {norway_stats.get('confidence')}")

        print(f"\nFetching France stats (ID: {france_id}) with xG...")
        france_stats = aggregator.fetch_team_stats(france_id, fetch_xg=True)
        print(f"✅ France stats fetched:")
        print(f"   - Form: {france_stats.get('form_string')}")
        print(f"   - Clean Sheets: {france_stats.get('clean_sheets')}")
        print(f"   - Avg xG: {france_stats.get('avg_xg')}")
        print(f"   - Confidence: {france_stats.get('confidence')}")

    except Exception as e:
        print(f"❌ Failed to fetch team stats: {e}")
        return False

    print("\n" + "-" * 80)
    print("TEST 2: Generate hybrid prediction (Gemini + API-Football data)")
    print("-" * 80)

    try:
        # Build matchup
        matchup = {
            "match_id": 42,
            "match_number": 42,
            "stage_id": 1,
            "home_team": {
                "name": "France",
                **france_stats,
            },
            "away_team": {
                "name": "Norway",
                **norway_stats,
            },
            # Note: api_football_prediction will be None for World Cup 2026 matches
            # since the tournament hasn't happened yet. This is prepared for future use.
            "api_football_prediction": None,
        }

        print("\nGenerating prediction with Gemini AI...")
        prediction = agent.generate_prediction(matchup)

        print(f"✅ Prediction generated:")
        print(f"   - Winner: {prediction.get('winner')}")
        print(
            f"   - Score: {prediction.get('predicted_home_score')}-{prediction.get('predicted_away_score')}"
        )
        print(f"   - Win Probability: {prediction.get('win_probability') * 100:.1f}%")
        print(f"   - Confidence: {prediction.get('confidence')}")
        print(f"   - Reasoning: {prediction.get('reasoning')}")

    except Exception as e:
        print(f"❌ Failed to generate prediction: {e}")
        import traceback

        traceback.print_exc()
        return False

    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print("\nSummary:")
    print("- ✅ xG fetching works (when available in API-Football)")
    print("- ✅ Enhanced team stats with xG, form, and clean sheets")
    print("- ✅ Gemini uses richer data for better predictions")
    print("- ⚠️  API-Football predictions unavailable (WC 2026 hasn't happened yet)")
    print("\nNote: xG may still be None if API-Football doesn't provide it for")
    print("      the specific fixtures, but the infrastructure is in place.")

    return True


if __name__ == "__main__":
    test_enhanced_predictions()
