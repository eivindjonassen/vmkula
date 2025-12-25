# Feature Specification: vmkula-website

**Feature Branch**: N/A (initial commit)
**Created**: 2025-12-25
**Status**: Draft

---

## User Scenarios & Testing

### Primary User Story
*As a football enthusiast, I want to view AI-powered predictions for the 2026 World Cup so that I can understand which teams are likely to advance and win matches based on data-driven analysis.*

### Acceptance Scenarios

1. **Given** the user visits the website, **When** they view the group stage tables, **Then** they should see all 12 groups with team standings calculated using FIFA rules (points, goal difference, goals scored) and AI-predicted final rankings.

2. **Given** match results have been fetched from API-Football, **When** the Python backend calculates group standings, **Then** it must correctly apply FIFA tiebreaker rules and identify the top 8 third-place teams for Round of 32 qualification.

3. **Given** a user browses the match schedule, **When** they select an upcoming match, **Then** they should see AI prediction with win probability, predicted score, and reasoning based on aggregated team statistics (xG, form, clean sheets).

4. **Given** the group stage is complete, **When** the user views the knockout bracket, **Then** they should see resolved matchups (e.g., "Winner A vs 3rd Place C" becomes "Mexico vs Poland") with AI predictions for each round.

5. **Given** the Python backend job runs, **When** it fetches team statistics from API-Football, **Then** it must aggregate data (average xG over last 5 games, form string, clean sheets) and provide this context to Gemini AI for prediction generation.

6. **Given** Gemini AI returns a prediction, **When** the response is processed, **Then** it must be parsed correctly (handling markdown formatting like ```json blocks) and validated before publishing to Firestore.

7. **Given** the frontend loads predictions, **When** Firestore data is retrieved, **Then** the UI must display updated predictions with timestamp, group standings, and bracket progression.

### Edge Cases & Unhappy Paths

- **What happens when two teams in a group have identical points, goal difference, and goals scored?**
  - System must apply FIFA head-to-head tiebreaker rules.
  - [TBD: Confirm exact tiebreaker sequence beyond head-to-head - to be determined during planning phase]

- **What happens when API-Football returns incomplete statistics for a team?**
  - System must handle missing xG data gracefully and provide a "data unavailable" prediction with lower confidence indicator.

- **What happens when Gemini AI returns malformed JSON or refuses to predict?**
  - System must implement cost-effective retry strategy (recommended: 1 retry with exponential backoff, then fallback to rule-based prediction).

- **What happens when the Round of 32 matchup resolution has ambiguous third-place qualifiers?**
  - System must use the official FIFA bracket mapping table stored in `worldcup2026.db`.

- **What happens when the frontend requests predictions but Firestore data is outdated?**
  - System must automatically trigger a backend refresh to fetch and calculate new predictions.

- **Permissions:**
  - This is a public website with no authentication required. User preferences (favorites, bookmarks) are stored in browser local storage.

---

## Requirements

### Functional Requirements

#### Backend (Python)

- **FR-001**: The system MUST load the complete tournament structure from `worldcup2026.db`, including all 104 matches, 48 teams, 12 groups, and stage information.

- **FR-002**: The system MUST fetch live match results from API-Football v3 using the endpoint `GET /fixtures?league=1&season=2026&status=FT` during active tournament periods.

- **FR-003**: The system MUST calculate group stage standings using FIFA rules: 3 points for win, 1 for draw, 0 for loss, with tiebreakers of (1) points, (2) goal difference, (3) goals scored.

- **FR-004**: The system MUST rank all third-place teams across the 12 groups and identify the top 8 qualifiers for the Round of 32 based on the same tiebreaker criteria.

- **FR-005**: The system MUST resolve Round of 32 matchups by mapping placeholder labels (e.g., "Winner A vs 3rd Place C/D/E") to actual qualified teams based on group results and third-place rankings.

- **FR-006**: The system MUST fetch team statistics from API-Football for the last 5 matches of each team, including goals scored/conceded and expected goals (xG) data.

- **FR-007**: The system MUST aggregate raw API-Football data into AI-ready metrics: average xG (last 5 games), clean sheets count, and form string (W-D-L sequence).

- **FR-008**: The system MUST generate prediction prompts for Gemini AI that include aggregated team statistics, not just team names, and explicitly request valid JSON responses.

- **FR-009**: The system MUST parse Gemini AI responses, stripping markdown formatting (e.g., ```json code blocks) and validating JSON structure before use.

- **FR-010**: The system MUST publish prediction results to Firestore in a structured format containing groups (with calculated standings), bracket (with resolved matchups), and AI predictions (winner, probability, reasoning, predicted score).

- **FR-011**: The system MUST include a timestamp in the published Firestore document to indicate when predictions were last updated.

- **FR-012**: The system MUST cache API-Football team statistics locally during development to avoid excessive API calls.

- **FR-013-BACKEND**: The system MUST implement a cost-effective retry strategy for Gemini AI calls: maximum 1 retry attempt with exponential backoff before falling back to rule-based predictions.

- **FR-014-BACKEND**: The system MUST generate "data unavailable" predictions with low confidence indicators when API-Football returns incomplete team statistics.

- **FR-015-BACKEND**: The system MUST retrieve FIFA's official bracket mapping table from `worldcup2026.db` to resolve Round of 32 matchups between group winners and qualified third-place teams.

#### Frontend (Next.js)

- **FR-016**: The system MUST display all 12 group stage tables with teams sorted by calculated standings (points, goal difference, goals scored).

- **FR-017**: The system MUST show AI-predicted final rankings for each group, indicating which teams are expected to finish 1st, 2nd, and 3rd.

- **FR-018**: The system MUST display the complete match schedule with filtering options by stage (Group Stage, Round of 32, Round of 16, Quarter-finals, Semi-finals, Final).

- **FR-019**: The system MUST show detailed match cards for each fixture, including teams, venue, kickoff time, and AI prediction (win probability, predicted score, reasoning).

- **FR-020**: The system MUST display the knockout bracket with resolved matchups, showing progression from Round of 32 to the Final.

- **FR-021**: The system MUST retrieve prediction data from Firestore and display the last updated timestamp.

- **FR-022**: The system MUST automatically trigger a backend refresh when Firestore prediction data is detected as outdated or stale.

- **FR-023**: The system MUST provide a responsive UI optimized for mobile and desktop viewing using Tailwind CSS.

- **FR-024**: The system MUST handle TBD matchups in the knockout stage by showing placeholder labels (e.g., "Winner of Group A") until teams are determined.

- **FR-025**: The system MUST allow users to mark teams as favorites and store these preferences in browser local storage without requiring authentication.

- **FR-026**: The system MUST indicate prediction confidence level visually, showing lower confidence for predictions based on incomplete data.

### Key Entities

- **Team**: Represents a national team in the tournament. Key attributes are: id, name, flag emoji, group assignment.

- **Match**: Represents a fixture in the tournament. Key attributes are: match number, home team, away team, venue, stage, kickoff time, actual score (if played), predicted score, AI prediction.

- **Group**: Represents a group in the group stage. Key attributes are: group letter (A-L), list of teams, calculated standings table.

- **Stage**: Represents a phase of the tournament. Key attributes are: stage name (Group Stage, Round of 32, etc.), order/sequence.

- **Venue**: Represents a stadium hosting matches. Key attributes are: city, country, stadium name, region, airport code.

- **TeamStatistics**: Represents aggregated performance data for a team. Key attributes are: average xG (last 5 games), clean sheets count, form string (W-D-L), goals for/against.

- **Prediction**: Represents an AI-generated match prediction. Key attributes are: predicted winner, win probability percentage, reasoning text, predicted home score, predicted away score.

- **TournamentSnapshot**: Represents the complete prediction state. Key attributes are: updated timestamp, group standings, resolved bracket matchups, all match predictions.

---

## Review & Acceptance Checklist

- [ ] **Clarity**: The spec is written for a non-technical audience.
- [ ] **Completeness**: All mandatory sections are filled, and there are no remaining `[NEEDS CLARIFICATION]` markers. (`[TBD]` markers are acceptable for items to be determined during planning phase.)
- [ ] **Purity**: The spec focuses purely on **WHAT** is needed, not **HOW** to build it. There are no implementation details (languages, frameworks, databases, etc.).
- [ ] **Testability**: All functional requirements are specific, measurable, and can be turned into a failing test case.
