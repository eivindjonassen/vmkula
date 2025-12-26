# Data Model: vmkula-website

**Created**: 2025-12-25  
**Feature**: vmkula-website  
**Purpose**: Comprehensive data model for World Cup 2026 prediction platform

---

## Entity Definitions

### Core Entities

#### Team
Represents a national team in the tournament.

**Source**: Firestore `teams` collection

```python
class Team:
    id: int                 # Primary key
    name: str               # "Mexico"
    fifa_code: str          # "MEX" (3-letter code)
    flag_emoji: str         # "🇲🇽"
    group_letter: str       # "A"-"L" (null for knockout-only teams)
    is_placeholder: bool    # True for TBD playoff teams (e.g., UEFA playoff winner)
    api_football_id: int    # API-Football team ID (null if no data available)
```

**Example**:
```json
{
  "id": 1,
  "name": "Mexico",
  "fifa_code": "MEX",
  "flag_emoji": "🇲🇽",
  "group": "A",
  "is_placeholder": false,
  "api_football_id": 16
}
```

---

#### Match
Represents a fixture in the tournament.

**Source**: Firestore `matches` collection

```python
class Match:
    id: int                     # Primary key
    match_number: int           # 1-104 (sequential)
    home_team_id: int | None    # None for TBD knockout matches
    away_team_id: int | None
    venue: str                  # "MetLife Stadium, New Jersey"
    stage_id: int               # 1=Group, 2=Round32, 3=Round16, etc.
    kickoff: str                # ISO8601 timestamp (e.g., "2026-06-12T15:00:00Z")
    label: str                  # "Winner A vs 3rd Place C/D/E" or "Mexico vs Poland"
    home_score: int | None      # Actual score (None if not played yet)
    away_score: int | None
    api_football_fixture_id: int | None  # API-Football fixture ID (null if unavailable)
```

**Example (Group Stage)**:
```json
{
  "id": 1,
  "match_number": 1,
  "home_team_id": 1,
  "away_team_id": 2,
  "venue": "MetLife Stadium, New Jersey",
  "stage_id": 1,
  "kickoff": "2026-06-12T15:00:00Z",
  "label": "Mexico vs Poland",
  "home_score": null,
  "away_score": null,
  "api_football_fixture_id": 12345
}
```

**Example (Knockout - TBD)**:
```json
{
  "id": 73,
  "match_number": 73,
  "home_team_id": null,
  "away_team_id": null,
  "venue": "SoFi Stadium, Los Angeles",
  "stage_id": 2,
  "kickoff": "2026-06-21T15:00:00Z",
  "label": "Winner A vs 3rd Place C/D/E",
  "home_score": null,
  "away_score": null,
  "api_football_fixture_id": null
}
```

---

#### GroupStanding
Calculated standings for a team in group stage.

**Source**: Calculated by `fifa_engine.py` from match results

```python
class GroupStanding:
    team_id: int
    team_name: str
    group: str              # "A"-"L"
    played: int
    won: int
    draw: int
    lost: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int             # 3 for win, 1 for draw, 0 for loss
    fair_play_points: int   # CRITICAL: For tiebreaking (negative values)
    rank: int               # 1-4 within group
```

**Fair Play Points Calculation**:
- Yellow card: -1 point
- Second yellow / Indirect red: -3 points
- Direct red card: -4 points

**Example**:
```json
{
  "team_id": 1,
  "team_name": "Mexico",
  "group": "A",
  "played": 3,
  "won": 2,
  "draw": 1,
  "lost": 0,
  "goals_for": 5,
  "goals_against": 1,
  "goal_difference": 4,
  "points": 7,
  "fair_play_points": -2,
  "rank": 1
}
```

---

#### TeamStatistics
Aggregated performance data from API-Football.

**Source**: Calculated by `data_aggregator.py` from API-Football `/fixtures` endpoint

```python
class TeamStatistics:
    team_id: int
    avg_xg_for: float | None        # Average xG in last 5 matches (None if unavailable)
    avg_xg_against: float | None
    clean_sheets: int               # Count of matches with 0 goals conceded
    form_string: str                # "W-W-D-L-W" (last 5 matches, most recent first)
    data_completeness: float        # 0.0-1.0 (percentage of matches with xG data)
    confidence: str                 # "high", "medium", "low"
    fallback_mode: str | None       # "traditional_form" if no xG data available
    has_real_data: bool             # True if team has API-Football ID
```

**Example (Complete Data)**:
```json
{
  "team_id": 1,
  "avg_xg_for": 1.8,
  "avg_xg_against": 0.9,
  "clean_sheets": 3,
  "form_string": "W-W-D-W-L",
  "data_completeness": 1.0,
  "confidence": "high",
  "fallback_mode": null,
  "has_real_data": true
}
```

**Example (Missing xG Data)**:
```json
{
  "team_id": 2,
  "avg_xg_for": 1.2,
  "avg_xg_against": 1.5,
  "clean_sheets": 1,
  "form_string": "L-D-W-L-D",
  "data_completeness": 0.6,
  "confidence": "medium",
  "fallback_mode": null,
  "has_real_data": true
}
```

**Example (No xG Data)**:
```json
{
  "team_id": 3,
  "avg_xg_for": null,
  "avg_xg_against": null,
  "clean_sheets": 2,
  "form_string": "W-D-D-L-W",
  "data_completeness": 0.0,
  "confidence": "low",
  "fallback_mode": "traditional_form",
  "has_real_data": false
}
```

---

#### Prediction
AI-generated match prediction.

**Source**: Generated by `ai_agent.py` using Gemini AI

```python
class Prediction:
    match_id: int
    predicted_winner: str           # Team name or "Draw"
    win_probability: float          # 0-100 (percentage)
    predicted_home_score: int
    predicted_away_score: int
    reasoning: str                  # AI explanation (1-2 sentences)
    confidence: str                 # "high", "medium", "low" (based on data completeness)
    generated_at: str               # ISO8601 timestamp
    has_real_data: bool             # True if both teams have real API-Football data
```

**Example**:
```json
{
  "match_id": 73,
  "predicted_winner": "Mexico",
  "win_probability": 65,
  "predicted_home_score": 2,
  "predicted_away_score": 1,
  "reasoning": "Mexico's avg xG of 1.8 vs Poland's 1.2 indicates offensive dominance. Mexico's W-W-D form vs Poland's W-L-D suggests momentum advantage.",
  "confidence": "high",
  "generated_at": "2026-06-12T10:00:00Z",
  "has_real_data": true
}
```

---

#### TournamentSnapshot
Complete prediction state published to Firestore.

**Source**: Assembled by `firestore_publisher.py` from all calculated data

```python
class TournamentSnapshot:
    updated_at: str                                 # ISO8601 timestamp
    groups: Dict[str, List[GroupStanding]]          # "A": [{team1}, {team2}, ...]
    matches: List[Match]                            # All matches (group + knockout)
    bracket: List[BracketMatch]                     # Resolved knockout matchups with predictions
    predictions: List[Prediction]                   # All predictions with has_real_data flags
    ai_summary: str                                 # Overall tournament narrative (from Gemini)
    favorites: List[str]                            # Top 3-5 teams per AI analysis
    dark_horses: List[str]                          # Surprise contender teams
```

**Example**:
```json
{
  "updated_at": "2026-06-12T10:00:00Z",
  "groups": {
    "A": [
      {
        "team_id": 1,
        "team_name": "Mexico",
        "played": 3,
        "won": 2,
        "draw": 1,
        "lost": 0,
        "goals_for": 5,
        "goals_against": 1,
        "goal_difference": 4,
        "points": 7,
        "fair_play_points": -2,
        "rank": 1,
        "has_real_data": true
      }
    ]
  },
  "matches": [
    {
      "id": 1,
      "match_number": 1,
      "stage_id": 1,
      "home_team_id": 1,
      "away_team_id": 2,
      "home_team_name": "Mexico",
      "away_team_name": "Poland",
      "venue": "MetLife Stadium, New Jersey",
      "kickoff": "2026-06-12T15:00:00Z",
      "label": "Mexico vs Poland",
      "has_real_data": true
    }
  ],
  "bracket": [
    {
      "id": 73,
      "match_number": 73,
      "stage_id": 2,
      "home_team_name": "Mexico",
      "away_team_name": "Poland",
      "venue": "SoFi Stadium, Los Angeles",
      "kickoff": "2026-06-21T15:00:00Z",
      "label": "Mexico vs Poland"
    }
  ],
  "predictions": [
    {
      "match_id": 1,
      "match_number": 1,
      "winner": "Mexico",
      "win_probability": 65,
      "predicted_home_score": 2,
      "predicted_away_score": 1,
      "reasoning": "Mexico's avg xG of 1.8 vs Poland's 1.2 indicates offensive dominance.",
      "confidence": "high",
      "has_real_data": true
    }
  ],
  "ai_summary": "The tournament setup favors European and South American teams with strong qualifying campaigns. Brazil, France, and Argentina emerge as clear favorites based on recent form and squad depth. Mexico stands out as a dark horse with home advantage.",
  "favorites": ["Brazil", "France", "Argentina"],
  "darkHorses": ["Mexico", "Japan", "Senegal"]
}
```

---

## Data Relationships & Flow

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ Firestore Collections (PRIMARY DATABASE)                   │
│ - teams (48 teams)                                          │
│ - matches (104 fixtures)                                    │
│ - team_stats (cached, 24h TTL)                              │
│ - match_predictions (cached with stats hash)                │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ Python Backend: firestore_manager.py                        │
│ - Load tournament structure                                 │
│ - Read match schedule                                       │
│ - Cache team stats (24h TTL)                                │
│ - Cache predictions (invalidate on stats change)            │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ Python Backend: fifa_engine.py                              │
│ - Calculate GroupStandings (with Fair Play Points)          │
│ - Rank top 8 third-place teams                              │
│ - Resolve Round of 32 matchups                              │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ├────────────────────────────────────┐
                    ▼                                    ▼
┌─────────────────────────────────────┐  ┌──────────────────────────────────┐
│ API-Football v3                     │  │ Python Backend: ai_agent.py      │
│ - GET /fixtures (match results)     │  │ - Build prompts with stats       │
│ - GET /fixtures/statistics (xG)     │  │ - Call Gemini 3.0 Pro            │
│ - GET /predictions (API predictions)│  │ - Parse JSON responses           │
└───────────────┬─────────────────────┘  │ - Retry + fallback logic         │
                │                        └──────────┬───────────────────────┘
                ▼                                   │
┌─────────────────────────────────────┐            │
│ Python Backend: data_aggregator.py  │            │
│ - Fetch team stats (with caching)   │            │
│ - Calculate TeamStatistics           │            │
│ - Handle missing xG data             │            │
└───────────────┬─────────────────────┘            │
                │                                   │
                └────────────┬──────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ Python Backend: firestore_publisher.py                      │
│ - Assemble TournamentSnapshot                               │
│ - Publish to Firestore                                      │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ Firestore: predictions/latest                               │
│ - Single document with complete snapshot                    │
│ - Updated on-demand or via Cloud Scheduler                  │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ Next.js Frontend: lib/firestore.ts                          │
│ - Fetch predictions/latest document                         │
│ - Display groups, matches, bracket                          │
│ - Trigger backend refresh if stale                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Entity Relationships

### Firestore Schema

**Collection**: `teams`
```json
{
  "id": 1,
  "name": "Mexico",
  "fifa_code": "MEX",
  "group": "A",
  "is_placeholder": false,
  "api_football_id": 16
}
```

**Collection**: `matches`
```json
{
  "id": 1,
  "match_number": 1,
  "home_team_id": 1,
  "away_team_id": 2,
  "venue": "MetLife Stadium, New Jersey",
  "stage_id": 1,
  "kickoff": "2026-06-12T15:00:00Z",
  "label": "Mexico vs Poland",
  "api_football_fixture_id": 12345
}
```

**Collection**: `team_stats` (Cache)
```json
{
  "team_id": 1,
  "stats": {
    "avg_xg_for": 1.8,
    "avg_xg_against": 0.9,
    "clean_sheets": 3,
    "form_string": "W-W-D-W-L",
    "confidence": "high",
    "has_real_data": true
  },
  "cached_at": "2026-06-11T10:00:00Z",
  "ttl_hours": 24
}
```

**Collection**: `match_predictions` (Cache)
```json
{
  "match_id": 1,
  "prediction": {
    "winner": "Mexico",
    "win_probability": 65,
    "predicted_home_score": 2,
    "predicted_away_score": 1,
    "reasoning": "Mexico's avg xG advantage...",
    "confidence": "high"
  },
  "stats_hash": "a1b2c3d4",
  "cached_at": "2026-06-11T10:00:00Z"
}
```

**Document**: `predictions/latest` (Hot Data)
```json
{
  "groups": { ... },
  "matches": [ ... ],
  "bracket": [ ... ],
  "predictions": [ ... ],
  "ai_summary": "...",
  "favorites": [ ... ],
  "darkHorses": [ ... ],
  "updated_at": "2026-06-11T10:00:00Z"
}
```

---

## Validation Rules

### GroupStanding Validation
- `rank` must be 1-4 within each group
- `points` = (won × 3) + (draw × 1)
- `goal_difference` = goals_for - goals_against
- `fair_play_points` ≤ 0 (always negative or zero)

### TeamStatistics Validation
- `data_completeness` must be 0.0-1.0
- `confidence` must be "high", "medium", or "low"
- If `avg_xg_for` is None, `fallback_mode` must be set
- `form_string` must match pattern: /^[WDL](-[WDL]){0,4}$/

### Prediction Validation
- `win_probability` must be 0-100
- `predicted_home_score` and `predicted_away_score` must be ≥ 0
- `confidence` must match `TeamStatistics.confidence` if data-driven
- `reasoning` must be non-empty string

---

## Data Constraints

### Performance Constraints
- Firestore document size: Max 1MB (current snapshot ~50-100KB)
- API-Football rate limit: 100 requests/day (free tier) - **cache aggressively**
- Gemini API cost: ~$0.10 per 104 predictions - **retry max 1 time**

### Data Freshness
- Group standings: Recalculate after each match day
- Team statistics: Update once per day (24-hour cache TTL)
- Predictions: Regenerate when standings change or new stats available

---

## Edge Cases

### Missing Data Scenarios

1. **TBD Knockout Matches**:
   - `home_team_id` and `away_team_id` are `null`
   - `label` contains placeholder text (e.g., "Winner A vs 3rd Place C/D/E")
   - Frontend must display placeholder labels gracefully

2. **Missing xG Data**:
   - Some API-Football matches lack `expected_goals` statistics
   - `data_aggregator.py` excludes those matches from average calculation
   - If ALL matches missing xG, set `fallback_mode = "traditional_form"`

3. **Equal Teams on All Tiebreakers**:
   - If points, GD, goals, head-to-head, and fair play are all equal
   - Final tiebreaker: Random seed (documented as "drawing of lots")

4. **API-Football 429 Error**:
   - Exponential backoff: wait 1s, 2s, 4s
   - After 3 retries, use cached data or fail gracefully

5. **Gemini AI Failure**:
   - After 1 retry (max 2 attempts total), use rule-based prediction
   - Rule-based prediction uses xG differential for probability calculation

---

## Firestore Collection Structure (Optimized)

### 1. Public Read (Hot Data)
* **Document:** `predictions/latest`
* **Content:** Contains the full `groups`, `matches`, `bracket`, and `predictions` arrays with ONLY the *current* snapshot. (Fast load time).

### 2. Cache Collections (Internal)
* **Collection:** `team_stats`
* **Document:** `{team_id}` (e.g., `team_1`)
* **Content:** Cached team statistics with TTL
* **TTL:** 24 hours (invalidated on new API-Football data)

* **Collection:** `match_predictions`
* **Document:** `{match_id}` (e.g., `match_1`)
* **Content:** Cached prediction with stats hash
* **Invalidation:** When stats hash changes (team stats updated)

**Benefits:**
- **Performance**: Main document stays under 1MB Firestore limit
- **Cost Optimization**: Cache reduces API calls (24h TTL for team stats)
- **Smart Regeneration**: Only regenerate predictions when team stats change (hash-based)

---

**End of Data Model**
