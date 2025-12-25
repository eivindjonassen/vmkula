Her er den komplette, reviderte spesifikasjonen. Denne er skreddersydd for å gis direkte til en AI-kodemakker (som OpenCode/Cursor).

Den inkorporerer alle de kritiske valgene vi har tatt: **Python for logikk (FIFA-regler)**, **SQLite for struktur**, **API-Football for rådata**, og **Gemini kun for prediksjon**.

---

# vmkula - Technical Specification (Master)

## 1. Architecture Overview

* **Core Philosophy:** "Logic in Python, Magic in AI". We do not ask AI to calculate standings. We calculate standings in Python, then ask AI to predict outcomes based on those facts.
* **Frontend:** Next.js (App Router) + Tailwind CSS.
* **Backend Logic:** Python 3.11+ (Cloud Run Job).
* *Libraries:* `pandas` (DataFrames), `sqlite3`, `google-generative-ai`, `requests`.


* **Databases:**
* **Static:** `worldcup2026.db` (SQLite) - Contains the tournament skeleton, teams, and schedule.
* **Live Cache:** Firestore - Stores the final processed prediction JSON for the frontend.


* **External Data:** API-Football (v3).

## 2. Data Flow Pipeline

The Python backend job runs sequentially:

1. **Hydrate Skeleton:** Load tournament structure from `worldcup2026.db`.
2. **Fetch Live Data:** Call API-Football for match results & advanced stats (xG).
3. **Run FIFA Engine:**
* Calculate Tables (Points, GD, Goals).
* Rank 3rd Place Teams (Top 8 qualify).
* Resolve "Round of 32" Matchups (Map "Winner A" vs "3rd Place C" to actual teams).


4. **Prepare AI Context:** Aggregate stats (e.g., "Avg xG last 5 games") into a prompt.
5. **Predict (AI):** Send specific matchups to Gemini 3.0 Pro.
6. **Publish:** Push valid JSON to Firestore.

## 3. TDD Implementation Plan

### Phase 1: The Skeleton & Database (SQLite)

**Goal:** Ensure we can read the tournament structure correctly.
**File:** `backend/db_manager.py`

*Test Spec:*

```python
def test_get_tournament_structure():
    # Should return all matches joined with stage names
    db = DatabaseManager("worldcup2026.db")
    matches = db.get_all_matches()
    
    # Assert we have 104 matches (48 team format)
    assert len(matches) == 104
    # Assert we can identify a Round of 32 match
    r32 = next(m for m in matches if m['stage_name'] == 'Round of 32')
    assert "Winner" in r32['match_label'] or "Runner-up" in r32['match_label']

```

### Phase 2: The FIFA Engine (Core Logic)

**Goal:** Calculate standings and resolve the complex "Best 3rd Place" matchups.
**File:** `backend/fifa_engine.py`

*Test Spec:*

```python
def test_calculate_group_standings():
    # Input: List of match results (dictionaries)
    results = [
        {"home": "Mexico", "away": "Poland", "home_score": 2, "away_score": 1, "group": "A"},
        {"home": "Mexico", "away": "Egypt", "home_score": 0, "away_score": 0, "group": "A"},
        # ... add more to complete a group
    ]
    engine = FifaEngine()
    table = engine.calculate_standings(results)
    
    # Mexico should be 1st with 4 points
    assert table['A'][0]['team'] == "Mexico"
    assert table['A'][0]['points'] == 4

def test_rank_third_place_teams():
    # Input: Mock tables for 12 groups
    engine = FifaEngine()
    # Mock data where Group A 3rd place has 6 points, Group B has 1 point
    qualified = engine.get_qualified_third_places(mock_tables)
    
    assert len(qualified) == 8
    assert "Group A Team" in qualified
    assert "Group B Team" not in qualified

def test_resolve_knockout_matchups():
    # The HARDEST test: Mapping "Winner A vs 3rd Place C/D/E"
    engine = FifaEngine()
    
    # Scenario: Winner A is Mexico. 3rd Place C is qualified.
    resolved_matches = engine.resolve_bracket(
        group_winners={"A": "Mexico", ...},
        qualified_thirds=["C", "D", "E", ...]
    )
    
    match_74 = resolved_matches[74] # ID from SQLite
    assert match_74['home_team'] == "Mexico"
    assert match_74['away_team'] == "Poland" # Assuming Poland was 3rd in C

```

### Phase 3: Data Aggregation (The "Smart" Layer)

**Goal:** Convert raw API-Football data into "AI-ready" metrics. Don't send raw logs to AI.
**File:** `backend/data_aggregator.py`

*Test Spec:*

```python
def test_aggregate_team_form():
    # Mock API response for last 5 matches
    mock_fixtures = [
        {"goals": {"for": 2, "against": 0}, "statistics": [{"type": "expected_goals", "value": 2.4}]},
        {"goals": {"for": 1, "against": 1}, "statistics": [{"type": "expected_goals", "value": 0.8}]},
        # ... 3 more
    ]
    
    aggregator = DataAggregator()
    stats = aggregator.compute_metrics(mock_fixtures)
    
    assert stats['avg_xg'] == 1.6  # (2.4 + 0.8 + ...) / 5
    assert stats['clean_sheets'] == 1
    assert stats['form_string'] == "W-D-..."

```

### Phase 4: The AI Agent (Gemini)

**Goal:** Generate predictions based on the aggregated stats.
**File:** `backend/ai_agent.py`

*Test Spec:*

```python
def test_generate_prediction_prompt():
    # Ensure the prompt contains the calculated stats, not just names
    agent = AiAgent()
    matchup = {
        "home": "Mexico", "home_stats": {"avg_xg": 1.5},
        "away": "Chile", "away_stats": {"avg_xg": 0.9}
    }
    
    prompt = agent.build_prompt(matchup)
    
    assert "Mexico" in prompt
    assert "1.5" in prompt # vital: stats must be in prompt
    assert "Return valid JSON" in prompt

def test_parse_gemini_response():
    # Test that we can handle Markdown formatting if Gemini adds it
    raw_response = "```json\n{\"winner\": \"Mexico\"}\n```"
    parsed = AiAgent.clean_json(raw_response)
    assert parsed['winner'] == "Mexico"

```

## 4. API-Football Strategy (Specific Endpoints)

To avoid over-fetching, define these distinct operations:

1. **`update_scores()`**:
* Call `GET /fixtures?league=1&season=2026&status=FT`
* *Frequency:* Every 5 min during games, or once daily.


2. **`fetch_team_stats(team_id)`**:
* Call `GET /fixtures?team={id}&last=5` -> Loop IDs -> `GET /fixtures/statistics?fixture={id}`
* *Frequency:* Once per day (stats don't change during matches).
* *Note:* Save this to a local cache/temp file so we don't spam the API during development.



## 5. Output Artifact (Firestore Schema)

The final result of the Python job:

```json
{
  "updated_at": "2026-06-12T10:00:00Z",
  "groups": { ... }, // Calculated by Python
  "bracket": [
    {
      "match_id": 73,
      "label": "Round of 32",
      "teams": {"home": "Mexico", "away": "Chile"},
      "ai_prediction": {
        "winner": "Mexico",
        "prob": 65,
        "reasoning": "Mexico's xG of 1.5 is superior..."
      }
    }
  ]
}

```