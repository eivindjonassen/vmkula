# Tasks: vmkula-website
**Feature**: vmkula-website
**Total Tasks**: 62
**Parallel Tasks**: 18 tasks can run in parallel
**Approach**: Backend-first TDD with aggressive testing. Following "Logic in Python, Magic in AI" philosophy. Tests created before implementation for all backend logic. Frontend follows after backend completion to consume validated APIs.
---
## Phase 1: Setup & Preparation
### T001: Create Python backend project structure
**File**: `backend/src/__init__.py`, `backend/tests/__init__.py`, `backend/requirements.txt`
**Description**: Initialize Python backend project with proper directory structure:
- Create `backend/src/` directory for source code
- Create `backend/tests/` directory for test files
- Create `backend/tests/fixtures/` directory for mock API responses
- Create `backend/cache/` directory for local API caching (add to .gitignore)
- Create `requirements.txt` with production dependencies (pandas, google-cloud-firestore, google-generative-ai, requests, fastapi, uvicorn)
- Create `requirements-dev.txt` with dev dependencies (pytest, pytest-cov, black, mypy)
- Create empty `__init__.py` files in src/ and tests/
- Move `worldcup2026.db` from root to `backend/` directory
**Dependencies**: None
**Parallel**: Yes [P]
**Status**: ✅ Complete
### T002: Configure pytest and test infrastructure
**File**: `backend/pytest.ini`, `backend/.coveragerc`
**Description**: Set up pytest configuration for TDD enforcement:
- Create `pytest.ini` with test discovery patterns (test_*.py)
- Configure coverage reporting (minimum 80% threshold per spec)
- Add coverage report formats (terminal + HTML)
- Set up pytest markers for unit vs integration tests
- Configure test paths to include tests/ directory
- Add coverage exclusions for `__init__.py` files
**Dependencies**: T001
**Parallel**: No
**Status**: ✅ Complete
### T003: Set up Next.js frontend project structure
**File**: `frontend/package.json`, `frontend/app/layout.tsx`, `frontend/tsconfig.json`
**Description**: Initialize Next.js 15+ App Router project:
- Run `npx create-next-app@latest frontend` with TypeScript, Tailwind CSS, App Router
- Configure `tsconfig.json` with strict type checking
- Create `app/layout.tsx` with basic HTML structure
- Create `lib/` directory for utilities and services
- Create `components/ui/` directory for reusable atoms
- Install Firebase SDK: `firebase` (Firestore client)
- Create `.env.local.example` template for environment variables
- Configure `next.config.js` for Firebase Hosting output
**Dependencies**: None
**Parallel**: Yes [P]
**Status**: ✅ Complete
### T004: Configure Vitest for frontend testing
**File**: `frontend/vitest.config.ts`, `frontend/__tests__/setup.ts`
**Description**: Set up Vitest + React Testing Library:
- Install vitest, @testing-library/react, @testing-library/jest-dom
- Create `vitest.config.ts` with React plugin and test environment
- Create `__tests__/setup.ts` for global test setup
- Configure path aliases to match tsconfig.json (@/ for app root)
- Add test scripts to package.json (test, test:ui, test:coverage)
**Dependencies**: T003
**Parallel**: No
**Status**: ✅ Complete
### T005: Create environment configuration files
**File**: `backend/src/config.py`, `.env.example`, `.gitignore`
**Description**: Set up environment variable management:
- Create `backend/src/config.py` with environment variable loading (API_FOOTBALL_KEY, GEMINI_API_KEY, FIRESTORE_PROJECT_ID)
- Create `.env.example` template with all required variables documented
- Update `.gitignore` to exclude `.env`, `backend/cache/`, `*.pyc`, `__pycache__/`
- Add validation for required environment variables on startup
- Include default values for optional settings (CACHE_TTL_HOURS=24)
**Dependencies**: T001
**Parallel**: Yes [P]
**Status**: ✅ Complete
---
## Phase 2: Tests First (TDD)
### T006: Create test for db_manager basic operations
**File**: `backend/tests/test_db_manager.py`
**Description**: Create failing tests for SQLite database interface:
- Test `load_all_teams()` returns 48 teams with correct schema (id, name, fifa_code, group_letter)
- Test `load_all_matches()` returns 104 matches with proper relationships
- Test `load_group_teams(group_letter)` returns 4 teams for group A
- Test `load_knockout_matches()` returns 32 matches with stage_id >= 2
- Test database connection error handling
- Test query for matches by stage_id
Expected to FAIL until T017 is implemented
**Dependencies**: T002
**Parallel**: Yes [P]
**Status**: ✅ Complete
### T007: Create test for FIFA standings calculation
**File**: `backend/tests/test_fifa_engine.py`
**Description**: Create failing tests for group standings calculation:
- Test basic standings: 3 points for win, 1 for draw, 0 for loss
- Test goal difference calculation (goals_for - goals_against)
- Test sorting by points, then GD, then goals scored
- Test Fair Play Points calculation (yellow=-1, 2nd yellow=-3, red=-4)
- CRITICAL TEST: Tiebreaker with Fair Play Points (see plan.md lines 289-320)
  - Scenario: Mexico and Poland both have 4 points, +1 GD, 3 GF
  - Mexico: 1 yellow card = -1 fair play point
  - Poland: 1 red card = -4 fair play points
  - Expected: Mexico ranks higher (better fair play)
- Test deterministic fallback (hash-based tiebreaker) when all criteria equal
Expected to FAIL until T014 is implemented
**Dependencies**: T002
**Parallel**: Yes [P]
**Status**: ✅ Complete
### T008: Create test for third-place team ranking
**File**: `backend/tests/test_fifa_engine.py` (additional tests)
**Description**: Create failing tests for third-place qualification logic:
- Test ranking of 12 third-place teams across all groups
- Test top 8 selection criteria (points, GD, goals, fair play)
- Test edge case: multiple teams with identical records (use deterministic seed)
- Test that selected teams have correct rank=3 in their groups
- Verify returned list has exactly 8 teams sorted by qualification criteria
Expected to FAIL until T015 is implemented
**Dependencies**: T007
**Parallel**: No
**Status**: ✅ Complete
### T009: Create test for Round of 32 bracket resolution
**File**: `backend/tests/test_fifa_engine.py` (additional tests)
**Description**: Create failing tests for knockout matchup resolution:
- Test resolving "Winner A vs 3rd Place C/D/E" with actual qualified teams
- Test mapping table from SQLite (bracket_mappings or match labels)
- Test that all 32 Round of 32 matches get resolved (no TBD remaining)
- Test preservation of venue, kickoff time, match_number from SQLite
- Test handling of placeholder teams (is_placeholder=True)
Expected to FAIL until T016 is implemented
**Dependencies**: T008
**Parallel**: No
**Status**: ✅ Complete
### T010: Create test for API-Football data aggregation
**File**: `backend/tests/test_data_aggregator.py`
**Description**: Create failing tests for team statistics calculation:
- Test fetching last 5 fixtures from API-Football (mock response)
- Test xG average calculation from fixtures with complete data
- CRITICAL TEST: Handle missing xG data (see plan.md lines 356-380)
  - Scenario: 5 matches, only 3 have xG data
  - Expected: avg_xg = (2.4 + 0.8 + 2.2) / 3 = 1.8
  - Expected: data_completeness = 0.6 (3/5)
  - Expected: confidence = "medium"
- Test clean sheets count (matches with goals_against=0)
- Test form string generation ("W-W-D-L-W" pattern)
- Test fallback mode when NO xG data available (fallback_mode="traditional_form")
Expected to FAIL until T017 is implemented
**Dependencies**: T002
**Parallel**: Yes [P]
**Status**: ✅ Complete
### T011: Create test for API caching logic
**File**: `backend/tests/test_data_aggregator.py` (additional tests)
**Description**: Create failing tests for local cache management:
- CRITICAL TEST: Use cached data if less than 24 hours old (see plan.md lines 595-626)
- Test cache file naming: `cache/team_stats_{team_id}_{YYYY-MM-DD}.json`
- Test cache expiration: data older than 24 hours is refetched
- Test cache directory creation if missing
- Test JSON serialization/deserialization of TeamStatistics
- Test cache hit vs cache miss metrics
Expected to FAIL until T018 is implemented
**Dependencies**: T010
**Parallel**: No
**Status**: ✅ Complete
### T012: Create test for API rate limiting
**File**: `backend/tests/test_data_aggregator.py` (additional tests)
**Description**: Create failing tests for API-Football rate limiting:
- CRITICAL TEST: Ensure 0.5 second delay between consecutive requests (see plan.md lines 498-554)
- Test exponential backoff on 429 errors (wait 1s, 2s, 4s)
- Test retry logic on 5xx errors (max 3 retries)
- Test failure after max retries exceeded
- Use mock time.sleep() to avoid slow tests
Expected to FAIL until T019 is implemented
**Dependencies**: T010
**Parallel**: Yes [P]
**Status**: ✅ Complete
### T013: Create test for Gemini AI prediction generation
**File**: `backend/tests/test_ai_agent.py`
**Description**: Create failing tests for AI prediction service:
- Test building prompts with aggregated team statistics (not just team names)
- Test calling Gemini API with structured JSON schema
- Test parsing markdown-wrapped JSON responses (strip ```json blocks)
- Test validation of prediction schema (winner, probability, score, reasoning)
- CRITICAL TEST: Retry strategy (see plan.md lines 634-676)
  - Max 1 retry on failure (2 total attempts)
  - After 2 failures, use rule-based fallback
- Test rule-based prediction fallback using xG differential
Expected to FAIL until T020 is implemented
**Dependencies**: T002
**Parallel**: Yes [P]
**Status**: ✅ Complete
### T014: Create test for Firestore publishing
**File**: `backend/tests/test_firestore_publisher.py`
**Description**: Create failing tests for Firestore write operations:
- Test assembling TournamentSnapshot from groups + bracket + AI summary
- Test publishing to predictions/latest document
- Test timestamp inclusion (updated_at field)
- Test schema validation before publishing
- CRITICAL TEST: History diff check (see plan.md lines 678-724)
  - Test skipping write if prediction unchanged (winner + reasoning identical)
  - Test writing new history entry if prediction differs
  - Test sub-collection path: matches/{match_id}/history/{timestamp}
Expected to FAIL until T021 is implemented
**Dependencies**: T002
**Parallel**: Yes [P]
**Status**: ✅ Complete
### T015: Create frontend test for GroupCard component
**File**: `frontend/__tests__/GroupCard.test.tsx`
**Description**: Create failing tests for group standings display:
- Test displaying group standings sorted by rank
- Test team flag emoji rendering
- Test points, GD, goals columns display correctly
- Test highlighting top 2 teams (qualifiers) with visual indicator
- Test showing 3rd place team with different style (potential qualifier)
- Test responsive layout (mobile vs desktop)
Expected to FAIL until T027 is implemented
**Dependencies**: T004
**Parallel**: Yes [P]
**Status**: ✅ Complete
### T016: Create frontend test for Firestore data fetching
**File**: `frontend/__tests__/lib/firestore.test.ts`
**Description**: Create failing tests for Firestore client:
- Test fetching predictions/latest document
- Test parsing TournamentSnapshot structure
- Test error handling when document doesn't exist
- Test detecting stale data (updated_at older than 2 hours)
- Test triggering backend refresh when data is stale
Expected to FAIL until T028 is implemented
**Dependencies**: T004
**Parallel**: Yes [P]
**Status**: ✅ Complete
---
## Phase 3: Core Implementation
### T017: Implement db_manager.py for SQLite operations
**File**: `backend/src/db_manager.py`
**Description**: Implement database interface to pass T006 tests:
- Create DBManager class with connection to worldcup2026.db
- Implement `load_all_teams()` returning List[Team] from teams table
- Implement `load_all_matches()` returning List[Match] with joins to teams/cities
- Implement `load_group_teams(group_letter)` with WHERE filter
- Implement `load_knockout_matches()` with stage_id >= 2 filter
- Add connection pooling and error handling
- Use context manager for connection lifecycle
Run pytest to verify T006 passes
**Dependencies**: T006
**Parallel**: No
**Status**: ✅ Complete
### T018: Implement FIFA standings calculation in fifa_engine.py
**File**: `backend/src/fifa_engine.py`
**Description**: Implement group standings logic to pass T007 tests:
- Create FifaEngine class with `calculate_standings(results)` method
- Calculate points: won*3 + draw*1
- Calculate goal_difference: goals_for - goals_against
- Implement Fair Play Points from cards data (yellow=-1, 2nd yellow=-3, red=-4)
- **CRITICAL: Implement resolve_tie_breaker with deterministic final fallback**:
  - Tiebreaker sequence: Points > GD > Goals > H2H > Fair Play
  - **For the final draw of lots, implement a deterministic random seed based on team names (e.g., hash(TeamA + TeamB))**
  - **Do NOT use standard random functions (random.choice(), random.random()) that change on every run**
  - This prevents the "Flickering Website" problem where rankings change randomly on each backend run
- Implement tiebreaker sorting (see plan.md lines 469-492):
  1. Points (descending)
  2. Goal Difference (descending)
  3. Goals Scored (descending)
  4. Fair Play Points (ascending - less negative is better)
  5. Deterministic seed: hash(team_name) for final fallback
- Return Dict[str, List[GroupStanding]] with groups A-L
Run pytest to verify T007 passes
**Dependencies**: T007, T017
**Parallel**: No
**Status**: ✅ Complete
### T019: Implement third-place team ranking in fifa_engine.py
**File**: `backend/src/fifa_engine.py` (additional method)
**Description**: Implement third-place qualification logic to pass T008 tests:
- Add method `rank_third_place_teams(standings)` to FifaEngine
- Extract all 3rd-place teams from 12 groups
- Sort by same criteria as group standings (points, GD, goals, fair play, hash)
- Select top 8 teams
- Return List[GroupStanding] with selected third-place qualifiers
Run pytest to verify T008 passes
**Dependencies**: T008, T018
**Parallel**: No
**Status**: ✅ Complete
### T020: Implement Round of 32 bracket resolution in fifa_engine.py
**File**: `backend/src/fifa_engine.py` (additional method)
**Description**: Implement knockout matchup resolution to pass T009 tests:
- Add method `resolve_knockout_bracket(standings, third_place_teams, knockout_matches)`
- Load bracket mapping table from SQLite (match labels like "Winner A vs 3rd Place C/D/E")
- Replace placeholders with actual qualified team names:
  - "Winner A" → standings['A'][0]
  - "3rd Place C/D/E" → first team in third_place list from groups C, D, or E
- Update match records with resolved home_team_id, away_team_id
- Preserve venue, kickoff_at, match_number from SQLite
- Return List[BracketMatch] with resolved matchups
Run pytest to verify T009 passes
**Dependencies**: T009, T019
**Parallel**: No
**Status**: ✅ Complete
### T021: Implement team statistics aggregation in data_aggregator.py
**File**: `backend/src/data_aggregator.py`
**Description**: Implement API-Football client to pass T010 tests:
- Create DataAggregator class with `compute_metrics(fixtures)` method
- Calculate average xG from last 5 matches (exclude matches with missing xG)
- Handle missing xG gracefully (see plan.md lines 562-589):
  - If some matches missing xG: calculate avg from available data, set data_completeness
  - If ALL matches missing xG: set avg_xg=None, fallback_mode="traditional_form", confidence="low"
- Calculate clean_sheets count (matches with goals_against=0)
- Generate form_string ("W-W-D-L-W" for last 5 matches, most recent first)
- Return TeamStatistics with data_completeness (0.0-1.0) and confidence ("high", "medium", "low")
Run pytest to verify T010 passes
**Dependencies**: T010
**Parallel**: No
**Status**: ✅ Complete 
### T022: Implement local caching in data_aggregator.py
**File**: `backend/src/data_aggregator.py` (additional methods)
**Description**: Implement cache management to pass T011 tests:
- Add method `get_cached_stats(team_id)` (see plan.md lines 595-626)
- Check cache file: `cache/team_stats_{team_id}_{YYYY-MM-DD}.json`
- Load from cache if file age < 24 hours
- Return None if cache miss or expired
- Add method `save_to_cache(team_id, stats)`
- Create cache/ directory if missing
- Serialize TeamStatistics to JSON with proper datetime formatting
Run pytest to verify T011 passes
**Dependencies**: T011, T021
**Parallel**: No
**Status**: ✅ Complete 
### T023: Implement API rate limiting in data_aggregator.py
**File**: `backend/src/data_aggregator.py` (decorators)
**Description**: Implement rate limiting to pass T012 tests:
- Create `@rate_limit(delay=0.5)` decorator (see plan.md lines 498-554)
- Insert time.sleep(0.5) between consecutive API requests
- Create `@retry_with_backoff(max_retries=3)` decorator
- Implement exponential backoff: wait 1s, 2s, 4s on 429/5xx errors
- Raise exception after max retries exceeded
- Apply decorators to `fetch_team_stats(team_id)` method
Run pytest to verify T012 passes
**Dependencies**: T012, T021
**Parallel**: No
**Status**: ✅ Complete 
### T024: Implement Gemini AI prediction service in ai_agent.py
**File**: `backend/src/ai_agent.py`
**Description**: Implement AI prediction generation to pass T013 tests:
- Create AIAgent class with `generate_prediction(matchup)` method
- Build prompts with aggregated stats (avg_xg, clean_sheets, form_string) not just team names
- **CRITICAL: Initialize Gemini Client with JSON Mode enforcement**:
  - Configure the model generation config to enforce `response_mime_type: 'application/json'`
  - This is critical for parsing stability and prevents backend crashes from malformed responses
  - Call Gemini 3.0 Pro with structured JSON schema (responseMimeType="application/json")
- Parse markdown-wrapped responses (strip ```json blocks using regex as fallback)
- Validate prediction schema (winner, win_probability, predicted_home_score, predicted_away_score, reasoning)
- Implement retry strategy (see plan.md lines 634-676):
  - Max 1 retry on failure (2 total attempts)
  - Exponential backoff: wait 1s after first failure
  - After 2 failures, call rule_based_prediction() fallback
- Implement `rule_based_prediction(matchup)` using xG differential for probability
Run pytest to verify T013 passes
**Dependencies**: T013
**Parallel**: No
**Status**: ✅ Complete 
### T025: Implement Firestore publisher in firestore_publisher.py
**File**: `backend/src/firestore_publisher.py`
**Description**: Implement Firestore write operations to pass T014 tests:
- Create FirestorePublisher class with `publish_snapshot(snapshot)` method
- Assemble TournamentSnapshot from groups, bracket, AI summary
- Validate schema before publishing
- Publish to predictions/latest document with timestamp
- **CRITICAL: Implement save_prediction_history with Sub-collection + Diff logic**:
  - Check if a document exists in the `/matches/{match_id}/history` sub-collection
  - **Diff Check**: Only write a new document if the winner or reasoning has changed significantly from the latest entry
  - **Cold Start**: Handle the case where the collection is empty (save immediately on first run)
  - This prevents "Document Explosion" (1MB Firestore limit) by avoiding duplicate history entries
- Implement `should_save_prediction_history(match_id, prediction)` (see plan.md lines 686-724)
- Check if prediction differs from latest history entry (winner OR reasoning changed)
- If changed: save to matches/{match_id}/history/{timestamp} sub-collection
- If identical: skip write (cost optimization)
- Return success/failure status
Run pytest to verify T014 passes
**Dependencies**: T014
**Parallel**: No
**Status**: ✅ Complete 
### T026: Implement FastAPI main endpoint in main.py
**File**: `backend/src/main.py`
**Description**: Create FastAPI application with prediction update endpoint:
- Create FastAPI app with CORS middleware
- Implement POST `/api/update-predictions` endpoint (see plan.md lines 165-195):
  - Load tournament structure from db_manager
  - Calculate standings using fifa_engine
  - Fetch team stats using data_aggregator (with caching)
  - Generate predictions using ai_agent
  - Resolve knockout bracket
  - Publish snapshot to Firestore using firestore_publisher
  - Return {status, updated_at, predictions_generated, errors}
- Implement GET `/health` endpoint (see plan.md lines 197-209):
  - Check database connection
  - Check Firestore connection
  - Report cache size
  - Return {status, database, firestore, cache_size}
- Add error handling with proper HTTP status codes (500 for failures)
**Dependencies**: T017, T018, T019, T020, T021, T022, T023, T024, T025
**Parallel**: No
**Status**: ✅ Complete 
### T027: Port types.ts to frontend
**File**: `frontend/lib/types.ts`
**Description**: Create TypeScript type definitions for frontend:
- Port POC types from `poc/types.ts` (see research.md lines 209-247)
- Define TeamStats interface (id, name, flag, played, won, draw, lost, goalsFor, goalsAgainst, points, rank)
- Define Match interface (id, matchNumber, homeTeamId, awayTeamId, cityId, stageId, kickoff, label)
- Define MatchPrediction interface (predictedWinner, winProbability, reasoning, predictedHomeScore, predictedAwayScore, confidence)
- Define Group interface (letter, teams: TeamStats[])
- Define TournamentSnapshot interface (updatedAt, groups, bracket, aiSummary, favorites, darkHorses)
- Add JSDoc comments for all interfaces
**Dependencies**: T003
**Parallel**: Yes [P]
**Status**: ✅ Complete 
### T028: Implement Firestore client in frontend
**File**: `frontend/lib/firestore.ts`
**Description**: Create Firestore data fetching service to pass T016 tests:
- Initialize Firebase app with project config
- Create `fetchLatestPredictions()` async function
- Fetch predictions/latest document from Firestore
- Parse and validate TournamentSnapshot structure
- Detect stale data: compare updated_at to current time (threshold: 2 hours)
- If stale: trigger backend refresh by calling POST /api/update-predictions
- Return TournamentSnapshot | null
- Add error handling for network failures
Run vitest to verify T016 passes
**Dependencies**: T016, T027
**Parallel**: No
**Status**: ✅ Complete 
### T029: Implement GroupCard component
**File**: `frontend/components/GroupCard.tsx`
**Description**: Create group standings table component to pass T015 tests:
- Port POC component logic from `poc/components/GroupCard.tsx` (see research.md lines 161-174)
- Accept props: group (Group interface), predictions (optional)
- Sort teams by rank from AI predictions, fallback to points
- Display table columns: Rank, Team (flag + name), P, W, D, L, GF, GA, GD, Pts
- Highlight top 2 teams (qualifiers) with green background
- Style 3rd place team with yellow background (potential qualifier)
- Use Tailwind CSS for responsive design
- Add mobile-friendly layout (stack columns on small screens)
Run vitest to verify T015 passes
**Dependencies**: T015, T027
**Parallel**: Yes [P]
**Status**: ✅ Complete 
### T030: Implement MatchCard component
**File**: `frontend/components/MatchCard.tsx`
**Description**: Create match prediction card component:
- Accept props: match (Match interface), prediction (MatchPrediction interface)
- Display match info: teams (flag + name), venue, kickoff time
- Show AI prediction: predicted winner, win probability (percentage bar)
- Display predicted score (e.g., "2-1")
- Show reasoning text (truncated with "Read more" expansion)
- Indicate confidence level with color coding (high=green, medium=yellow, low=red)
- Handle TBD matchups: display placeholder label (e.g., "Winner A vs 3rd Place C/D/E")
- Use Tailwind CSS for card design
**Dependencies**: T027
**Parallel**: Yes [P]
**Status**: ✅ Complete
### T031: Implement BracketView component
**File**: `frontend/components/BracketView.tsx`
**Description**: Create knockout bracket visualization component:
- Accept props: bracket (BracketMatch[])
- Group matches by stage (Round of 32, Round of 16, Quarter-finals, Semi-finals, Final)
- Display bracket tree with connecting lines (use SVG or CSS borders)
- Show match cards for each fixture
- Display progression from Round of 32 → Final
- Handle TBD matchups gracefully (show placeholder labels)
- Make responsive for mobile (horizontal scroll or vertical stack)
- Use Tailwind CSS for layout
**Dependencies**: T027
**Parallel**: Yes [P]
**Status**: ✅ Complete
### T032: Create app home page with tabs
**File**: `frontend/app/page.tsx`
**Description**: Implement main landing page:
- Port POC tab structure from `poc/App.tsx` (see research.md lines 78-85)
- Create tab navigation: Groups | Matches | Bracket
- Fetch predictions on page load using fetchLatestPredictions()
- Display last updated timestamp from TournamentSnapshot
- Show loading state while fetching data
- Show error state if Firestore fetch fails
- Pass data to child components based on active tab
- Add "Refresh Predictions" button to manually trigger backend update
**Dependencies**: T028
**Parallel**: No
**Status**: ✅ Complete 
### T033: Create groups page
**File**: `frontend/app/groups/page.tsx`
**Description**: Implement group stage view:
- Fetch predictions using fetchLatestPredictions()
- Display all 12 groups using GroupCard component
- Arrange groups in responsive grid (3 columns desktop, 1 column mobile)
- Show AI-predicted top 8 third-place qualifiers in separate section
- Add filter buttons to highlight specific groups
- Display loading skeleton while fetching data
**Dependencies**: T028, T029
**Parallel**: Yes [P]
**Status**: 
### T034: Create matches page
**File**: `frontend/app/matches/page.tsx`
**Description**: Implement match schedule view:
- Fetch predictions using fetchLatestPredictions()
- Display all 104 matches using MatchCard component
- Add stage filter dropdown (All, Group Stage, Round of 32, Round of 16, etc.)
- Add date filter to show matches by kickoff date
- Implement search by team name
- Sort matches by kickoff time (ascending)
- Use virtualized list for performance (react-window or similar)
**Dependencies**: T028, T030
**Parallel**: Yes [P]
**Status**: 
### T035: Create bracket page
**File**: `frontend/app/bracket/page.tsx`
**Description**: Implement knockout bracket view:
- Fetch predictions using fetchLatestPredictions()
- Display knockout bracket using BracketView component
- Show tournament progression from Round of 32 to Final
- Highlight predicted winner path (use bold or colored lines)
- Display AI summary and favorites list below bracket
- Show dark horses section
- Add zoom controls for mobile viewing
**Dependencies**: T028, T031
**Parallel**: Yes [P]
**Status**: 
---
## Phase 4: Integration & Polish
### T036: Create end-to-end backend integration test
**File**: `backend/tests/test_integration.py`
**Description**: Create integration test for full backend pipeline:
- Mock API-Football responses (use fixtures/mock_api_football.json)
- Mock Gemini AI responses (use fixtures/mock_gemini_response.json)
- Test complete flow: SQLite → FIFA engine → Data aggregator → AI agent → Firestore publisher
- Verify predictions/latest document structure matches TournamentSnapshot schema
- Verify history sub-collection skips identical predictions (diff check)
- Test error handling when API-Football returns 429
- Test fallback to rule-based predictions when Gemini fails
Run pytest to verify integration test passes
**Dependencies**: T026
**Parallel**: No
**Status**: 
### T037: Create frontend integration test
**File**: `frontend/__tests__/integration/predictions-flow.test.tsx`
**Description**: Create integration test for Firestore → UI rendering:
- Mock Firestore responses with sample TournamentSnapshot
- Test fetchLatestPredictions() returns correct data
- Test GroupCard renders with fetched data
- Test MatchCard displays predictions correctly
- Test BracketView shows resolved matchups
- Test stale data detection triggers backend refresh
- Test error handling when Firestore fetch fails
Run vitest to verify integration test passes
**Dependencies**: T032, T033, T034, T035
**Parallel**: No
**Status**: 
### T038: Add comprehensive error handling to backend
**File**: `backend/src/main.py`, `backend/src/data_aggregator.py`, `backend/src/ai_agent.py`
**Description**: Improve error handling and logging:
- Add structured logging with Python logging module (INFO, WARNING, ERROR levels)
- Log all API calls (API-Football, Gemini) with request/response times
- Add try-except blocks around external API calls
- Return detailed error messages in FastAPI responses
- Log cache hits vs cache misses for monitoring
- Add request ID tracking for debugging
- Create custom exception classes (APIRateLimitError, GeminiFailureError, etc.)
**Dependencies**: T026
**Parallel**: No
**Status**: 
### T039: Add loading and error states to frontend
**File**: `frontend/components/LoadingSpinner.tsx`, `frontend/components/ErrorBoundary.tsx`, `frontend/app/page.tsx`
**Description**: Implement proper loading and error UI:
- Create LoadingSpinner component with skeleton placeholders
- Create ErrorBoundary component to catch React errors
- Add loading state to all data fetching operations
- Display error messages when Firestore fetch fails
- Add retry button for failed requests
- Show connection status indicator in header
- Add offline mode detection and messaging
**Dependencies**: T032
**Parallel**: No
**Status**: 
### T040: Optimize Firestore queries and caching
**File**: `frontend/lib/firestore.ts`
**Description**: Add client-side caching and optimization:
- Implement client-side cache with 5-minute TTL
- Use SWR (stale-while-revalidate) pattern for data fetching
- Add Firestore real-time listeners for predictions/latest document
- Implement optimistic UI updates when triggering backend refresh
- Add network-first caching strategy (check Firestore, fall back to cache)
- Prefetch predictions on app load
**Dependencies**: T028
**Parallel**: No
**Status**: 
---
## Phase 5: Deployment & Infrastructure
### T041: Create Dockerfile for backend
**File**: `backend/Dockerfile`
**Description**: Dockerize Python backend for Cloud Run deployment:
- Use Python 3.11-slim base image
- Copy requirements.txt and install dependencies
- Copy src/ and worldcup2026.db to container
- Set environment variables for production
- Expose port 8080 (Cloud Run default)
- Set CMD to run uvicorn with main:app
- Optimize for cold start performance (minimize image size)
**Dependencies**: T026
**Parallel**: Yes [P]
**Status**: 
### T042: Create Cloud Run deployment configuration
**File**: `backend/cloudbuild.yaml`, `backend/service.yaml`
**Description**: Set up Cloud Run service configuration:
- Create cloudbuild.yaml for automated builds from Git
- Create service.yaml with Cloud Run service spec:
  - Memory: 512MB (sufficient for Python app)
  - CPU: 1 (minimum)
  - Concurrency: 10 (allow multiple requests)
  - Min instances: 0 (scale to zero for cost savings)
  - Max instances: 5 (prevent runaway costs)
  - Timeout: 300s (5 minutes for AI calls)
- Configure service account with Firestore write permissions
- Add secret management for API keys (GEMINI_API_KEY, API_FOOTBALL_KEY)
**Dependencies**: T041
**Parallel**: No
**Status**: 
### T043: Set up Cloud Scheduler for periodic updates
**File**: `backend/scheduler.yaml`
**Description**: Configure Cloud Scheduler to trigger backend updates:
- Create Cloud Scheduler job to call POST /api/update-predictions
- Schedule: Daily at 10:00 AM UTC (during tournament active period)
- HTTP target: Cloud Run service URL
- Authentication: Service account with invoker role
- Retry configuration: 3 retries with exponential backoff
- Add monitoring alerts for failed runs
**Dependencies**: T042
**Parallel**: No
**Status**: 
### T044: Configure Firebase Hosting for frontend
**File**: `frontend/firebase.json`, `frontend/.firebaserc`
**Description**: Set up Firebase Hosting deployment:
- Run `firebase init hosting` in frontend/ directory
- Configure firebase.json:
  - Public directory: out/ (Next.js static export)
  - Rewrites for SPA routing
  - Headers for caching static assets (1 year for JS/CSS, no-cache for HTML)
- Create .firebaserc with project ID
- Add deployment script to package.json
- Configure custom domain (optional, document in README)
**Dependencies**: T003
**Parallel**: Yes [P]
**Status**: 
### T045: Build Next.js for static export
**File**: `frontend/next.config.js`
**Description**: Configure Next.js for Firebase Hosting static export:
- Add `output: 'export'` to next.config.js
- Configure image optimization for static export (unoptimized: true or custom loader)
- Disable server-side features (API routes, ISR)
- Add build script: `next build` (outputs to out/ directory)
- Test build locally: `npx serve out/`
- Verify all routes work in static mode
**Dependencies**: T044
**Parallel**: No
**Status**: 
### T046: Set up GitHub Actions for backend CI/CD
**File**: `.github/workflows/backend-test.yml`, `.github/workflows/backend-deploy.yml`
**Description**: Create CI/CD pipeline for backend:
- Create backend-test.yml workflow:
  - Trigger on push to backend/ directory
  - Set up Python 3.11
  - Install dependencies from requirements-dev.txt
  - Run pytest with coverage reporting
  - Fail if coverage < 80%
- Create backend-deploy.yml workflow:
  - Trigger on push to main branch (backend/ changes)
  - Build Docker image
  - Push to Google Container Registry
  - Deploy to Cloud Run
  - Run smoke test (call /health endpoint)
**Dependencies**: T042
**Parallel**: Yes [P]
**Status**: 
### T047: Set up GitHub Actions for frontend CI/CD
**File**: `.github/workflows/frontend-test.yml`, `.github/workflows/frontend-deploy.yml`
**Description**: Create CI/CD pipeline for frontend:
- Create frontend-test.yml workflow:
  - Trigger on push to frontend/ directory
  - Set up Node.js 20+
  - Install dependencies (npm ci)
  - Run vitest with coverage reporting
  - Run lint checks (next lint)
- Create frontend-deploy.yml workflow:
  - Trigger on push to main branch (frontend/ changes)
  - Build Next.js (npm run build)
  - Deploy to Firebase Hosting (firebase deploy)
  - Run smoke test (check homepage loads)
**Dependencies**: T045
**Parallel**: Yes [P]
**Status**: 
---
## Phase 6: Documentation & Validation
### T048: Create backend README
**File**: `backend/README.md`
**Description**: Document backend setup and deployment:
- Add project overview and architecture diagram
- Document environment variables (API_FOOTBALL_KEY, GEMINI_API_KEY, etc.)
- Add local development setup instructions:
  - Create virtual environment (python -m venv venv)
  - Install dependencies (pip install -r requirements-dev.txt)
  - Run tests (pytest)
  - Run locally (uvicorn src.main:app --reload)
- Document API endpoints (/api/update-predictions, /health)
- Add deployment instructions (Docker build, Cloud Run deploy)
- Include troubleshooting section (common errors, cache clearing)
**Dependencies**: T026
**Parallel**: Yes [P]
**Status**: 
### T049: Create frontend README
**File**: `frontend/README.md`
**Description**: Document frontend setup and deployment:
- Add project overview with screenshots (add later)
- Document environment variables (NEXT_PUBLIC_FIREBASE_PROJECT_ID, etc.)
- Add local development setup instructions:
  - Install dependencies (npm install)
  - Run dev server (npm run dev)
  - Run tests (npm test)
- Document component structure and data flow
- Add Firebase Hosting deployment instructions
- Include Tailwind CSS configuration notes
**Dependencies**: T035
**Parallel**: Yes [P]
**Status**: 
### T050: Create root README with architecture overview
**File**: `README.md`
**Description**: Create comprehensive project documentation:
- Add project title and description (World Cup 2026 AI Prediction Platform)
- Include architecture diagram (backend + frontend + data flow)
- Document monorepo structure (frontend/, backend/, poc/, specs/)
- Link to backend and frontend READMEs
- Add "Logic in Python, Magic in AI" philosophy explanation
- Document deployment status and URLs (production site, API endpoint)
- Add contributing guidelines (TDD required, Bifrost workflow)
- Include license information
**Dependencies**: T048, T049
**Parallel**: No
**Status**: 
### T051: Update RULES.md constitution (if missing)
**File**: `RULES.md`
**Description**: Create or update project constitution:
- Add code style guidelines (Python: Black formatter, TypeScript: Prettier)
- Document TDD requirements (tests before implementation, 80% coverage minimum)
- Add commit message conventions (use Conventional Commits)
- Document technology stack (Python 3.11+, Next.js 15+, FastAPI, Firebase)
- Add API-Football and Gemini AI usage guidelines
- Document Fair Play Points tiebreaker logic (reference for future developers)
- Include cost optimization guidelines (cache aggressively, 1 retry max for AI)
**Dependencies**: None
**Parallel**: Yes [P]
**Status**: 
### T052: Create API documentation
**File**: `backend/docs/api.md`
**Description**: Document backend API contracts:
- Document POST /api/update-predictions endpoint (see plan.md lines 165-195):
  - Request schema (empty body)
  - Response schema (status, updated_at, predictions_generated, errors)
  - Error codes and meanings (500 for API failures)
- Document GET /health endpoint (see plan.md lines 197-209):
  - Response schema (status, database, firestore, cache_size)
- Add example requests with curl commands
- Document authentication (Cloud Run IAM for production, API key for dev)
- Include rate limiting information (0.5s delay, exponential backoff)
**Dependencies**: T026
**Parallel**: Yes [P]
**Status**: 
### T053: Create data model documentation
**File**: `backend/docs/data-model.md`
**Description**: Document complete data model:
- Copy from `specs/vmkula-website/data-model.md` (see data-model.md)
- Add SQLite schema diagrams (teams, matches, host_cities, tournament_stages)
- Document Firestore schema (predictions/latest, matches/{id}/history)
- Include entity relationship diagrams
- Document validation rules (Fair Play Points calculation, tiebreaker sequence)
- Add example data for each entity
**Dependencies**: None
**Parallel**: Yes [P]
**Status**: 
### T054: Validate all tests pass
**File**: N/A (validation task)
**Description**: Run complete test suite and verify 100% pass rate:
- Run backend tests: `cd backend && pytest --cov=src --cov-report=html`
- Verify coverage >= 80% (spec requirement)
- Run frontend tests: `cd frontend && npm test -- --coverage`
- Verify all integration tests pass (T036, T037)
- Fix any failing tests discovered
- Generate coverage reports (HTML for review)
- Document any known test limitations
**Dependencies**: Phase 3 complete
**Parallel**: No
**Status**: 
### T055: Validate Firestore schema matches spec
**File**: N/A (validation task)
**Description**: Verify Firestore document structure:
- Trigger backend update: POST /api/update-predictions
- Fetch predictions/latest document
- Validate schema matches TournamentSnapshot (see data-model.md lines 242-297):
  - updated_at (ISO8601 string)
  - groups (Dict[str, List[GroupStanding]])
  - bracket (List[BracketMatch])
  - ai_summary (string)
  - favorites (List[str])
  - dark_horses (List[str])
- Check document size < 1MB (Firestore limit)
- Verify history sub-collection works (matches/{id}/history/{timestamp})
- Test diff check: trigger update twice, verify no duplicate history entries
**Dependencies**: T026, T036
**Parallel**: No
**Status**: 
### T056: Validate Fair Play Points tiebreaker
**File**: N/A (validation task)
**Description**: Test FIFA tiebreaker logic with real data:
- Create test scenario: Two teams with equal points, GD, goals
- Add card data: Team A (1 yellow), Team B (1 red)
- Run fifa_engine.calculate_standings()
- Verify Team A ranks higher (fair_play_points: -1 vs -4)
- Test deterministic fallback: Teams with identical stats always rank same way
- Verify no random flickering between runs
- Document tiebreaker sequence in test output
**Dependencies**: T018
**Parallel**: No
**Status**: 
### T057: Validate caching reduces API calls
**File**: N/A (validation task)
**Description**: Test caching effectiveness:
- Clear cache directory (delete backend/cache/*)
- Trigger backend update (first run - should fetch from API-Football)
- Check cache files created (cache/team_stats_{team_id}_{date}.json)
- Trigger backend update again immediately (should use cache)
- Verify API-Football was NOT called (check logs)
- Wait 24+ hours (or mock time), trigger update (should refetch)
- Verify API-Football was called (cache expired)
- Count total API calls: should be ~48 teams on first run, 0 on second run
**Dependencies**: T022, T026
**Parallel**: No
**Status**: 
### T058: Validate Gemini AI retry and fallback
**File**: N/A (validation task)
**Description**: Test AI failure handling:
- Mock Gemini API to return error on first call, success on retry
- Trigger prediction generation
- Verify retry occurred (check logs for "Retry attempt 1")
- Verify prediction generated successfully after retry
- Mock Gemini API to fail twice
- Trigger prediction generation
- Verify fallback to rule_based_prediction() (check logs for "Using rule-based fallback")
- Verify prediction has confidence="low" and reasoning mentions "Statistical probability"
**Dependencies**: T024, T026
**Parallel**: No
**Status**: 
### T059: Performance test: Full prediction generation time
**File**: N/A (validation task)
**Description**: Measure end-to-end performance:
- Clear cache to force full API fetches
- Trigger POST /api/update-predictions
- Measure total execution time (should complete in < 5 minutes per Cloud Run timeout)
- Break down timing:
  - SQLite queries: < 1 second
  - API-Football fetches (48 teams with 0.5s delay): ~24 seconds
  - FIFA engine calculations: < 5 seconds
  - Gemini AI predictions (104 matches): ~2-3 minutes
  - Firestore writes: < 5 seconds
- Identify bottlenecks (likely Gemini API calls)
- Verify no timeout errors
**Dependencies**: T026
**Parallel**: No
**Status**: 
### T060: Accessibility audit for frontend
**File**: N/A (validation task)
**Description**: Verify WCAG 2.1 AA compliance:
- Run Lighthouse accessibility audit on all pages (groups, matches, bracket)
- Test keyboard navigation (tab through all interactive elements)
- Test screen reader compatibility (VoiceOver on Mac, NVDA on Windows)
- Verify color contrast ratios (text vs background >= 4.5:1)
- Add ARIA labels to interactive elements (buttons, links)
- Test focus indicators visible on all focusable elements
- Fix any accessibility issues found
- Target score: 95+ on Lighthouse accessibility
**Dependencies**: T033, T034, T035
**Parallel**: No
**Status**: 
### T061: Mobile responsiveness validation
**File**: N/A (validation task)
**Description**: Test mobile user experience:
- Test on real devices (iPhone, Android) or use Chrome DevTools device emulation
- Verify layouts work on screen sizes: 320px, 375px, 768px, 1024px, 1440px
- Test touch interactions (tap targets >= 44x44px)
- Verify text is readable without zoom (font-size >= 16px)
- Test horizontal scroll behavior on bracket view
- Verify images and flags render correctly on mobile
- Test page load performance on 3G connection (Lighthouse)
- Fix any layout issues or performance problems
**Dependencies**: T033, T034, T035
**Parallel**: No
**Status**: 
### T062: Create deployment checklist
**File**: `DEPLOYMENT.md`
**Description**: Document production deployment steps:
- Add pre-deployment checklist:
  - [ ] All tests passing (backend + frontend)
  - [ ] Environment variables configured in Cloud Run and Firebase
  - [ ] Firestore indexes created (if needed)
  - [ ] Service accounts have correct permissions
  - [ ] API keys have sufficient quotas (API-Football, Gemini)
- Add deployment steps:
  1. Deploy backend to Cloud Run (via GitHub Actions or manual gcloud deploy)
  2. Test backend /health endpoint
  3. Deploy frontend to Firebase Hosting (via GitHub Actions or firebase deploy)
  4. Test frontend loads predictions
  5. Set up Cloud Scheduler job
  6. Monitor first scheduled run
- Add rollback procedure (redeploy previous version)
- Add monitoring setup (Cloud Logging, Firebase Analytics)
**Dependencies**: T046, T047
**Parallel**: No
**Status**: 
---
## Validation Checklist
- [ ] All user stories from spec.md have corresponding implementation tasks
  - ✓ Group stage tables with FIFA rules (T018, T033)
  - ✓ Match predictions with reasoning (T024, T034)
  - ✓ Knockout bracket with resolved matchups (T020, T035)
  - ✓ AI predictions based on aggregated stats (T021, T024)
  - ✓ Firestore data retrieval (T028, T032)
- [ ] All backend modules from plan.md have implementation tasks
  - ✓ db_manager.py (T017)
  - ✓ fifa_engine.py (T018, T019, T020)
  - ✓ data_aggregator.py (T021, T022, T023)
  - ✓ ai_agent.py (T024)
  - ✓ firestore_publisher.py (T025)
  - ✓ main.py (T026)
- [ ] All frontend components from plan.md have implementation tasks
  - ✓ GroupCard (T029)
  - ✓ MatchCard (T030)
  - ✓ BracketView (T031)
  - ✓ Firestore client (T028)
  - ✓ App pages (T032, T033, T034, T035)
- [ ] All critical tests from plan.md have test creation tasks
  - ✓ Fair Play Points tiebreaker (T007)
  - ✓ Missing xG data handling (T010)
  - ✓ API rate limiting (T012)
  - ✓ Gemini retry + fallback (T013)
  - ✓ Firestore history diff check (T014)
- [ ] Test tasks are ordered before implementation tasks (TDD enforced)
  - ✓ Phase 2 (Tests) completed before Phase 3 (Implementation)
  - ✓ Each implementation task depends on corresponding test task
- [ ] All tasks have specific file paths and clear descriptions
  - ✓ Every task specifies File field with exact paths
  - ✓ Descriptions include implementation details and expected outcomes
- [ ] Parallel tasks are correctly identified (independent files, no dependencies)
  - ✓ Setup tasks (T001, T003, T005) are parallel
  - ✓ Test creation tasks (T006-T016) are mostly parallel
  - ✓ Implementation tasks are sequential (depend on tests)
- [ ] Dependencies are explicitly noted for sequential tasks
  - ✓ All implementation tasks depend on their test tasks
  - ✓ Integration tasks depend on Phase 3 completion
- [ ] Deployment tasks cover both backend and frontend
  - ✓ Backend: Dockerfile (T041), Cloud Run (T042), Scheduler (T043)
  - ✓ Frontend: Firebase Hosting (T044), Static export (T045)
  - ✓ CI/CD pipelines (T046, T047)
- [ ] Documentation tasks ensure project maintainability
  - ✓ READMEs (T048, T049, T050)
  - ✓ API docs (T052)
  - ✓ Data model docs (T053)
  - ✓ RULES.md constitution (T051)
---
## Summary
**Total Tasks**: 62
**Estimated Effort**: ~85-95 hours (2-2.5 weeks for 1 developer)
**Phase Breakdown**:
- **Phase 1 (Setup)**: 5 tasks, ~4 hours
- **Phase 2 (Tests)**: 11 tasks, ~12 hours
- **Phase 3 (Implementation)**: 19 tasks, ~40 hours
- **Phase 4 (Integration)**: 5 tasks, ~8 hours
- **Phase 5 (Deployment)**: 7 tasks, ~10 hours
- **Phase 6 (Documentation)**: 15 tasks, ~12 hours
**Parallel Execution Opportunities**:
- **Phase 1**: Tasks T001, T003, T005 can run in parallel (different projects: Python vs Next.js vs config)
- **Phase 2**: Tasks T006, T007, T010, T012, T013, T014, T015, T016 can run in parallel (independent test files)
- **Phase 3**: Tasks T027, T029, T030, T031, T033, T034, T035 can run in parallel (independent components)
- **Phase 5**: Tasks T041, T044, T046, T047 can run in parallel (different deployment targets)
- **Phase 6**: Tasks T048, T049, T051, T052, T053 can run in parallel (independent documentation files)
**Critical Path** (must be sequential):
T002 → T006 → T017 → T007 → T018 → T008 → T019 → T009 → T020 → T026 → T036 → T054
**Implementation Strategy**:
1. **Start with Setup (Phase 1)**: Run T001, T003, T005 in parallel to bootstrap both projects
2. **Write Tests First (Phase 2)**: Create all test files before implementation (TDD enforcement)
3. **Implement Backend (Phase 3 - Backend)**: Sequential implementation following critical path
4. **Implement Frontend (Phase 3 - Frontend)**: Can start after T027 (types), run component tasks in parallel
5. **Integrate & Validate (Phase 4)**: End-to-end testing after both backend and frontend complete
6. **Deploy (Phase 5)**: Set up CI/CD and deploy to production
7. **Document (Phase 6)**: Write comprehensive documentation and validate all requirements
**Success Criteria**:
- All 62 tasks completed with status ✅
- All tests passing (pytest and vitest) with coverage >= 80%
- Backend deployed to Cloud Run and accessible via /health endpoint
- Frontend deployed to Firebase Hosting and displaying predictions
- Cloud Scheduler triggering daily updates successfully
- Documentation complete (READMEs, API docs, data model)
- Validation tasks confirm Fair Play Points, caching, retry logic, and performance requirements met