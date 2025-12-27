# Tasks: API-Football Data Refactor

**Feature**: api-football-data-refactor  
**Total Tasks**: 28  
**Parallel Tasks**: 18 tasks can run in parallel  
**Approach**: Option A+ (Enhanced) - TDD-first approach with legacy cleanup + API-Football canonical source. Tests created before implementation, following Red-Green-Refactor cycle.

---

## Phase 1: Setup & Legacy Cleanup

### T001: Delete legacy migration script
**File**: `backend/migrate_to_firestore.py`
**Status**: ✅ Complete
**Description**: Delete the legacy one-time migration script that references non-existent `db_manager.py`.
- Remove entire file (no longer needed, migration already complete)
- Verify no other files import from this script
**Dependencies**: None
**Parallel**: Yes [P]

### T002: Delete broken Norway integration test
**File**: `backend/test_norway_integration.py`
**Description**: Delete test file with broken `DBManager` import.
- Remove entire file (references deprecated module)
- Alternative: If test logic is valuable, rewrite without DBManager dependency
**Dependencies**: None
**Parallel**: Yes [P]

### T003: Remove DBManager comments from main.py
**File**: `backend/src/main.py`
**Description**: Clean up legacy documentation comments referencing old `DBManager`.
- Remove comment at line 167 (old DBManager reference)
- Remove comment at line 190 (old DBManager reference)
- Remove comment at line 193 (old DBManager reference)
- Update any relevant docstrings to reflect Firestore-only architecture
**Dependencies**: None
**Parallel**: Yes [P]

### T004: Remove DBManager import from populate script
**File**: `backend/populate_from_api_football.py`
**Description**: Remove deprecated `DBManager` import and related code.
- Remove `from src.db_manager import DBManager` (line 28)
- Remove any DBManager usage in migration logic (if present)
- Verify script still functional without DBManager
**Dependencies**: None
**Parallel**: Yes [P]

---

## Phase 2: Tests First (TDD - Red Phase)

### T005: Create failing test for storing raw API responses
**File**: `backend/tests/test_api_football_sync.py` (new)
**Description**: Create first test for sync module - storing raw API-Football responses.
- Import required testing modules (pytest, Mock from unittest.mock)
- Create `test_sync_teams_stores_raw_response()` test
- Mock FirestoreManager and DataAggregator
- Mock API-Football response with sample teams data
- Create APIFootballSync instance (will fail - class doesn't exist yet)
- Assert `firestore_manager.store_raw_api_response()` called with correct args
- Expected: ❌ Test FAILS (APIFootballSync class doesn't exist)
**Dependencies**: None
**Parallel**: Yes [P]

### T006: Create failing test for change detection
**File**: `backend/tests/test_api_football_sync.py`
**Description**: Create test for detecting changes between API data and existing Firestore data.
- Create `test_detect_changes_identifies_new_teams()` test
- Setup existing teams in Firestore (mock data)
- Setup raw API response with new team added
- Call `sync.detect_changes(raw_entities, existing)`
- Assert correct identification of new entities (entities_to_add)
- Assert unchanged entities correctly identified
- Expected: ❌ Test FAILS (detect_changes method doesn't exist)
**Dependencies**: T005
**Parallel**: No

### T007: Create failing test for conflict resolution with manual overrides
**File**: `backend/tests/test_api_football_sync.py`
**Description**: Create test for preserving manual overrides during sync.
- Create `test_resolve_conflicts_preserves_manual_overrides()` test
- Create Conflict object with manual_override=True
- Call `sync.resolve_conflicts(conflicts, force_update=False)`
- Assert resolution action is "preserve_override"
- Assert conflict is logged
- Expected: ❌ Test FAILS (resolve_conflicts method doesn't exist)
**Dependencies**: T005
**Parallel**: No

### T008: Create failing test for force update mode
**File**: `backend/tests/test_api_football_sync.py`
**Description**: Create test for forcing updates even with manual overrides.
- Create `test_resolve_conflicts_forces_update_when_requested()` test
- Create Conflict object with manual_override=True
- Call `sync.resolve_conflicts(conflicts, force_update=True)`
- Assert resolution action is "apply_api_update"
- Assert manual_override flag cleared
- Expected: ❌ Test FAILS (method doesn't exist)
**Dependencies**: T005
**Parallel**: No

### T009: Create failing test for sync_teams method
**File**: `backend/tests/test_api_football_sync.py`
**Description**: Create end-to-end test for teams sync process.
- Create `test_sync_teams_end_to_end()` test
- Mock complete API-Football teams response
- Mock existing Firestore teams
- Call `sync.sync_teams(league_id=1, season=2026)`
- Assert raw response stored
- Assert change detection performed
- Assert teams collection updated
- Assert sync result returned with correct counts
- Expected: ❌ Test FAILS (sync_teams method doesn't exist)
**Dependencies**: T005
**Parallel**: No

### T010: Create failing test for sync_fixtures method
**File**: `backend/tests/test_api_football_sync.py`
**Description**: Create end-to-end test for fixtures sync process.
- Create `test_sync_fixtures_end_to_end()` test
- Mock complete API-Football fixtures response
- Mock existing Firestore matches
- Call `sync.sync_fixtures(league_id=1, season=2026)`
- Assert raw response stored
- Assert change detection performed
- Assert matches collection updated
- Expected: ❌ Test FAILS (sync_fixtures method doesn't exist)
**Dependencies**: T005
**Parallel**: No

### T011: Create failing tests for Firestore raw collection methods
**File**: `backend/tests/test_firestore_manager.py`
**Description**: Add tests for new api_football_raw collection operations.
- Create `test_store_raw_api_response()` test
- Create `test_get_raw_api_response()` test
- Mock Firestore client
- Assert document created with correct structure (entity_type, raw_response, metadata)
- Assert timestamps added (fetched_at)
- Expected: ❌ Tests FAIL (methods don't exist in FirestoreManager)
**Dependencies**: None
**Parallel**: Yes [P]

### T012: Create failing test for sync endpoint
**File**: `backend/tests/test_main.py`
**Description**: Add test for new `POST /api/sync-api-football` endpoint.
- Import TestClient from fastapi.testclient
- Create `test_sync_api_football_endpoint_teams()` test
- Send POST request with {"entity_type": "teams", "league_id": 1, "season": 2026}
- Assert 200 status code
- Assert response contains sync result (status, changes_detected, synced_at)
- Create `test_sync_api_football_endpoint_fixtures()` test for fixtures
- Expected: ❌ Tests FAIL (endpoint doesn't exist)
**Dependencies**: None
**Parallel**: Yes [P]

### T013: Create failing test for legacy cleanup validation
**File**: `backend/tests/test_legacy_cleanup.py` (new)
**Description**: Create validation test ensuring no DBManager references remain.
- Create `test_no_dbmanager_imports_in_codebase()` test
- Use subprocess to run `grep -r "from src.db_manager" backend/`
- Assert returncode != 0 (no matches found)
- Assert stdout is empty
- Expected: ✅ Test PASSES after T001-T004 complete
**Dependencies**: T001, T002, T003, T004
**Parallel**: No

---

## Phase 3: Core Implementation (TDD - Green Phase)

### T014: Extend FirestoreManager with raw collection methods
**File**: `backend/src/firestore_manager.py`
**Description**: Add methods for api_football_raw collection operations.
- Add `api_football_raw_collection` property (reference to collection)
- Implement `store_raw_api_response()` method:
  - Parameters: entity_type, league_id, season, raw_response
  - Create document with ID format: "{entity_type}_{league_id}_{season}"
  - Include metadata: fetched_at (timestamp), api_version, endpoint
  - Return document ID
- Implement `get_raw_api_response()` method:
  - Parameters: entity_type, league_id, season
  - Fetch and return raw response document
  - Return None if not found
- Add type hints for all parameters and return values
**Code Location**: New methods, add after existing collection properties
**Dependencies**: T011 (test created)
**Parallel**: Yes [P]

### T015: Create APIFootballSync class skeleton
**File**: `backend/src/api_football_sync.py` (new)
**Description**: Create new sync module with class structure and data classes.
- Import required modules (typing, dataclasses, logging)
- Create `SyncResult` dataclass with fields:
  - status, entity_type, changes_detected, conflicts_resolved
  - entities_added, entities_updated, entities_unchanged
  - raw_document_id, synced_at, details (list)
- Create `ChangeSet` dataclass with fields:
  - entities_to_add, entities_to_update, entities_unchanged, conflicts
- Create `Conflict` dataclass with fields:
  - entity_id, entity_name, firestore_value, api_value, field, manual_override
- Create `Resolution` dataclass with fields:
  - entity_id, action, conflict_logged
- Create `APIFootballSync` class with __init__ accepting firestore_manager and data_aggregator
- Add stub methods (raise NotImplementedError):
  - sync_teams(), sync_fixtures(), detect_changes(), resolve_conflicts()
- Add logging setup
**Code Location**: New file in backend/src/
**Dependencies**: T005 (test created)
**Parallel**: Yes [P]

### T016: Implement detect_changes method
**File**: `backend/src/api_football_sync.py`
**Description**: Implement change detection logic.
- Implement `detect_changes(raw_entities, existing_entities)` method
- Create mapping of existing entities by ID for fast lookup
- Iterate through raw_entities:
  - If ID not in existing: add to entities_to_add
  - If ID in existing:
    - Compare relevant fields (name, code, etc.)
    - If changed and not manual_override: add to entities_to_update
    - If changed and manual_override: add to conflicts
    - If unchanged: add to entities_unchanged
- Return ChangeSet with categorized entities
- Add detailed logging for each category
- Handle edge cases (missing fields, None values)
**Code Location**: Lines 50-100 (estimate)
**Dependencies**: T006 (test created), T015 (class skeleton)
**Parallel**: No

### T017: Implement resolve_conflicts method
**File**: `backend/src/api_football_sync.py`
**Description**: Implement conflict resolution logic.
- Implement `resolve_conflicts(conflicts, force_update)` method
- Iterate through conflicts list:
  - If force_update=False:
    - Create Resolution with action="preserve_override"
    - Log conflict for manual review
    - Set conflict_logged=True
  - If force_update=True:
    - Create Resolution with action="apply_api_update"
    - Prepare update to clear manual_override flag
    - Log forced update
- Return list of Resolution objects
- Add detailed logging for transparency
**Code Location**: Lines 100-140 (estimate)
**Dependencies**: T007, T008 (tests created), T015 (class skeleton)
**Parallel**: No

### T018: Implement sync_teams method
**File**: `backend/src/api_football_sync.py`
**Description**: Implement teams sync orchestration logic.
- Implement `sync_teams(league_id, season, force_update)` method
- Step 1: Fetch teams from API-Football using data_aggregator
  - Call API-Football endpoint: GET /teams?league={league_id}&season={season}
  - Handle rate limiting (reuse data_aggregator's built-in handling)
- Step 2: Store raw response using firestore_manager.store_raw_api_response()
- Step 3: Fetch existing teams from Firestore
- Step 4: Call detect_changes() to identify updates needed
- Step 5: Call resolve_conflicts() if conflicts detected
- Step 6: Apply updates to teams collection:
  - Add new teams with api_football_raw_id reference
  - Update changed teams with last_synced_at timestamp
  - Log conflicts in sync_conflicts field for manual overrides
- Step 7: Build and return SyncResult with detailed summary
- Add comprehensive error handling and logging
**Code Location**: Lines 140-220 (estimate)
**Dependencies**: T009 (test created), T016, T017 (helper methods implemented)
**Parallel**: No

### T019: Implement sync_fixtures method
**File**: `backend/src/api_football_sync.py`
**Description**: Implement fixtures sync orchestration logic.
- Implement `sync_fixtures(league_id, season, force_update)` method
- Similar process to sync_teams but for fixtures:
  - Fetch from API-Football: GET /fixtures?league={league_id}&season={season}
  - Store raw response
  - Detect changes comparing with matches collection
  - Resolve conflicts
  - Update matches collection
  - Return SyncResult
- Map API-Football fixture fields to internal match schema:
  - fixture.id → api_football_fixture_id
  - teams.home.id → home_team_id
  - teams.away.id → away_team_id
  - fixture.date → kickoff
  - fixture.venue → venue
  - fixture.status → status
- Handle TBD knockout matches gracefully (null team IDs)
**Code Location**: Lines 220-300 (estimate)
**Dependencies**: T010 (test created), T016, T017 (helper methods implemented)
**Parallel**: No

### T020: Add sync endpoint to FastAPI
**File**: `backend/src/main.py`
**Description**: Add `POST /api/sync-api-football` endpoint to FastAPI application.
- Import APIFootballSync from api_football_sync module
- Create request model (SyncRequest) with pydantic:
  - entity_type: str (enum: "teams", "fixtures")
  - league_id: int
  - season: int
  - force_update: bool = False
- Create endpoint handler `sync_api_football(request: SyncRequest)`:
  - Initialize APIFootballSync with firestore_manager and data_aggregator
  - Route based on entity_type:
    - If "teams": call sync.sync_teams()
    - If "fixtures": call sync.sync_fixtures()
    - Else: return 400 error
  - Return SyncResult as JSON
  - Add error handling (try/except with proper HTTP status codes)
- Add endpoint documentation with OpenAPI annotations
**Code Location**: New endpoint after existing endpoints (~line 1000)
**Dependencies**: T012 (test created), T018, T019 (sync methods implemented)
**Parallel**: No

---

## Phase 4: Integration & Enhancement

### T021: Add API-Football fetch_teams method to DataAggregator
**File**: `backend/src/data_aggregator.py`
**Description**: Add method to fetch teams list from API-Football (currently only fetches team stats).
- Add `fetch_teams(league_id, season)` method to DataAggregator class
- Endpoint: GET /teams?league={league_id}&season={season}
- Implement with existing rate limiting (reuse _enforce_rate_limit)
- Return raw API-Football response (full JSON)
- Add error handling with exponential backoff (same as existing methods)
- Cache response locally if beneficial (consistent with existing caching strategy)
**Code Location**: New method, add after fetch_team_stats (around line 425)
**Dependencies**: None
**Parallel**: Yes [P]

### T022: Add API-Football fetch_fixtures method to DataAggregator
**File**: `backend/src/data_aggregator.py`
**Description**: Add method to fetch fixtures list from API-Football.
- Add `fetch_fixtures(league_id, season)` method to DataAggregator class
- Endpoint: GET /fixtures?league={league_id}&season={season}
- Implement with existing rate limiting
- Return raw API-Football response
- Add error handling with exponential backoff
- Note: Different from existing `fetch_from_api` which fetches team-specific fixtures
**Code Location**: New method, add after fetch_teams
**Dependencies**: None
**Parallel**: Yes [P]

### T023: Update populate script to use new sync module
**File**: `backend/populate_from_api_football.py`
**Description**: Refactor populate script to use APIFootballSync instead of manual logic.
- Import APIFootballSync from api_football_sync
- Add CLI flags: `--sync-teams`, `--sync-fixtures`, `--force-update`
- Replace manual team ID mapping logic with sync_teams() call
- Add sync_fixtures() call when --sync-fixtures flag provided
- Preserve existing API_FOOTBALL_TEAM_IDS mapping (for reference/documentation)
- Update main() function to handle new flags
- Add progress reporting (show sync results)
- Update docstring to reflect new sync-based approach
**Code Location**: Replace migration logic (lines 146-201), update main() function
**Dependencies**: T004 (DBManager removed), T018, T019 (sync methods available)
**Parallel**: No

### T024: Add backward-compatible fields to teams collection schema
**File**: `backend/src/firestore_manager.py`
**Description**: Update team creation/update methods to include new sync metadata fields.
- Modify team document creation to include:
  - api_football_raw_id: str (reference to raw collection document)
  - last_synced_at: str (ISO8601 timestamp, null initially)
  - manual_override: bool (false by default)
  - sync_conflicts: list (empty array by default)
- Ensure backward compatibility: existing documents without these fields work correctly
- Update get_all_teams() to handle documents with/without new fields
- Add migration helper method if needed (optional)
**Code Location**: Modify create_team/update_team methods
**Dependencies**: T014 (Firestore methods available)
**Parallel**: Yes [P]

### T025: Add backward-compatible fields to matches collection schema
**File**: `backend/src/firestore_manager.py`
**Description**: Update match creation/update methods to include new sync metadata fields.
- Modify match document creation to include:
  - api_football_raw_id: str
  - last_synced_at: str
  - manual_override: bool
  - sync_conflicts: list
- Ensure backward compatibility with existing match documents
- Update get_all_matches() to handle documents with/without new fields
**Code Location**: Modify create_match/update_match methods
**Dependencies**: T014 (Firestore methods available)
**Parallel**: Yes [P]

---

## Phase 5: Documentation & Validation

### T026: Update data model documentation
**File**: `backend/docs/data-model.md`
**Description**: Document new api_football_raw collection and updated schemas.
- Add section for `api_football_raw` collection:
  - Document structure, document IDs
  - Field descriptions (entity_type, raw_response, metadata)
  - Purpose and usage examples
- Update `Team` entity documentation:
  - Add new fields (api_football_raw_id, last_synced_at, manual_override, sync_conflicts)
  - Document backward compatibility
- Update `Match` entity documentation similarly
- Update data flow diagram to include sync process
- Remove any remaining SQLite references
**Code Location**: Add new section, update existing entity documentation
**Dependencies**: T024, T025 (schema changes implemented)
**Parallel**: Yes [P]

### T027: Create sync process documentation
**File**: `backend/docs/SYNC_PROCESS.md` (new)
**Description**: Create comprehensive documentation for sync workflow.
- Document sync endpoint usage:
  - Request examples (curl, Python)
  - Response interpretation
  - Error handling
- Document conflict resolution workflow:
  - When conflicts occur
  - How to review sync_conflicts field
  - How to resolve manually (update Firestore, set manual_override)
  - When to use force_update flag
- Document troubleshooting:
  - Common errors and solutions
  - How to rollback using raw collection
  - How to replay sync from raw data
- Add usage examples:
  - Initial World Cup 2026 data sync
  - Periodic fixture updates
  - Historical tournament data sync
**Code Location**: New documentation file
**Dependencies**: T020 (sync endpoint implemented)
**Parallel**: Yes [P]

### T028: Update README with new architecture and remove SQLite references
**File**: `backend/README.md`
**Description**: Update README to reflect new architecture and remove outdated SQLite instructions.
- Remove SQLite setup section (database no longer used)
- Remove references to worldcup2026.db file
- Add "API-Football Sync" section:
  - Explain new sync process
  - Link to SYNC_PROCESS.md
  - Show basic sync command examples
- Update architecture diagram to show:
  - API-Football → api_football_raw → teams/matches → predictions
  - Remove SQLite components
- Update "Getting Started" section if needed
- Update dependencies list (no sqlite3 module)
**Code Location**: Multiple sections throughout file
**Dependencies**: T026, T027 (documentation complete)
**Parallel**: Yes [P]

---

## Validation Checklist

- [x] All critical requirements from spec.md have corresponding tasks:
  - FR-001: Fetch WC2026 fixtures from API-Football (T022, T019)
  - FR-002: Fetch team statistics from API-Football (existing + T021)
  - FR-003: Cache API-Football data with TTL (T014, T024, T025)
  - FR-004: Manual triggers for sync (T020)
  - FR-005: Fetch historical tournament data (T023 with --sync-fixtures)
  - FR-006: Eliminate legacy storage (T001-T004)
  - FR-007: Maintain backward compatibility (T024, T025)
  - FR-008: Handle missing API team IDs gracefully (existing fallback logic preserved)
  - FR-009: Smart cache invalidation (existing hash-based logic preserved)
  - FR-010: Preserve rate limiting (T021, T022 reuse existing logic)

- [x] All endpoints from plan have contract test tasks:
  - POST /api/sync-api-football (T012 test, T020 implementation)

- [x] All entities from data-model have implementation tasks:
  - api_football_raw collection (T014 implementation)
  - Updated teams collection (T024 schema update)
  - Updated matches collection (T025 schema update)

- [x] All test tasks are ordered before implementation tasks (TDD):
  - Phase 2 (T005-T013) creates all failing tests
  - Phase 3 (T014-T020) implements code to make tests pass

- [x] All tasks have specific file paths and clear descriptions:
  - Every task includes File field with exact path
  - Descriptions include line numbers where relevant

- [x] Parallel tasks correctly identified (independent files, no dependencies):
  - 18 tasks marked [P] - verified independent file modifications

- [x] Dependencies explicitly noted for sequential tasks:
  - All Phase 3 tasks depend on Phase 2 tests
  - Sequential dependencies within phases noted

---

## Summary

**Total Tasks**: 28
**Estimated Effort**: ~12-16 hours (breakdown per phase)
- Phase 1 (Legacy Cleanup): 4 tasks, ~1 hour
- Phase 2 (Tests): 9 tasks, ~3-4 hours
- Phase 3 (Implementation): 7 tasks, ~5-7 hours
- Phase 4 (Integration): 5 tasks, ~2-3 hours
- Phase 5 (Documentation): 3 tasks, ~1-2 hours

**Parallel Execution**: 18 tasks can run in parallel (64%)
- Phase 1: All 4 tasks (T001-T004) - different files, no shared state
- Phase 2: T005, T011, T012 can run in parallel (independent test files)
- Phase 3: T014, T015 can run in parallel (different files)
- Phase 4: T021, T022, T024, T025 can run in parallel (different methods/files)
- Phase 5: All 3 tasks (T026-T028) - different documentation files

**Implementation Strategy**:
1. **Start with legacy cleanup** (T001-T004) to remove broken code references
2. **Create all failing tests** (T005-T013) following TDD red phase
3. **Implement sync infrastructure** (T014-T015) to establish foundation
4. **Implement core sync logic** (T016-T020) to make tests pass (TDD green phase)
5. **Enhance integration** (T021-T025) to complete API-Football integration
6. **Update documentation** (T026-T028) to reflect new architecture

**Critical Path**: T001-T004 → T005 → T015 → T016 → T017 → T018 → T020 → T023 → T027

**Success Criteria**:
- All tests passing (including new sync tests)
- No DBManager references in codebase (T013 validation passes)
- Sync endpoint functional and documented
- Backward compatibility maintained (existing teams/matches schema preserved)
- Code coverage ≥80% (add ~300 lines of sync code with comprehensive tests)
- Documentation complete (SYNC_PROCESS.md, updated README, data-model.md)
- Manual sync workflow tested end-to-end (teams and fixtures)

**TDD State Tracking**:
- Phase 2 tasks set TDD state to TEST_FAILING
- Phase 3 tasks transition through IMPLEMENTING → TEST_PASSING → COMMITTED
- `.bifrost/tdd-state.json` updated by /implement command per Bifrost standards
