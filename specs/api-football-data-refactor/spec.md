# Feature Specification: API-Football Data Refactor

**Feature Branch**: N/A (main branch)  
**Created**: 2025-12-27  
**Status**: Draft

---

## Overview

The current data structure has become overcomplicated due to a hybrid approach between legacy storage and API-Football data. This refactor will simplify the architecture by using API-Football as the single source of truth for all match and team data, eliminating legacy data stores entirely and streamlining Firestore as a pure cache layer.

## User Scenarios & Testing

### Primary User Story

*As a system administrator, I want to refactor the data architecture to use API-Football as the single source of truth, so that I can eliminate data inconsistencies and simplify the codebase.*

### Acceptance Scenarios

1. **Given** the system has been refactored, **When** the backend fetches match data, **Then** all data must come exclusively from API-Football (not legacy storage).

2. **Given** API-Football returns World Cup 2026 fixtures, **When** the system loads tournament data, **Then** all matches, teams, and statistics must be pulled from API-Football and cached.

3. **Given** the system needs team statistics for AI predictions, **When** requesting the latest 5 matches for a team, **Then** the data must be fetched from API-Football and cached with a 24-hour TTL.

4. **Given** historical tournament data is needed for AI predictions, **When** the system loads past tournament data, **Then** it must be fetched once manually from API-Football and stored permanently.

5. **Given** the refactor is complete, **When** running the backend, **Then** legacy storage references must not exist in the codebase.

### Edge Cases & Unhappy Paths

- **What happens when API-Football rate limit is exceeded?**
  - System should fall back to cached data if available, or fail gracefully with clear error message.

- **What happens when a team has no API-Football ID mapping?**
  - System should mark the team with `has_real_data: false` and use fallback prediction methods.

- **What happens when historical data fetch fails?**
  - System should retry with exponential backoff (per RULES.md), then log failure for manual intervention.

- **Permissions required**: None (data refactor is backend-only, no user roles affected).

---

## Requirements

### Functional Requirements

- **FR-001**: The system MUST fetch all World Cup 2026 match fixtures exclusively from API-Football.

- **FR-002**: The system MUST fetch team statistics (last 5 matches, form, xG) exclusively from API-Football.

- **FR-003**: The system MUST cache all API-Football data with appropriate TTL (24 hours for live data, permanent for historical data).

- **FR-004**: The system MUST support manual triggers for data synchronization (not automatic/scheduled).

- **FR-005**: The system MUST fetch historical tournament data (past World Cups, qualifiers) manually and store permanently for AI prediction training.

- **FR-006**: The system MUST eliminate all legacy data storage dependencies from the codebase.

- **FR-007**: The system MUST maintain backward compatibility with existing data schema for teams, matches, and predictions collections.

- **FR-008**: The system MUST handle missing API-Football team ID mappings gracefully by setting `has_real_data: false` and using fallback prediction logic.

- **FR-009**: The system MUST implement smart cache invalidation that only regenerates predictions when team statistics change (hash-based).

- **FR-010**: The system MUST preserve existing rate limiting (0.5s between requests) and retry logic (exponential backoff).

### Key Entities

#### APIFootballMatch
Represents a fixture from API-Football. Key attributes:
- `fixture_id` (API-Football fixture ID)
- `league_id` (competition identifier, e.g., World Cup 2026)
- `home_team_id` (API-Football team ID)
- `away_team_id` (API-Football team ID)
- `kickoff` (ISO8601 timestamp)
- `venue` (stadium name and location)
- `status` (e.g., "scheduled", "finished", "live")
- `home_score` (null if not played)
- `away_score` (null if not played)
- `stage` (e.g., "Group A", "Round of 16")

#### APIFootballTeam
Represents a national team from API-Football. Key attributes:
- `api_football_id` (primary identifier)
- `name` (e.g., "Mexico")
- `fifa_code` (3-letter code, e.g., "MEX")
- `flag_emoji` (e.g., "🇲🇽")
- `is_qualified` (whether team is in World Cup 2026)

#### APIFootballTeamStats
Represents aggregated statistics for a team. Key attributes:
- `team_id` (reference to team)
- `form_string` (e.g., "W-W-D-L-W" for last 5 matches)
- `avg_xg_for` (average expected goals)
- `avg_xg_against` (average expected goals conceded)
- `clean_sheets` (number of matches without conceding)
- `data_completeness` (0.0-1.0 percentage of matches with xG data)
- `confidence` (high/medium/low based on data completeness)
- `fetched_at` (timestamp of last fetch)
- `ttl_hours` (time-to-live, default 24 hours)

#### HistoricalTournamentData
Represents past tournament data for AI training. Key attributes:
- `tournament_id` (e.g., "world_cup_2022")
- `matches` (array of historical match results)
- `teams` (participating teams and their stats)
- `fetched_at` (timestamp of manual fetch)
- `is_permanent` (true - data should not expire)

---

## Review & Acceptance Checklist

- [x] **Clarity**: The spec is written for a non-technical audience.
- [x] **Completeness**: All mandatory sections are filled, and there are no remaining `[NEEDS CLARIFICATION]` markers.
- [x] **Purity**: The spec focuses purely on **WHAT** is needed, not **HOW** to build it. There are no implementation details (languages, frameworks, databases, etc.).
- [x] **Testability**: All functional requirements are specific, measurable, and can be turned into a failing test case.

---

**End of Specification**
