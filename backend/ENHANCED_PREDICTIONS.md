# Enhanced Prediction System

## Overview

The vmkula prediction system uses a **hybrid approach** combining multiple data sources to generate accurate World Cup 2026 match predictions.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    HYBRID PREDICTION SYSTEM                  │
└─────────────────────────────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
        ┌───────▼──────┐          ┌──────▼──────┐
        │ API-Football │          │   Gemini AI │
        │     Data     │          │   Analysis  │
        └───────┬──────┘          └──────┬──────┘
                │                         │
                └────────────┬────────────┘
                             │
                    ┌────────▼────────┐
                    │ Final Prediction│
                    └─────────────────┘
```

## Data Sources

### 1. API-Football (Statistical Foundation)

**Team Statistics** (`/fixtures` endpoint):
- ✅ **Recent Form**: W-D-L pattern from last 5 matches
- ✅ **Clean Sheets**: Number of matches without conceding
- ⚠️ **Expected Goals (xG)**: Fetched from `/fixtures/statistics` when available
  - Note: May not be available for all fixtures/tiers
  - Infrastructure is ready when data becomes available

**Match Predictions** (`/predictions` endpoint):
- ⚠️ **Win Probabilities**: Home/Draw/Away percentages
- ⚠️ **Comparison Metrics**: Form, Attack, Defense comparisons
- ⚠️ **Statistical Advice**: Recommended betting outcomes
  - Note: Only available for existing fixtures
  - World Cup 2026 matches don't exist in API yet (tournament is in future)
  - Will be used when available or for testing with real matches

### 2. Gemini AI (Contextual Analysis)

**Capabilities**:
- Analyzes team statistics in context
- Considers tournament dynamics
- Applies football knowledge and reasoning
- Generates natural language explanations
- Refines predictions based on multiple data points

**Model**: `gemini-2.5-flash` (Tier 1 Paid)
- Rate Limit: 2,000 RPM
- Cost: ~$0.01 per 72 predictions
- Response Time: ~3 seconds per prediction

## Prediction Flow

### Step 1: Fetch Team Statistics

```python
# Fetch Norway stats with xG enabled
norway_stats = aggregator.fetch_team_stats(
    team_id=1090,
    fetch_xg=True  # Costs extra API calls to statistics endpoint
)

# Result:
{
    "form_string": "W-W-D-W-W",
    "clean_sheets": 1,
    "avg_xg": None,  # May be None if not available
    "confidence": "low",  # Based on data completeness
    "has_real_data": True
}
```

### Step 2: Try to Fetch API-Football Prediction (Optional)

```python
# Only works for existing fixtures (not World Cup 2026 yet)
api_prediction = aggregator.fetch_match_prediction(fixture_id=12345)

# Result (when available):
{
    "predictions": {
        "winner": {"name": "France"},
        "percent": {"home": "65", "draw": "20", "away": "15"},
        "advice": "Combo bet: Home & Over 2.5"
    },
    "comparison": {
        "form": {"home": "75%", "away": "60%"},
        "att": {"home": "80%", "away": "70%"},
        "def": {"home": "70%", "away": "65%"}
    }
}
```

### Step 3: Build Hybrid Matchup

```python
matchup = {
    "home_team": {
        "name": "France",
        "form_string": "W-W-D-W-W",
        "clean_sheets": 2,
        "avg_xg": None
    },
    "away_team": {
        "name": "Norway",
        "form_string": "W-W-D-W-W",
        "clean_sheets": 1,
        "avg_xg": None
    },
    "api_football_prediction": api_prediction  # None if not available
}
```

### Step 4: Gemini Generates Final Prediction

```python
prediction = agent.generate_prediction(matchup)

# Gemini receives prompt with ALL available data:
# - Team form (W-W-D-W-W)
# - Clean sheets
# - xG (if available)
# - API-Football probabilities (if available)
# - Comparison metrics (if available)

# Result:
{
    "winner": "France",
    "win_probability": 0.68,
    "predicted_home_score": 2,
    "predicted_away_score": 1,
    "reasoning": "France's superior squad quality and historical performance give them an edge...",
    "confidence": "medium"
}
```

## Current Status

### ✅ Implemented

1. **Team Statistics Fetching**
   - Form strings from recent matches
   - Clean sheet tracking
   - xG fetching infrastructure (when available)

2. **xG Infrastructure**
   - Fetches from `/fixtures/statistics` endpoint
   - Extracts xG for each team
   - Handles missing data gracefully
   - Currently returns `None` (not available for test fixtures)

3. **API-Football Predictions Infrastructure**
   - Fetches from `/predictions` endpoint
   - Parses win probabilities and comparison metrics
   - Passes to Gemini for analysis
   - Currently `None` for WC 2026 (tournament doesn't exist yet)

4. **Gemini AI Integration**
   - Enhanced prompts with all available data
   - Contextual analysis of statistics
   - Natural language reasoning
   - Fallback when data is missing

### ⚠️ Limitations

1. **xG Data**
   - Infrastructure ready but data not always available
   - May depend on API-Football tier or fixture type
   - Falls back gracefully to form + clean sheets

2. **API-Football Predictions**
   - Only available for existing fixtures
   - World Cup 2026 hasn't happened yet (no fixtures in API)
   - Ready to use when WC 2026 fixtures are added

3. **Historical Data**
   - Limited to last 5 matches per team
   - International matches may have sparse data

## API Call Costs

### Per Team (with xG enabled)

| Operation | Endpoint | API Calls | Cache TTL |
|-----------|----------|-----------|-----------|
| Fetch last 5 matches | `/fixtures` | 1 | 24 hours |
| Fetch xG per match | `/fixtures/statistics` | 5 | 24 hours |
| **Total per team** | - | **6** | 24 hours |

### Per Match Prediction

| Operation | Endpoint | API Calls | Cache TTL |
|-----------|----------|-----------|-----------|
| Fetch 2 teams stats | `/fixtures` | 2 | 24 hours |
| Fetch xG (2 teams × 5 matches) | `/fixtures/statistics` | 10 | 24 hours |
| Fetch match prediction | `/predictions` | 1 | 24 hours |
| Gemini AI call | Google AI API | 1 | - |
| **Total per match** | - | **14 API calls** | - |

### With Caching

On subsequent runs within 24 hours:
- API-Football: **0 calls** (all cached)
- Gemini: **1 call** per prediction

### Cost Optimization

**Disable xG fetching** to reduce API calls:
```python
stats = aggregator.fetch_team_stats(team_id, fetch_xg=False)
# Reduces from 6 to 1 API call per team
```

**Use cached data**:
- All API-Football responses are cached for 24 hours
- Cache hit = 0 API calls

## Testing

### Run Enhanced Prediction Test

```bash
cd backend
source venv/bin/activate
python test_enhanced_predictions.py
```

**Expected Output**:
```
✅ Norway stats fetched:
   - Form: W-W-D-W-W
   - Clean Sheets: 1
   - Avg xG: None
   - Confidence: low

✅ France stats fetched:
   - Form: W-W-D-W-W
   - Clean Sheets: 2
   - Avg xG: None
   - Confidence: low

✅ Prediction generated:
   - Winner: France
   - Score: 2-1
   - Win Probability: 68.0%
   - Reasoning: France's superior squad quality...
```

## Future Enhancements

### When xG Becomes Available

No code changes needed! The system will automatically:
1. Fetch xG from statistics endpoint
2. Include in team stats
3. Pass to Gemini for analysis
4. Generate more accurate predictions

### When World Cup 2026 Fixtures Are Added

```python
# Add api_football_fixture_id to matches table
ALTER TABLE matches ADD COLUMN api_football_fixture_id INTEGER;

# Update match with fixture ID when available
UPDATE matches SET api_football_fixture_id = 123456 WHERE id = 42;

# System will automatically fetch API-Football predictions
```

### Advanced Metrics (Future)

Can be added to `fetch_fixture_statistics`:
- Shots on target
- Possession %
- Pass completion %
- Tackles and interceptions
- Player injuries/suspensions

## Comparison: Before vs After

### Before (Legacy System)

```
Team Data:
├─ Form: ❌ Not fetched
├─ Clean Sheets: ❌ Not fetched
└─ xG: ❌ Not available

Prediction:
└─ Gemini: Generic prediction with minimal data
   Result: "Insufficient data for prediction"
```

### After (Enhanced System)

```
Team Data:
├─ Form: ✅ W-W-D-W-W from API-Football
├─ Clean Sheets: ✅ Tracked from API-Football
├─ xG: ⚠️ Infrastructure ready (when available)
└─ API Prediction: ⚠️ Infrastructure ready (for existing fixtures)

Prediction:
└─ Gemini: Rich analysis with multiple data sources
   Result: "France's superior squad quality and historical
           performance give them an edge despite Norway's
           strong recent form. France also has a slightly
           better clean sheet record."
   Confidence: Medium
   Win Probability: 68%
```

## Configuration

### Enable xG Fetching Globally

In `backend/src/main.py`:
```python
# Line 468
stats = aggregator.fetch_team_stats(team.api_football_id, fetch_xg=True)
```

### Disable xG (Reduce API Calls)

```python
# Line 468
stats = aggregator.fetch_team_stats(team.api_football_id, fetch_xg=False)
```

### Adjust Rate Limiting

In `backend/src/data_aggregator.py`:
```python
def _enforce_rate_limit(self):
    """Enforce delay between API requests."""
    elapsed = time.time() - self.last_request_time
    delay = 0.5  # Change this value (seconds)
    if elapsed < delay:
        time.sleep(delay - elapsed)
    self.last_request_time = time.time()
```

## Troubleshooting

### "avg_xg is None"

**Causes**:
1. xG not available for these specific fixtures
2. API tier limitation
3. International matches may not have xG data

**Solution**: System falls back to form + clean sheets. No action needed.

### "No prediction available for fixture"

**Cause**: API-Football doesn't have prediction for this fixture (common for future matches).

**Solution**: Gemini still generates predictions using team stats.

### Rate Limit Errors

**Solution**:
1. Check API quota on API-Football dashboard
2. Increase delay in `_enforce_rate_limit()`
3. Use cached data (24-hour TTL)

## Best Practices

1. **Enable caching**: Always use cache to minimize API calls
2. **Batch processing**: Fetch all team stats before generating predictions
3. **Monitor quota**: Track API-Football usage on dashboard
4. **xG optional**: Only enable for high-priority matches if quota is limited
5. **Incremental updates**: Only regenerate predictions when team data changes

## Resources

- [API-Football Documentation](https://www.api-football.com/documentation-v3)
- [API-Football Predictions](https://www.api-football.com/documentation-v3#tag/Predictions)
- [API-Football Statistics](https://www.api-football.com/documentation-v3#tag/Fixtures/operation/get-fixtures-statistics)
- [Gemini AI Documentation](https://ai.google.dev/gemini-api/docs)
