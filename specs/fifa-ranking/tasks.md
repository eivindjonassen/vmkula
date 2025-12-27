# Tasks: FIFA Ranking Integration

**Feature**: fifa-ranking  
**Total Tasks**: 21  
**Parallel Tasks**: 14 tasks can run in parallel  
**Approach**: Following Test-Driven Development (TDD) approach with tests created before implementation. BeautifulSoup4 scraper with single-document Firestore storage pattern, 30-day TTL cache, and integration with prediction pipeline.

---

## Phase 1: Setup & Dependencies (3 tasks)

### T001: Add BeautifulSoup4 and lxml dependencies
**Status**: ✅ Complete
**File**: `backend/requirements.txt`  
**Description**: Add HTML parsing libraries for FIFA rankings scraping:
- Add `beautifulsoup4>=4.12.0` for HTML parsing
- Add `lxml>=4.9.0` for fast XML/HTML parsing backend
- These dependencies enable static HTML scraping without JavaScript rendering
**Dependencies**: None  
**Parallel**: Yes [P]

### T002: Add responses library for HTTP mocking in tests
**Status**: ✅ Complete
**File**: `backend/requirements-dev.txt`  
**Description**: Add HTTP mocking library for test fixtures:
- Add `responses>=0.24.0` for mocking HTTP requests in tests
- Enables testing scraper without hitting live FIFA.com
- Follows existing test pattern from test_data_aggregator.py
**Dependencies**: None  
**Parallel**: Yes [P]

### T003: Install new dependencies and verify imports
**Status**: ✅ Complete
**File**: `backend/`  
**Description**: Install newly added dependencies and verify they work:
- Run `pip install -r requirements.txt` to install beautifulsoup4 and lxml
- Run `pip install -r requirements-dev.txt` to install responses
- Verify imports: `python -c "from bs4 import BeautifulSoup; from lxml import etree; import responses"`
- Confirm no import errors or conflicts with existing dependencies
**Dependencies**: T001, T002  
**Parallel**: No

---

## Phase 2: Tests First (TDD) (9 tasks)

### T004: Create test file for FIFA ranking scraper
**Status**: ✅ Complete
**File**: `backend/tests/test_fifa_ranking_scraper.py` (new)  
**Description**: Create empty test file structure for FIFA ranking scraper:
- Import pytest, unittest.mock (Mock, patch, MagicMock)
- Import datetime, timedelta for TTL testing
- Define TestFIFARankingScraper class
- Add module-level docstring explaining test purpose
- This file will contain all failing tests created in T005-T012
**Dependencies**: T003  
**Parallel**: No

### T005: Write failing test for scraper initialization
**Status**: ✅ Complete
**File**: `backend/tests/test_fifa_ranking_scraper.py`  
**Description**: Create test for FIFARankingScraper class initialization:
- Test: `test_scraper_initialization()`
- Verify scraper.RANKINGS_URL equals "https://inside.fifa.com/fifa-world-ranking/men"
- Verify scraper.MIN_DELAY_SECONDS equals 2.0 (polite scraping)
- Verify scraper.CACHE_TTL_DAYS equals 30 (monthly updates)
- **Expected**: Test will FAIL (class doesn't exist yet)
**Dependencies**: T004  
**Parallel**: Yes [P]

### T006: Write failing test for HTTP fetching with retry logic
**Status**: ✅ Complete
**File**: `backend/tests/test_fifa_ranking_scraper.py`  
**Description**: Create tests for fetch_rankings_page() method:
- Test: `test_fetch_rankings_page_success()` - Mock successful HTTP 200 response
- Test: `test_fetch_rankings_page_retry_on_failure()` - Mock 503 errors, succeed on 3rd attempt
- Test: `test_fetch_rankings_page_max_retries_exceeded()` - Mock persistent failures, verify DataAggregationError raised
- Verify User-Agent header is set in request
- Verify exponential backoff delays: [1s, 2s, 4s]
- **Expected**: All tests will FAIL (method doesn't exist yet)
**Dependencies**: T004  
**Parallel**: Yes [P]

### T007: Write failing test for HTML parsing
**Status**: ✅ Complete
**File**: `backend/tests/test_fifa_ranking_scraper.py`  
**Description**: Create tests for parse_rankings() method:
- Test: `test_parse_rankings_table_success()` - Parse mock HTML with 2 teams
- Verify returned structure: list of dicts with rank, team_name, fifa_code, confederation, points, previous_rank, rank_change
- Test: `test_parse_rankings_handles_missing_data()` - Parse incomplete HTML gracefully
- Mock HTML fixture should mimic FIFA.com table structure
- **Expected**: All tests will FAIL (method doesn't exist yet)
**Dependencies**: T004  
**Parallel**: Yes [P]

### T008: Write failing test for rankings validation
**Status**: ✅ Complete
**File**: `backend/tests/test_fifa_ranking_scraper.py`  
**Description**: Create tests for validate_completeness() method:
- Test: `test_validate_rankings_completeness()` - Verify 211 teams = valid, 200 teams = invalid
- Test should check total count equals expected FIFA member nations
- **Expected**: Test will FAIL (method doesn't exist yet)
**Dependencies**: T004  
**Parallel**: Yes [P]

### T009: Write failing test for rate limiting enforcement
**Status**: ✅ Complete
**File**: `backend/tests/test_fifa_ranking_scraper.py`  
**Description**: Create test for _enforce_rate_limit() method:
- Test: `test_rate_limiting_enforced()` - Mock time.time() and time.sleep()
- Verify that if 1 second elapsed, sleep called with 1.0 (to reach 2.0 total delay)
- Verify that if 2+ seconds elapsed, no sleep called
- **Expected**: Test will FAIL (method doesn't exist yet)
**Dependencies**: T004  
**Parallel**: Yes [P]

### T010: Write failing test for Firestore storage integration
**Status**: ✅ Complete
**File**: `backend/tests/test_fifa_ranking_scraper.py`  
**Description**: Create tests for scrape_and_store() full workflow:
- Test: `test_scrape_and_store_success()` - Mock fetch, parse, Firestore write
- Test: `test_cache_hit_avoids_scraping()` - Mock valid cached data, verify fetch_rankings_page NOT called
- Test: `test_force_refresh_bypasses_cache()` - Verify force_refresh=True always scrapes
- Verify returned dict contains: success, teams_scraped, duration_seconds, fetched_at, cache_expires_at
- **Expected**: All tests will FAIL (method doesn't exist yet)
**Dependencies**: T004  
**Parallel**: Yes [P]

### T011: Write failing test for team ranking lookup
**Status**: ✅ Complete
**File**: `backend/tests/test_fifa_ranking_scraper.py`  
**Description**: Create tests for get_ranking_for_team() method:
- Test: `test_get_ranking_for_team_success()` - Mock Firestore doc with rankings, lookup "FRA"
- Test: `test_get_ranking_for_team_not_found()` - Lookup non-existent code "ZZZ", return None
- Mock Firestore document structure: {"rankings": [...], "fetched_at": ..., "total_teams": 211}
- **Expected**: All tests will FAIL (method doesn't exist yet)
**Dependencies**: T004  
**Parallel**: Yes [P]

### T012: Write failing tests for Firestore manager methods
**Status**: ✅ Complete
**File**: `backend/tests/test_firestore_manager.py`  
**Description**: Add tests to existing Firestore manager test file:
- Test: `test_get_fifa_rankings_success()` - Mock Firestore doc, verify data returned
- Test: `test_update_fifa_rankings_with_ttl()` - Mock Firestore write, verify fetched_at and expires_at timestamps
- Verify TTL calculation: expires_at = fetched_at + timedelta(days=30)
- **Expected**: Tests will FAIL (methods don't exist yet)
**Dependencies**: T003  
**Parallel**: Yes [P]

---

## Phase 3: Core Implementation (6 tasks)

### T013: Implement FIFARankingScraper class initialization
**Status**: ✅ Complete
**File**: `backend/src/fifa_ranking_scraper.py` (new)  
**Description**: Create FIFARankingScraper class with initialization:
- Define class constants: RANKINGS_URL, MIN_DELAY_SECONDS (2.0), CACHE_TTL_DAYS (30)
- Initialize `last_request_time = 0.0` for rate limiting
- Import required libraries: requests, BeautifulSoup, time, datetime, logging
- Add type hints for all methods
- Follow PascalCase for class name (RULES.md:9-16)
- **Expected**: T005 test should now PASS
**Dependencies**: T005 (test created)  
**Parallel**: No

### T014: Implement HTTP fetching with retry logic and rate limiting
**File**: `backend/src/fifa_ranking_scraper.py`  
**Description**: Implement fetch_rankings_page() and _enforce_rate_limit() methods:
- Implement `_enforce_rate_limit()`: Calculate elapsed time, sleep if needed to reach MIN_DELAY_SECONDS
- Implement `fetch_rankings_page()`: HTTP GET with User-Agent header, exponential backoff retry [1s, 2s, 4s]
- Reuse retry pattern from data_aggregator.py:352-424
- Raise DataAggregationError after max retries exceeded
- Add logging for attempts and failures
- **Expected**: T006 and T009 tests should now PASS
**Dependencies**: T006, T009 (tests created), T013 (class exists)  
**Parallel**: No

### T015: Implement HTML parsing with BeautifulSoup
**File**: `backend/src/fifa_ranking_scraper.py`  
**Description**: Implement parse_rankings() method:
- Use BeautifulSoup with lxml parser
- Find FIFA rankings table (inspect FIFA.com HTML structure for correct selectors)
- Extract data for each team: rank, team_name, fifa_code, confederation, points, previous_rank
- Calculate rank_change: current_rank - previous_rank
- Handle missing data gracefully (log warning, use defaults or skip row)
- Return List[Dict[str, Any]] with 211 team dictionaries
- **Expected**: T007 test should now PASS
**Dependencies**: T007 (test created), T013 (class exists)  
**Parallel**: No

### T016: Implement Firestore methods in FirestoreManager
**File**: `backend/src/firestore_manager.py`  
**Description**: Add FIFA rankings methods to existing FirestoreManager class:
- Implement `get_fifa_rankings()`: Fetch fifa_rankings/latest document, return dict or None if expired/missing
- Implement `update_fifa_rankings(data, ttl_days=30)`: Write to fifa_rankings/latest with fetched_at and expires_at
- Implement `is_fifa_rankings_cache_valid()`: Check if expires_at > now
- Reuse TTL pattern from update_team_stats() (firestore_manager.py:169-193)
- Add type hints: `-> Optional[Dict[str, Any]]`
- **Expected**: T012 tests should now PASS
**Dependencies**: T012 (test created)  
**Parallel**: Yes [P]

### T017: Implement full scraping workflow in scrape_and_store()
**File**: `backend/src/fifa_ranking_scraper.py`  
**Description**: Implement scrape_and_store() orchestration method:
- Check cache validity with FirestoreManager.is_fifa_rankings_cache_valid()
- If cache valid and force_refresh=False, return cached data
- Otherwise: fetch_rankings_page() → parse_rankings() → validate 211 teams → store with update_fifa_rankings()
- Store raw HTML in raw_api_responses collection (reuse pattern from firestore_manager.py:457-497)
- Track duration_seconds with start/end timestamps
- Return result dict: {success, teams_scraped, duration_seconds, fetched_at, cache_expires_at, error_message}
- **Expected**: T010 test should now PASS
**Dependencies**: T010 (test created), T014 (fetch), T015 (parse), T016 (Firestore)  
**Parallel**: No

### T018: Implement helper methods validate_completeness() and get_ranking_for_team()
**File**: `backend/src/fifa_ranking_scraper.py`  
**Description**: Implement remaining helper methods:
- `validate_completeness(rankings)`: Check len(rankings) == 211, return bool
- `get_ranking_for_team(fifa_code)`: Fetch fifa_rankings/latest, filter by fifa_code, return team dict or None
- Add logging for validation failures and lookups
- **Expected**: T008 and T011 tests should now PASS
**Dependencies**: T008, T011 (tests created), T016 (Firestore methods)  
**Parallel**: Yes [P]

---

## Phase 4: API Integration & Endpoints (3 tasks)

### T019: Create FastAPI endpoint for manual FIFA rankings sync
**File**: `backend/src/main.py`  
**Description**: Add POST /api/sync-fifa-rankings endpoint:
- Define request model: `class SyncFIFARankingsRequest(BaseModel): force_refresh: bool = False`
- Implement endpoint handler: Instantiate FIFARankingScraper, call scrape_and_store()
- Return response: {success, teams_scraped, duration_seconds, fetched_at, cache_expires_at}
- Handle errors: Catch DataAggregationError, return 500 with error details and cached_data_available flag
- Add endpoint documentation with docstring
- Code location: After existing sync endpoints (around line 450-500)
- **Expected**: Manual API call to POST /api/sync-fifa-rankings should work
**Dependencies**: T017 (scraper complete)  
**Parallel**: No

### T020: Integrate FIFA rankings into team stats enrichment
**File**: `backend/src/data_aggregator.py`  
**Description**: Modify fetch_team_stats() to include FIFA ranking:
- After fetching xG and form data, call FIFARankingScraper().get_ranking_for_team(team.fifa_code)
- If ranking found, add to stats dict: fifa_ranking, fifa_points, fifa_confederation
- If ranking not found, log warning but continue (graceful degradation)
- Handle case where team.fifa_code is None or empty
- Code location: Around lines 540-604 (team stats fetching loop in main.py or data_aggregator.py)
- **Expected**: Team stats now include FIFA ranking data when available
**Dependencies**: T018 (get_ranking_for_team implemented)  
**Parallel**: No

### T021: Update AI prompt to include FIFA rankings
**File**: `backend/src/ai_agent.py`  
**Description**: Enhance AI prediction prompt with FIFA ranking data:
- In generate_prediction() method, check if team_stats contains fifa_ranking field
- If present, add to prompt: "FIFA Ranking: #{rank} ({points} pts, {confederation})"
- Place after form and xG data in prompt template
- Handle None case gracefully (skip FIFA ranking in prompt if unavailable)
- Code location: ai_agent.py generate_prediction() method (around prompt construction)
- **Expected**: AI predictions now consider FIFA rankings when generating outcomes
**Dependencies**: T020 (stats enrichment complete)  
**Parallel**: No

---

## Validation Checklist

- [x] All functional requirements from spec.md have corresponding tasks:
  - FR-001 (Scrape 211 teams): T015, T017
  - FR-002 (Click "Show full rankings"): Research shows static HTML, not needed
  - FR-003 (Extract data points): T015
  - FR-004 (Separate storage): T016
  - FR-005 (Historical snapshots): T016 (TTL-based), T017 (raw storage)
  - FR-006 (Manual trigger): T019
  - FR-007 (Graceful failure): T014, T017
  - FR-008 (Optimize storage): T016 (single document pattern)
  - FR-009 (Validate completeness): T008, T018
  - FR-010 (Track metadata): T017
- [x] All endpoints from contracts/fifa_ranking_api.md have tasks:
  - POST /api/sync-fifa-rankings: T019
  - Internal methods (scrape_and_store, parse_rankings, get_ranking_for_team): T013-T018
  - Firestore methods (get_fifa_rankings, update_fifa_rankings): T016
- [x] All entities from data-model.md have implementation tasks:
  - FIFA Rankings Document: T016, T017
  - Raw Scraping Response: T017
  - Team Stats Enrichment: T020
- [x] All test tasks (Phase 2) ordered before implementation tasks (Phase 3): ✅ T004-T012 before T013-T018
- [x] All tasks have specific file paths and clear descriptions: ✅
- [x] Parallel tasks correctly identified (independent files, no dependencies): ✅ 14 tasks marked [P]
- [x] Dependencies explicitly noted for sequential tasks: ✅
- [x] Security considerations addressed: No API keys needed (public data), service account permissions already configured
- [x] Translation keys: Not applicable (backend-only feature)
- [x] Documentation updates: Not required per plan (internal backend feature)

---

## Summary

**Total Tasks**: 21  
**Estimated Effort**: ~12 hours
- Phase 1 (Setup): 3 tasks, ~0.5 hours
- Phase 2 (Tests): 9 tasks, ~4 hours
- Phase 3 (Implementation): 6 tasks, ~5 hours
- Phase 4 (Integration): 3 tasks, ~2.5 hours

**Parallel Execution**: 14 of 21 tasks can run in parallel
- Phase 1: T001 and T002 can run in parallel (different files)
- Phase 2: T005-T011 can run in parallel (independent test methods in same file or different files)
- Phase 3: T016 and T018 can run in parallel (different files: firestore_manager.py vs fifa_ranking_scraper.py)

**Implementation Strategy**:
1. **Phase 1**: Install dependencies (T001-T003) - must complete before tests can run
2. **Phase 2**: Create all failing tests (T004-T012) - strict TDD approach, tests before implementation
3. **Phase 3**: Implement scraper and Firestore methods (T013-T018) - make tests pass incrementally
4. **Phase 4**: Integrate with API and prediction pipeline (T019-T021) - connect all pieces

**Critical Path**: T001 → T003 → T004 → T005 → T013 → T014 → T017 → T019 → T020 → T021

**Success Criteria**:
- All 9 test tasks (T005-T012, plus additions to T012) passing (100% pass rate)
- Test coverage ≥80% for new fifa_ranking_scraper.py module
- All 211 FIFA teams successfully scraped and stored
- Team stats enriched with FIFA ranking data
- AI predictions include FIFA rankings in prompt
- Manual sync endpoint functional: `POST /api/sync-fifa-rankings`
- Graceful degradation: predictions continue if FIFA rankings unavailable

**TDD Enforcement**:
- Phase 2 (Tests) MUST complete before Phase 3 (Implementation)
- Each implementation task (T013-T018) has corresponding test task (T005-T012)
- Tests will fail (RED) until implementation makes them pass (GREEN)
- Refactoring can occur after tests pass while keeping them green

**Reusable Patterns Leveraged**:
- Rate limiting: data_aggregator.py:726-731
- Retry logic: data_aggregator.py:352-424
- TTL caching: firestore_manager.py:169-193
- Raw response storage: firestore_manager.py:457-497
- Test mocking: test_data_aggregator.py, test_firestore_manager.py
