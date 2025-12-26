# VM Kula - Prediction Process

## Overview
This document describes how match predictions are generated in the VM Kula system.

## Process Flow Diagram (BPMN)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       PREDICTION GENERATION PROCESS                              │
└─────────────────────────────────────────────────────────────────────────────────┘

  START: POST /api/update-predictions
    │
    ▼
┌──────────────────────────────────┐
│ 1. Load Tournament Data          │
│    - Teams from Firestore        │
│    - Matches from Firestore      │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. Fetch Team Statistics (with Caching)                      │
│                                                               │
│   FOR EACH TEAM:                                             │
│   ┌─────────────────────────────────────────┐               │
│   │ Check Firestore Cache (24h TTL)         │               │
│   └─────┬───────────────────┬────────────────┘               │
│         │                   │                                │
│    Cache HIT          Cache MISS                             │
│         │                   │                                │
│         │                   ▼                                │
│         │         ┌─────────────────────────┐               │
│         │         │ Has API-Football ID?    │               │
│         │         └─────┬──────────┬────────┘               │
│         │               │          │                        │
│         │             YES         NO                        │
│         │               │          │                        │
│         │               ▼          ▼                        │
│         │    ┌──────────────┐  ┌──────────────┐            │
│         │    │ Fetch from   │  │ Use Fallback │            │
│         │    │ API-Football │  │ Stats        │            │
│         │    │ - xG         │  │              │            │
│         │    │ - Form       │  └──────────────┘            │
│         │    │ - Clean Sht  │                              │
│         │    └──────┬───────┘                              │
│         │           │                                       │
│         │           ▼                                       │
│         │    ┌──────────────┐                              │
│         │    │ Save to      │                              │
│         │    │ Firestore    │                              │
│         │    └──────┬───────┘                              │
│         │           │                                       │
│         └───────────┴─────────────────────────────────────►│
│                     │                                       │
│                     ▼                                       │
│            Team Stats Collected                            │
└─────────────────────┬──────────────────────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────────────────────────┐
│ 3. Generate AI Predictions (with Smart Caching)               │
│                                                                 │
│   FOR EACH MATCH:                                              │
│   ┌──────────────────────────────────────────┐                │
│   │ Calculate Stats Hash                      │                │
│   │ (home_stats + away_stats)                 │                │
│   └─────┬────────────────────────────────────┘                │
│         │                                                       │
│         ▼                                                       │
│   ┌──────────────────────────────────────────┐                │
│   │ Check if Stats Changed?                  │                │
│   └─────┬──────────────────┬─────────────────┘                │
│         │                  │                                   │
│    Stats SAME        Stats CHANGED                             │
│         │                  │                                   │
│         ▼                  ▼                                   │
│   ┌──────────┐      ┌────────────────────────────┐           │
│   │ Use      │      │ Fetch API-Football         │           │
│   │ Cached   │      │ Prediction (if available)  │           │
│   │ Predict  │      └────────┬───────────────────┘           │
│   └──────────┘               │                                │
│                              ▼                                │
│                    ┌───────────────────────┐                 │
│                    │ Build Matchup Data    │                 │
│                    │ - Home team stats     │                 │
│                    │ - Away team stats     │                 │
│                    │ - API-Football pred   │                 │
│                    └────────┬──────────────┘                 │
│                             │                                │
│                             ▼                                │
│                    ┌────────────────────────────────┐       │
│                    │ Call Gemini AI (with Retry)    │       │
│                    │                                 │       │
│                    │ Prompt (Norwegian):             │       │
│                    │ - Team statistics               │       │
│                    │ - xG, form, clean sheets        │       │
│                    │ - API-Football prediction       │       │
│                    │                                 │       │
│                    │ Max 1 retry (2 attempts)        │       │
│                    └────┬────────────────────────────┘       │
│                         │                                    │
│                ┌────────┴────────┐                           │
│                │                 │                           │
│           SUCCESS           FAILURE                          │
│                │                 │                           │
│                ▼                 ▼                           │
│         ┌─────────────┐   ┌────────────────┐               │
│         │ Parse JSON  │   │ Rule-Based     │               │
│         │ Response    │   │ Fallback       │               │
│         │             │   │ (xG-based)     │               │
│         └──────┬──────┘   └────────┬───────┘               │
│                │                   │                        │
│                └───────────────────┘                        │
│                         │                                   │
│                         ▼                                   │
│                ┌─────────────────┐                          │
│                │ Save Prediction │                          │
│                │ to Firestore    │                          │
│                │ with Stats Hash │                          │
│                └─────────────────┘                          │
└─────────────────────────┬──────────────────────────────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ 4. Merge Results │
                 │    - Predictions │
                 │    - Matches     │
                 │    - has_real_   │
                 │      data flags  │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ 5. Publish to    │
                 │    Firestore     │
                 │    latest doc    │
                 └────────┬─────────┘
                          │
                          ▼
                        END
```

## Detailed Component Breakdown

### 1. **Data Aggregator** (`src/data_aggregator.py`)
**Purpose**: Fetch and compute team statistics from API-Football

**Key Methods**:
- `fetch_team_stats(team_id, fetch_xg=True)`
  - Fetches last 5 matches for team
  - Computes metrics: avg_xG, clean sheets, form string
  - Implements rate limiting (0.5s between requests)
  - Exponential backoff retry (1s, 2s, 4s)
  - Max 3 retries

**Caching**:
- **File cache**: Local JSON cache with date-based expiry
- **Firestore cache**: 24-hour TTL for team stats
- Cache key: `team_stats_{team_id}_{YYYY-MM-DD}.json`

**Metrics Computed**:
```python
{
  "avg_xg": 1.45,              # Average expected goals
  "clean_sheets": 2,            # Matches with 0 goals conceded
  "form_string": "W-D-W-W-L",  # Last 5 results (most recent first)
  "data_completeness": 0.8,    # % of matches with xG data
  "confidence": "high",         # high/medium/low
  "has_real_data": true        # Real vs fallback data
}
```

---

### 2. **AI Agent** (`src/ai_agent.py`)
**Purpose**: Generate match predictions using Google Gemini AI

**Key Methods**:
- `generate_prediction(matchup)` - Main prediction method
- `call_gemini(matchup)` - API call to Gemini
- `rule_based_prediction(matchup)` - Fallback logic

**Gemini Configuration**:
- Model: `gemini-2.5-flash` (Tier 1 Paid)
- Response mode: JSON
- Temperature: 0.7
- Rate limit: 2,000 RPM (0.05s min delay)

**Retry Strategy**:
1. First attempt → Call Gemini
2. If fails → Wait 1s, retry
3. If fails again → Use rule-based fallback

**Prompt Structure** (Norwegian):
```
Spå resultatet av denne VM 2026-kampen:

Hjemmelag: Norge
- Gjennomsnittlig xG: 1.45
- Nullet motstanderen: 2
- Siste form: W-W-D-L-W

Bortelag: Sverige
- Gjennomsnittlig xG: 1.32
- Nullet motstanderen: 1
- Siste form: D-W-W-L-D

[Optional API-Football prediction data]

Gi spådommen som JSON...
```

**Response Format**:
```json
{
  "winner": "Norge",
  "win_probability": 0.65,
  "predicted_home_score": 2,
  "predicted_away_score": 1,
  "reasoning": "Norge har bedre form og høyere xG"
}
```

**Fallback Logic** (Rule-Based):
- Compare `avg_xg` values
- If diff < 0.3 → Predict draw
- If diff > 0.3 → Predict team with higher xG
- Always marked with `confidence: "low"`

---

### 3. **Firestore Manager** (`src/firestore_manager.py`)
**Purpose**: Manage all Firestore operations with smart caching

**Collections**:
- `teams` - Team data with API-Football IDs
- `matches` - Match fixtures and labels
- `team_stats` - Cached team statistics (24h TTL)
- `match_predictions` - Cached predictions with stats hash

**Smart Caching Logic**:
```python
# Calculate hash of team stats
stats_hash = calculate_stats_hash(home_stats, away_stats)

# Check if prediction needs regeneration
if cached_hash != current_hash:
    regenerate_prediction()
else:
    use_cached_prediction()
```

**Cache Invalidation**:
- Team stats expire after 24 hours
- Predictions regenerate when team stats change
- Stats hash prevents unnecessary AI calls

---

### 4. **Main Pipeline** (`src/main.py`)

**Endpoint**: `POST /api/update-predictions`

**Steps**:
1. **Load tournament data** from Firestore
2. **Fetch team stats** (with Firestore + file caching)
3. **Generate predictions** (with smart caching)
4. **Merge results** into tournament snapshot
5. **Publish** to Firestore `predictions/latest`

**Performance Optimizations**:
- Firestore cache reduces API calls by ~80%
- Smart prediction caching (regenerate only when stats change)
- Parallel-safe with rate limiting
- Exponential backoff on failures

**Response**:
```json
{
  "status": "success",
  "predictions_generated": 104,
  "gemini_success": 98,
  "gemini_fallback": 6,
  "firestore_cache_hits": 42,
  "firestore_cache_misses": 6,
  "predictions_cached": 85,
  "predictions_regenerated": 19,
  "elapsed_seconds": 12.45
}
```

---

## Data Flow Summary

```
API-Football → DataAggregator → Firestore Cache
                                      ↓
                         Team Stats (with xG, form)
                                      ↓
                         AI Agent (Gemini)
                                      ↓
        JSON Prediction (winner, score, reasoning)
                                      ↓
                         Firestore Cache
                                      ↓
                    Frontend (Firebase SDK)
```

## Key Features

### 1. **Multi-Layer Caching**
- **L1**: Firestore (24h TTL) - Shared across instances
- **L2**: File cache (date-based) - Local instance cache
- **L3**: Prediction cache (invalidates on stats change)

### 2. **Fallback Resilience**
- Gemini failure → Rule-based prediction
- API-Football failure → Cached/fallback stats
- Missing xG → Form-based prediction

### 3. **Rate Limiting**
- API-Football: 0.5s delay between requests
- Gemini: 0.05s min delay (2,000 RPM)
- Exponential backoff on failures

### 4. **Data Quality Indicators**
- `has_real_data` flag on matches/predictions
- `confidence` level (high/medium/low)
- `data_completeness` percentage

### 5. **Norwegian Language**
- Prompts in Norwegian
- Reasoning in Norwegian
- Team names in Norwegian (from database)

---

## Error Handling

### Gemini Failures
1. **429 Rate Limit** → Immediate fallback (no wait)
2. **API Error** → Retry once, then fallback
3. **Parsing Error** → Retry once, then fallback

### API-Football Failures
1. **429 Rate Limit** → Raise error, use cache
2. **Network Error** → Retry 3x with backoff
3. **Missing Data** → Use fallback stats

### Firestore Failures
- Graceful degradation
- Continue with cached data
- Log errors for monitoring

---

## Configuration

**Environment Variables**:
- `GEMINI_API_KEY` - Google AI API key
- `API_FOOTBALL_KEY` - API-Football API key
- `FIRESTORE_PROJECT_ID` - Firebase project ID

**Constants**:
- `CACHE_TTL_HOURS`: 24 (team stats)
- `MAX_RETRIES`: 3 (API calls)
- `RETRY_DELAYS`: [1, 2, 4] seconds
- `RATE_LIMIT_DELAY`: 0.5 seconds (API-Football)

---

## Testing

See `backend/tests/` for unit and integration tests:
- `test_ai_agent.py` - AI prediction tests
- `test_data_aggregator.py` - API fetching tests
- `test_integration.py` - End-to-end pipeline tests
