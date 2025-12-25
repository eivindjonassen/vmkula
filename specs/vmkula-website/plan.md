# Implementation Plan: vmkula-website

**Branch**: N/A (initial commit) | **Date**: 2025-12-25 | **Spec**: [specs/vmkula-website/spec.md](spec.md)

---

## Planning Strategy

### Scope Assessment

- **Codebase Size**: Small (<20 files currently, POC only)
- **Research Scope**: Medium - Greenfield production implementation
- **Agent Assistance Recommended**: No - Direct planning sufficient
- **Research Status**: ✅ Complete (see research.md)

---

## Technical Context

- **Language/Framework**: 
  - **Frontend**: Next.js 15+ (App Router), React 19+, TypeScript 5.8+
  - **Backend**: Python 3.11+, FastAPI (for Cloud Run HTTP endpoint)
- **Primary Dependencies**:
  - **Frontend**: Next.js, Tailwind CSS, Firebase SDK (Firestore client)
  - **Backend**: pandas, google-cloud-firestore, google-generative-ai, requests, pytest
- **Storage**: 
  - **Static Data**: SQLite (`worldcup2026.db`) - bundled with backend
  - **Live Cache**: Firestore (predictions collection)
  - **Local Cache**: JSON files for API-Football responses (development only)
- **Testing**: 
  - **Backend**: Pytest with TDD enforcement
  - **Frontend**: Vitest + React Testing Library
- **Project Type**: Monorepo (frontend/ + backend/ structure)
- **Deployment**:
  - **Frontend**: Firebase Hosting
  - **Backend**: Google Cloud Run (HTTP service, trigger-on-demand + scheduled)

---

## Constitution Check

**Note**: No `RULES.md` file exists in this project. Constitutional compliance based on project standards from `AGENTS.md` and `init-rules.md`:

- **Rule 1 (TDD Enforcement)**: ✅ **COMPLIANT** - Plan includes TDD workflow with failing tests first for all backend logic (fifa_engine, data_aggregator, ai_agent).
  - **Evidence**: Phase 1 creates pytest infrastructure and test files before implementation.

- **Rule 2 (Component Reusability)**: ✅ **COMPLIANT** - Plan reuses POC type definitions and component logic patterns.
  - **Evidence**: Phase 3 ports `types.ts` interfaces and `GroupCard` component structure.

- **Rule 3 (Cost Optimization)**: ✅ **COMPLIANT** - Aggressive caching strategy to minimize API calls.
  - **Evidence**: 24-hour TTL on local JSON cache for API-Football, single Firestore document for predictions.

- **Rule 4 (Domain-First Design)**: ✅ **COMPLIANT** - Core FIFA engine logic implemented in Python, not delegated to AI.
  - **Evidence**: `fifa_engine.py` implements standings calculation following spec philosophy "Logic in Python, Magic in AI".

---

## Project Structure

**Structure Decision**: **Monorepo** - Frontend and backend in same repository for easier dependency management, shared type definitions, and simplified CI/CD.

```
vmkula/
├── frontend/               # Next.js App Router application
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx        # Home with tabs (groups/matches/bracket)
│   │   ├── groups/
│   │   │   └── page.tsx
│   │   ├── matches/
│   │   │   └── page.tsx
│   │   └── bracket/
│   │       └── page.tsx
│   ├── components/
│   │   ├── ui/             # Reusable atoms (Button, Card, etc.)
│   │   ├── GroupCard.tsx
│   │   ├── MatchCard.tsx
│   │   └── BracketView.tsx
│   ├── lib/
│   │   ├── firestore.ts    # Firestore client
│   │   ├── types.ts        # Shared TypeScript types (ported from POC)
│   │   └── utils.ts
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.js
│   └── vitest.config.ts
│
├── backend/                # Python Cloud Run service
│   ├── src/
│   │   ├── __init__.py
│   │   ├── db_manager.py       # SQLite interface
│   │   ├── fifa_engine.py      # Group standings + knockout resolution
│   │   ├── data_aggregator.py  # API-Football → metrics
│   │   ├── ai_agent.py         # Gemini prediction generator
│   │   ├── firestore_publisher.py  # Firestore write operations
│   │   ├── main.py             # FastAPI app (HTTP endpoint)
│   │   └── config.py           # Environment variables, constants
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_db_manager.py
│   │   ├── test_fifa_engine.py
│   │   ├── test_data_aggregator.py
│   │   ├── test_ai_agent.py
│   │   └── fixtures/           # Mock API responses
│   ├── cache/                  # API-Football local cache (dev only, in .gitignore)
│   ├── worldcup2026.db         # SQLite tournament structure (moved from root)
│   ├── requirements.txt
│   ├── requirements-dev.txt    # pytest, black, mypy
│   ├── Dockerfile              # Cloud Run container
│   └── pytest.ini
│
├── poc/                    # KEEP AS REFERENCE - do not modify
│   └── [existing POC files]
│
├── specs/                  # Bifrost artifacts
│   └── vmkula-website/
│       ├── spec.md
│       ├── plan.md         # This file
│       ├── tasks.md
│       ├── session.md
│       ├── research.md
│       └── data-model.md
│
├── .bifrost/               # AI development framework
├── .opencode/
├── .github/
│   └── workflows/
│       ├── backend-test.yml    # Pytest on push
│       └── frontend-test.yml   # Vitest on push
│
├── .gitignore
├── .env.example            # Template for local development
└── README.md
```

---

## Phase 0: ACE-Enhanced Research & Exploration

### Research Summary (✅ COMPLETE)

**Key Findings**:
1. **POC Status**: Working Vite + React prototype with client-side Gemini integration
2. **Database**: SQLite `worldcup2026.db` complete with 104 matches, 48 teams, 12 groups
3. **No Production Code**: Zero Next.js or Python implementation exists
4. **No Tests**: TDD enforcement required but no test infrastructure exists
5. **Reusable Assets**: POC types, component logic, Gemini prompt structure

**Research Output**: See `research.md` for comprehensive findings.

---

## Phase 1: Design & Contracts

### 1.1 Data Model Design

**File**: `specs/vmkula-website/data-model.md`

See `data-model.md` for complete entity definitions, relationships, and data flow diagram.

### 1.2 API Contracts

#### Backend Endpoint: Trigger Prediction Update (Cloud Run)

**POST** `/api/update-predictions`

**Description**: Triggers the backend pipeline to calculate standings and generate predictions

**Authentication**: Cloud Run IAM (internal only) or API key for development

**Request Body**: 
```json
{}
```

**Response (200 OK)**:
```json
{
  "status": "success",
  "updated_at": "2026-06-12T10:00:00Z",
  "predictions_generated": 104,
  "errors": []
}
```

**Response (500 Internal Server Error)**:
```json
{
  "status": "error",
  "message": "Failed to fetch API-Football data",
  "details": { "error_code": "API_RATE_LIMIT" }
}
```

#### Backend Endpoint: Health Check

**GET** `/health`

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "database": "connected",
  "firestore": "connected",
  "cache_size": "1.2 MB"
}
```

#### Firestore Contract

**Collection**: `predictions`  
**Document**: `latest`

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
        "rank": 1
      }
    ]
  },
  "bracket": [
    {
      "match_id": 73,
      "match_number": 73,
      "stage": "Round of 32",
      "home_team": "Mexico",
      "away_team": "Poland",
      "kickoff_at": "2026-06-21T15:00:00Z",
      "venue": "MetLife Stadium, New Jersey",
      "prediction": {
        "predicted_winner": "Mexico",
        "win_probability": 65,
        "predicted_home_score": 2,
        "predicted_away_score": 1,
        "reasoning": "Mexico's avg xG of 1.8 vs Poland's 1.2 indicates offensive dominance.",
        "confidence": "high"
      }
    }
  ],
  "ai_summary": "The tournament setup favors European and South American teams...",
  "favorites": ["Brazil", "France", "Argentina"],
  "dark_horses": ["Mexico", "Japan", "Senegal"]
}
```

### 1.3 Failing Tests (TDD Setup)

#### Backend Test: `tests/test_fifa_engine.py`

```python
import pytest
from src.fifa_engine import FifaEngine

def test_calculate_group_standings_basic():
    """Test basic standings calculation with clear winner"""
    engine = FifaEngine()
    results = [
        {"home": "Mexico", "away": "Poland", "home_score": 2, "away_score": 1, "group": "A"},
        {"home": "Mexico", "away": "Egypt", "home_score": 0, "away_score": 0, "group": "A"},
        {"home": "Poland", "away": "Egypt", "home_score": 1, "away_score": 0, "group": "A"},
    ]
    
    standings = engine.calculate_standings(results)
    
    # Mexico: 4 pts (W, D), GD +1
    # Poland: 3 pts (L, W), GD 0
    # Egypt: 1 pt (D, L), GD -1
    assert standings['A'][0]['team'] == "Mexico"
    assert standings['A'][0]['points'] == 4
    assert standings['A'][1]['team'] == "Poland"


def test_tiebreaker_fair_play_points():
    """
    CRITICAL TEST: When teams have equal points, GD, and goals,
    Fair Play Points must be the tiebreaker.
    
    Scenario: Mexico and Poland both have 4 points, +1 GD, 3 GF.
    Mexico: 1 yellow card = -1 fair play point
    Poland: 1 red card = -4 fair play points
    
    Expected: Mexico ranks higher (better fair play)
    """
    engine = FifaEngine()
    results = [
        {
            "home": "Mexico", "away": "Egypt", 
            "home_score": 2, "away_score": 0, "group": "A",
            "cards": {"home": {"yellow": 1, "red": 0}, "away": {"yellow": 0, "red": 0}}
        },
        {
            "home": "Poland", "away": "Chile", 
            "home_score": 2, "away_score": 0, "group": "A",
            "cards": {"home": {"yellow": 0, "red": 1}, "away": {"yellow": 0, "red": 0}}
        },
    ]
    
    standings = engine.calculate_standings(results)
    
    # THIS TEST WILL FAIL until fair play logic is implemented
    assert standings['A'][0]['team'] == "Mexico"
    assert standings['A'][0]['fair_play_points'] == -1
    assert standings['A'][1]['team'] == "Poland"
    assert standings['A'][1]['fair_play_points'] == -4


def test_rank_third_place_teams():
    """Test selection of top 8 third-place teams across 12 groups"""
    # Detailed implementation from vmkula-init.md
    pass


def test_resolve_knockout_matchups():
    """Test Round of 32 bracket resolution with 3rd place teams"""
    # Detailed implementation from vmkula-init.md
    pass
```

#### Backend Test: `tests/test_data_aggregator.py`

```python
import pytest
from src.data_aggregator import DataAggregator

def test_missing_xg_data_handling():
    """
    CRITICAL TEST: Handle missing xG data gracefully.
    
    Scenario: 5 matches, only 3 have xG data.
    Expected: Calculate avg xG from available data (3 matches),
    set data_completeness = 0.6 (3/5), confidence = "medium"
    """
    aggregator = DataAggregator()
    
    mock_fixtures = [
        {"goals": {"for": 2, "against": 0}, "statistics": [{"type": "expected_goals", "value": 2.4}]},
        {"goals": {"for": 1, "against": 1}, "statistics": [{"type": "expected_goals", "value": 0.8}]},
        {"goals": {"for": 1, "against": 0}, "statistics": []},  # Missing xG
        {"goals": {"for": 0, "against": 1}, "statistics": []},  # Missing xG
        {"goals": {"for": 3, "against": 1}, "statistics": [{"type": "expected_goals", "value": 2.2}]},
    ]
    
    stats = aggregator.compute_metrics(mock_fixtures)
    
    # THIS TEST WILL FAIL until missing data handling is implemented
    assert stats['avg_xg'] == pytest.approx(1.8, 0.1)  # (2.4 + 0.8 + 2.2) / 3
    assert stats['clean_sheets'] == 2
    assert stats['data_completeness'] == 0.6
    assert stats['confidence'] == "medium"


def test_rate_limiting_with_delay():
    """
    CRITICAL TEST: Ensure API calls are throttled to avoid 429 errors.
    Expected: 0.5 second delay between consecutive API requests.
    """
    pass


def test_local_cache_ttl():
    """
    CRITICAL TEST: Use cached data if less than 24 hours old.
    """
    pass
```

#### Frontend Test: `frontend/__tests__/GroupCard.test.tsx`

```tsx
import { render, screen } from '@testing-library/react';
import GroupCard from '@/components/GroupCard';

test('displays group standings sorted by points', () => {
  const mockGroup = {
    id: 'A',
    name: 'Group A',
    teams: [
      { id: 1, name: 'Poland', points: 3, rank: 2 },
      { id: 2, name: 'Mexico', points: 7, rank: 1 },
    ]
  };
  
  render(<GroupCard group={mockGroup} predictions={[]} />);
  
  const rows = screen.getAllByRole('row');
  expect(rows[1]).toHaveTextContent('Mexico');
});
```

---

## Phase 2: Task Planning Approach

*This section describes what the `/tasks` command will generate.*

The `/tasks` command will break down implementation into **TDD-enforced sprints**:

### Sprint 1: Backend Core (TDD) - 3-4 days
1. Set up Python environment (venv, pytest, requirements.txt)
2. Implement `db_manager.py` with tests
3. Implement `fifa_engine.py` - Group standings with Fair Play Points
4. Implement `fifa_engine.py` - Third place ranking
5. Implement `fifa_engine.py` - Round of 32 bracket resolution

### Sprint 2: Data Integration (TDD) - 2-3 days
1. Implement `data_aggregator.py` - API-Football client with caching
2. Implement `data_aggregator.py` - Metrics calculation with missing xG fallback
3. Implement `ai_agent.py` - Gemini integration with retry logic
4. Implement `firestore_publisher.py` - Firestore write operations

### Sprint 3: API Orchestration - 1 day
1. Implement `main.py` FastAPI app with `/api/update-predictions` endpoint
2. Dockerize backend for Cloud Run

### Sprint 4: Frontend Implementation - 3-4 days
1. Set up Next.js App Router project with Firebase SDK
2. Port POC types and create Firestore client
3. Implement GroupCard, MatchCard, BracketView components
4. Build app routes (groups/matches/bracket pages)

### Sprint 5: Integration & Deployment - 1-2 days
1. End-to-end backend test (mock API → Firestore)
2. Frontend integration test (Firestore → UI rendering)
3. Deploy backend to Cloud Run
4. Deploy frontend to Firebase Hosting
5. Set up Cloud Scheduler for periodic updates

**Total Estimated Effort**: ~2 weeks (10-12 days)

---

## Critical Implementation Details

### FIFA Engine Tiebreaker Logic

**CRITICAL REQUIREMENT**: Strict FIFA tiebreaker sequence when teams have equal points:

1. Goal Difference (GD)
2. Goals Scored
3. Head-to-Head (Points, then GD, then Goals)
4. **Fair Play Points** (calculated from cards)
5. **Deterministic Drawing of Lots:**
   * *Problem:* If we use `random.choice()`, the bracket changes every time the script runs, confusing the AI and the users.
   * *Solution:* Use a deterministic seed based on team names.
   * *Code Logic:* `seed = hash(team_a_name + team_b_name)`. The team with the higher hash value always wins the tie-breaker until actual match data changes.

**Fair Play Points Calculation**:
- Yellow card: -1 point
- Second yellow / Indirect red: -3 points
- Direct red card: -4 points

```python
# fifa_engine.py - calculate_standings() implementation

def calculate_standings(self, results: List[MatchResult]) -> Dict[str, List[GroupStanding]]:
    """Calculate group standings with STRICT FIFA tiebreaker rules."""
    
    # Calculate Fair Play Points from match cards
    for standing in standings:
        fair_play = 0
        for match in team_matches:
            cards = match.get('cards', {})
            fair_play -= cards.get('yellow', 0) * 1       # Yellow: -1
            fair_play -= cards.get('second_yellow', 0) * 3 # 2nd Yellow: -3
            fair_play -= cards.get('red', 0) * 4          # Direct Red: -4
        standing['fair_play_points'] = fair_play
    
    # Sort with tiebreakers
    standings.sort(key=lambda x: (
        -x['points'],
        -x['goal_difference'],
        -x['goals_for'],
        -x['fair_play_points'],  # Less negative is better
        -hash(x['team_name'])     # Deterministic final fallback (higher hash wins)
    ))
```

### Data Aggregation Resilience & Rate Limiting

**CRITICAL REQUIREMENTS**:

#### Rate Limiting
- **Implementation**: Insert `time.sleep(0.5)` delay between team requests
- **Retry Logic**: Exponential backoff decorator for 429/5xx errors

```python
# data_aggregator.py - Rate limiting decorators

import time
from functools import wraps

def rate_limit(delay=0.5):
    """Decorator to throttle API calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            time.sleep(delay)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def retry_with_backoff(max_retries=3):
    """Decorator for exponential backoff on 429/5xx errors"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.HTTPError as e:
                    if e.response.status_code in [429, 500, 502, 503]:
                        wait = 2 ** attempt  # 1s, 2s, 4s
                        time.sleep(wait)
                    else:
                        raise
            raise Exception("Max retries exceeded")
        return wrapper
    return decorator

@rate_limit(delay=0.5)
@retry_with_backoff(max_retries=3)
def fetch_team_stats(self, team_id: int) -> TeamStatistics:
    """Fetch team stats with rate limiting + retry logic"""
    # Check cache first
    cached = self.get_cached_stats(team_id)
    if cached:
        return cached
    
    # Fetch from API-Football
    response = requests.get(f"{API_BASE}/fixtures?team={team_id}&last=5")
    response.raise_for_status()
    
    # Save to cache
    stats = self.compute_metrics(response.json())
    self.save_to_cache(team_id, stats)
    
    return stats
```

#### Missing xG Data Handling

**Logic**:
- If `expected_goals` is `null` for a specific match: Exclude from average calculation
- If `expected_goals` is `null` for **ALL** matches: Return fallback flag, use traditional form (W-D-L)

```python
# data_aggregator.py - Missing data handling

def compute_metrics(self, fixtures: List[dict]) -> TeamStatistics:
    """Calculate metrics with missing xG fallback."""
    xg_values = []
    
    for fixture in fixtures:
        stats = fixture.get('statistics', [])
        xg = next((s['value'] for s in stats if s['type'] == 'expected_goals'), None)
        if xg is not None:
            xg_values.append(xg)
    
    if len(xg_values) == 0:
        # ALL matches missing xG
        return {
            'avg_xg': None,
            'data_completeness': 0.0,
            'confidence': 'low',
            'fallback_mode': 'traditional_form'
        }
    
    return {
        'avg_xg': sum(xg_values) / len(xg_values),
        'data_completeness': len(xg_values) / len(fixtures),
        'confidence': 'high' if len(xg_values) == len(fixtures) else 'medium'
    }
```

### Caching Strategy

**CRITICAL REQUIREMENT**: Save API-Football responses to local JSON cache with 24-hour TTL.

```python
# data_aggregator.py - Local caching

import json
from pathlib import Path
from datetime import datetime, timedelta

CACHE_DIR = Path("cache")
CACHE_TTL_HOURS = 24

def get_cached_stats(self, team_id: int) -> TeamStatistics | None:
    """Load from cache if less than 24 hours old"""
    today = datetime.now().strftime("%Y-%m-%d")
    cache_file = CACHE_DIR / f"team_stats_{team_id}_{today}.json"
    
    if cache_file.exists():
        age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if age < timedelta(hours=CACHE_TTL_HOURS):
            with open(cache_file, 'r') as f:
                return TeamStatistics(**json.load(f))
    
    return None

def save_to_cache(self, team_id: int, stats: TeamStatistics):
    """Save stats to local JSON cache"""
    CACHE_DIR.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    cache_file = CACHE_DIR / f"team_stats_{team_id}_{today}.json"
    
    with open(cache_file, 'w') as f:
        json.dump(stats.__dict__, f, indent=2)
```

### Gemini AI Integration

**CRITICAL REQUIREMENTS**:
- Cost-effective retry: Maximum 1 retry with exponential backoff
- Fallback to rule-based prediction if Gemini fails twice
- Parse markdown-wrapped JSON responses

```python
# ai_agent.py - Gemini integration with retry and fallback

def generate_prediction(self, matchup: dict) -> Prediction:
    """Generate prediction with 1-retry max, then fallback."""
    
    for attempt in range(2):  # Max 2 attempts (initial + 1 retry)
        try:
            prompt = self.build_prompt(matchup)
            response = self.gemini_client.generate_content(prompt)
            
            # Parse and validate JSON
            prediction = self.parse_response(response.text)
            return prediction
            
        except Exception as e:
            if attempt == 0:
                # First attempt failed, wait and retry
                time.sleep(1)  # Exponential backoff
            else:
                # Second attempt failed, use fallback
                return self.rule_based_prediction(matchup)
    
def rule_based_prediction(self, matchup: dict) -> Prediction:
    """Fallback prediction based on statistical probability."""
    home_stats = matchup['home_stats']
    away_stats = matchup['away_stats']
    
    # Simple probability based on avg xG difference
    xg_diff = (home_stats.get('avg_xg', 1.0) - away_stats.get('avg_xg', 1.0))
    win_prob = 50 + (xg_diff * 15)  # Scale: 1.0 xG diff = 15% probability shift
    win_prob = max(15, min(85, win_prob))  # Clamp between 15-85%
    
    return {
        'predicted_winner': matchup['home_team'] if win_prob > 50 else matchup['away_team'],
        'win_probability': win_prob if win_prob > 50 else 100 - win_prob,
        'predicted_home_score': 1 if win_prob > 60 else 0,
        'predicted_away_score': 1 if win_prob < 40 else 0,
        'reasoning': 'Statistical probability based on available data (AI unavailable).',
        'confidence': 'low'
    }
```

### History Storage Logic (Diff Check)
Before writing to the `/matches/{id}/history` sub-collection, the script must:
1.  **Fetch the latest entry** from that match's history.
2.  **Compare:** Does the new AI prediction (Winner OR Reasoning) differ significantly from the previous entry?
3.  **Action:**
    * *IF Changed:* Write new document to history.
    * *IF Identical:* Skip writing (save storage costs).

**Implementation**:
```python
# firestore_publisher.py - History diff check

def should_save_prediction_history(match_id: int, new_prediction: Prediction) -> bool:
    """Check if prediction changed significantly from last saved version."""
    
    # Fetch latest history entry
    history_ref = db.collection('matches').document(str(match_id)).collection('history')
    latest_entries = history_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1).get()
    
    if not latest_entries:
        return True  # No history yet, save first entry
    
    latest = latest_entries[0].to_dict()
    
    # Compare winner and reasoning
    winner_changed = latest['predicted_winner'] != new_prediction['predicted_winner']
    reasoning_changed = latest['reasoning'] != new_prediction['reasoning']
    
    return winner_changed or reasoning_changed

def save_prediction_to_history(match_id: int, prediction: Prediction, trigger_event: str):
    """Save prediction to match history if it differs from previous."""
    
    if not should_save_prediction_history(match_id, prediction):
        return  # Skip identical predictions
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    history_ref = db.collection('matches').document(str(match_id)).collection('history').document(timestamp)
    
    history_ref.set({
        'timestamp': prediction['generated_at'],
        'predicted_winner': prediction['predicted_winner'],
        'confidence': prediction['win_probability'],
        'reasoning': prediction['reasoning'],
        'trigger_event': trigger_event
    })
```

---

## Complexity Tracking

| Violation | Justification | Alternative Rejected Because... |
| :--- | :--- | :--- |
| Using Gemini AI (new dependency) | Spec explicitly requires AI predictions for match outcomes | Rule-based predictions lack narrative reasoning |
| Client-side favorites in localStorage | Cost optimization - avoids authentication infrastructure | User accounts add Firebase Auth costs for public website |
| Monorepo structure (multiple languages) | Easier coordination during development | Separate repos complicate shared type definitions |
| Cloud Run instead of Cloud Functions | Better cold start performance + HTTP endpoints | Cloud Functions Gen2 has similar costs but less flexibility |

---

## Next Steps

Run `/tasks vmkula-website` to generate detailed, ordered implementation tasks following TDD principles.

**Estimated Timeline**:
- Week 1: Backend Core + Data Integration (Sprints 1-2)
- Week 2: API Orchestration + Frontend + Deployment (Sprints 3-5)

**Total**: ~2 weeks for full implementation with TDD enforcement
