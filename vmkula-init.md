# Technical Specification: vmkula.no (World Cup 2026)

---

### 1. Project Overview

* **Domain:** vmkula.no
* **Objective:** Provide a real-time World Cup 2026 bracket with daily AI-driven win probability and stage predictions.
* **Reference:** Current Proof of Concept (PoC) for UI/UX layout and bracket visualization.

### 2. Tech Stack

* **Frontend:** Next.js (App Router) for SSR/SEO optimization.
* **Backend/Database:** Firebase (Firestore) for real-time data synchronization.
* **AI Engine:** Gemini 3.0 Pro (via Vertex AI or Google AI Studio).
* **Compute:** Cloud Run Jobs (Dockerized Python/Node.js) for heavy-duty AI processing.
* **Data Source:** API-Football (v3) for live match data and historical stats.

### 3. Data Schema (Firestore)

#### `/matches/{match_id}`

```json
{
  "homeTeam": "Norway",
  "awayTeam": "Brazil",
  "score": { "home": 2, "away": 1 },
  "status": "FT",
  "timestamp": "2026-06-15T18:00:00Z"
}

```

#### `/predictions/latest`

```json
{
  "tournament_winner": "Argentina",
  "bracket_structure": { "round_of_16": [...], "quarter_finals": [...] },
  "ai_logic": "String explaining recent logic changes based on match results",
  "last_synced": "Timestamp"
}

```

### 4. Functional Requirements & TDD Specs

| Module | Requirement | Test Case (TDD) |
| --- | --- | --- |
| **Real-time UI** | Bracket must update without page refresh when Firestore data changes. | `expect(ui.bracket).toUpdateOn(firestore.snapshot)` |
| **AI Sync Job** | Cloud Run Job must trigger via Cloud Scheduler at 23:00 UTC daily. | `expect(job.status).toBe(200)` after daily match completion. |
| **Prediction Logic** | Gemini 3.0 Pro must ingest current standings + results to output valid JSON. | `expect(gemini.output).toBeValidJSON()` and match tournament schema. |
| **User Favorites** | Users can "star" a team to highlight them across the bracket and tables. | `expect(localStorage.getItem('fav_team')).toBe(teamId)` |
| **SEO/Social** | Every stage/match must have unique metadata for social sharing. | `expect(header.ogTitle).toContain(matchTeams)` |

### 5. System Workflow

1. **Ingestion:** Cloud Run Job fetches latest results from API-Football.
2. **Reasoning:** Results + Previous Prediction + Historical Data fed to Gemini 3.0 Pro.
3. **Persistence:** Updated bracket and AI reasoning string saved to Firestore.
4. **Distribution:** Next.js frontend listens to Firestore `onSnapshot`, updating the UI for all active users instantly.
5. **Personalization:** Client-side logic reads `localStorage` to apply CSS highlights to the user's "favorited" team.

### 6. Deployment Strategy

* **Frontend:** Firebase App Hosting (supports Next.js SSR).
* **Secrets:** All API keys (Football API, Gemini) stored in Google Secret Manager or Cloud Run Environment Variables.
* **Caching:** Use Gemini Context Caching for the 48-team base data to minimize token costs.
