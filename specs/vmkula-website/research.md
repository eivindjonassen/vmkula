# Research Report: vmkula-website

**Research Date**: 2025-12-25  
**Research Type**: Codebase Architecture Analysis  
**Status**: Complete

---

## Executive Summary

The vmkula project is in **early development stage** with a working POC but no production code. Key findings:

✅ **POC Complete**: Vite + React prototype with Gemini AI integration  
✅ **Database Ready**: SQLite with complete tournament structure (104 matches, 48 teams)  
✅ **Specifications Defined**: Detailed spec document for production  
❌ **Production Code**: No Next.js frontend or Python backend implemented  
❌ **Deployment Infrastructure**: No Firestore, Cloud Run, or API-Football integration  

---

## Technology Stack Analysis

### Current Stack (POC)

| Component | Technology | Version | Status |
|-----------|------------|---------|--------|
| Frontend | React + TypeScript | React 19.0.3, TS 5.8.2 | ✅ Working |
| Build Tool | Vite | 6.2.0 | ✅ Working |
| AI Service | Google Gemini | @google/genai 1.34.0 | ✅ Working |
| Database | SQLite | worldcup2026.db | ✅ Ready |

### Dependencies (poc/package.json)

**Production Dependencies**:
```json
{
  "react": "^19.0.3",
  "react-dom": "^19.0.3",
  "@google/genai": "^1.34.0"
}
```

**Development Dependencies**:
```json
{
  "@types/node": "^22.14.0",
  "@vitejs/plugin-react": "^5.0.0",
  "typescript": "~5.8.2",
  "vite": "^6.2.0"
}
```

### Required Stack (Production)

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Frontend** | Next.js 15+ (App Router) | Spec requirement, SEO optimization |
| **Backend** | Python 3.11+ | Spec requirement, pandas/numpy ecosystem |
| **Backend Framework** | FastAPI | Lightweight, async, Cloud Run compatible |
| **Testing (Backend)** | Pytest | Industry standard for Python |
| **Testing (Frontend)** | Vitest | Fast, Vite-native test runner |
| **Deployment (Frontend)** | Firebase Hosting | User-specified, free tier available |
| **Deployment (Backend)** | Cloud Run | Serverless, cost-effective, auto-scaling |

---

## Codebase Structure Analysis

### Current Structure (POC Only)

```
vmkula/
├── poc/                    # 🟢 WORKING Vite + React prototype
│   ├── components/
│   │   └── GroupCard.tsx   # Group stage table component (174 lines)
│   ├── services/
│   │   └── geminiService.ts # AI prediction service (95 lines)
│   ├── App.tsx             # Main app with tabs (409 lines)
│   ├── types.ts            # TypeScript interfaces (90 lines)
│   ├── constants.ts        # Hardcoded teams, venues, matches
│   ├── vite.config.ts      # Vite config with env var injection
│   └── package.json
│
├── specs/                  # 🟡 PLANNING artifacts
│   └── vmkula-website/
│       ├── spec.md         # Functional requirements (139 lines)
│       ├── plan.md         # Technical plan (this phase)
│       └── tasks.md        # Empty (awaiting /tasks command)
│
├── .bifrost/               # 🔧 AI development framework
├── .opencode/              # 🔧 OpenCode configuration
├── worldcup2026.db         # 🟢 SQLite tournament structure
└── vmkula-init.md          # 📖 Original technical spec (204 lines)
```

### Recommended Production Structure

```
vmkula/                     # Monorepo root
├── frontend/               # Next.js App Router
│   ├── app/
│   ├── components/
│   └── lib/
├── backend/                # Python Cloud Run Job
│   ├── src/
│   ├── tests/
│   └── requirements.txt
├── poc/                    # Keep as reference
└── specs/                  # Bifrost artifacts
```

---

## Database Analysis

### SQLite Schema (worldcup2026.db)

**Verified Tables**:

1. **teams** (48 teams)
   - Primary key: `id`
   - Columns: `team_name`, `fifa_code`, `group_letter`, `is_placeholder`
   - Sample: Mexico (id=1, group=A), Poland (id=2, group=A)

2. **matches** (104 matches)
   - Primary key: `id`
   - Columns: `match_number`, `home_team_id`, `away_team_id`, `city_id`, `stage_id`, `kickoff_at`, `match_label`
   - Breakdown: 72 group stage + 32 knockout matches
   - Sample: Match #1 (Mexico vs Poland, Group A, June 12 2026)

3. **host_cities** (16 venues)
   - Primary key: `id`
   - Columns: `city_name`, `country`, `stadium`, `region`, `airport_code`
   - Coverage: USA, Canada, Mexico

4. **tournament_stages** (7 stages)
   - Primary key: `id`
   - Columns: `stage_name`, `stage_order`
   - Stages: Group, Round of 32, Round of 16, Quarter-finals, Semi-finals, Third Place, Final

**Key Findings**:
- ✅ Complete tournament structure ready
- ✅ Placeholder teams for playoffs (is_placeholder=1)
- ✅ TBD knockout matches (home_team_id/away_team_id = NULL)
- ❌ No card data (yellow/red cards) - must come from API-Football

---

## POC Code Analysis

### Component Patterns

#### GroupCard Component (poc/components/GroupCard.tsx)

**Functionality**:
- Displays group stage table with team standings
- Sorts teams by AI-predicted rank
- Shows team flag emoji, name, stats (P-W-D-L-GF-GA-GD-Pts)

**Key Logic** (reusable for production):
```tsx
// Sorting by AI predicted rank or fallback to points
const sortedTeams = [...group.teams].sort((a, b) => {
  if (predictions) {
    const aPred = predictions.find(p => p.teamId === a.id);
    const bPred = predictions.find(p => p.teamId === b.id);
    return (aPred?.rank || 5) - (bPred?.rank || 5);
  }
  return b.points - a.points;  // Fallback to points
});
```

**Reuse Recommendation**: Port component structure to Next.js, preserve sorting logic.

---

#### Gemini AI Service (poc/services/geminiService.ts)

**Functionality**:
- Client-side Gemini API calls
- Structured JSON schema for responses
- Generates group predictions + tournament path

**Current Implementation** (client-side):
```typescript
const ai = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const response = await ai.models.generateContent({
  model: "gemini-3-flash-preview",
  config: {
    responseMimeType: "application/json",
    responseSchema: { /* ... */ }
  }
});
```

**⚠️ CRITICAL ARCHITECTURAL SHIFT**:
- POC: Client-side AI calls with hardcoded prompts
- Production: **Server-side (Python)** with data-driven prompts including team stats

**Reuse Recommendation**: 
- ✅ Reuse JSON schema structure
- ✅ Reuse prompt format (group predictions + tournament path)
- ❌ Do NOT reuse client-side approach (move to Python backend)

---

### Type Definitions (poc/types.ts)

**Highly Reusable** - Port directly to Next.js:

```typescript
export interface TeamStats {
  id: number;
  name: string;
  flag: string;
  played: number;
  won: number;
  draw: number;
  lost: number;
  goalsFor: number;
  goalsAgainst: number;
  points: number;
  predictedPlacement?: string;
  predictedRank?: number;
}

export interface Match {
  id: number;
  matchNumber: number;
  homeTeamId: number | null;  // null for TBD knockout matches
  awayTeamId: number | null;
  cityId: number;
  stageId: number;
  kickoff: string;
  label: string;
  prediction?: MatchPrediction;
}

export interface MatchPrediction {
  winnerId: number | 'draw' | null;
  winProbability: number;
  reasoning: string;
  predictedHomeScore: number;
  predictedAwayScore: number;
  predictedWinnerLabel?: string;
}
```

**Action Item**: Create `frontend/lib/types.ts` by copying and extending these interfaces.

---

## Integration Point Analysis

### Current POC Integration

| Integration | Status | Implementation |
|-------------|--------|----------------|
| **Gemini AI** | ✅ Working | Direct client-side calls |
| **Firestore** | ❌ Not integrated | N/A |
| **API-Football** | ❌ Not integrated | N/A |
| **SQLite** | ⚠️ Partial | Data hardcoded in constants.ts, not reading from .db |

### Required Production Integration

**Backend Data Flow** (per spec.md):
```
SQLite → API-Football → FIFA Engine → Data Aggregator → Gemini AI → Firestore
```

**Frontend Data Flow**:
```
Firestore → Next.js → Display (groups/matches/bracket)
```

---

## Existing Patterns & Conventions

### Code Organization

✅ **Well-Structured POC**:
- Clear separation: `components/`, `services/`, `types.ts`
- Single-file constants for static data
- Type-safe interfaces for all entities

✅ **Naming Conventions**:
- PascalCase for components (`GroupCard`, `App`)
- camelCase for services (`geminiService`, `getWorldCupAnalysis`)
- Descriptive interfaces (`AIAnalysis`, `MatchPrediction`, `TeamStats`)

### TypeScript Patterns

**Modern React 19 + TypeScript 5.8**:
- Functional components with hooks
- Strict type checking enabled
- Nullable types for TBD matches (`homeTeamId: number | null`)

**Example** (handling TBD matches gracefully):
```typescript
const getTeamName = (id: number | null, label: string) => {
  if (id !== null && allTeams[id]) return allTeams[id].name;
  return label;  // Use placeholder label for TBD
};
```

---

## Build & Deployment Configuration

### POC Build Setup (Vite)

**vite.config.ts**:
```typescript
export default defineConfig({
  plugins: [react()],
  define: {
    'process.env.GEMINI_API_KEY': JSON.stringify(process.env.GEMINI_API_KEY)
  }
});
```

**Features**:
- ✅ Dev server on port 3000
- ✅ HMR (Hot Module Replacement) enabled
- ✅ Environment variables injected via `loadEnv()`

**Missing**:
- ❌ No Docker/Cloud Run config
- ❌ No Vercel/Firebase deployment config
- ❌ No production build optimizations

### Production Requirements

**Frontend (Next.js → Firebase Hosting)**:
- `firebase.json` configuration
- `next.config.js` with Firebase output settings
- Environment variables in Firebase console

**Backend (Python → Cloud Run)**:
- `Dockerfile` with Python 3.11+ base image
- `requirements.txt` with dependencies
- Cloud Run service YAML configuration
- Service account with Firestore write permissions

---

## Testing Infrastructure

### Current Status

❌ **No Tests Found**:
- No test files (`.test.ts`, `.spec.py`)
- No test framework configuration (Jest, Pytest, Vitest)
- No CI/CD pipeline

### Required Testing (per spec.md)

**Spec Requirement**: TDD with 80% coverage threshold

**Test Frameworks**:
- **Backend**: Pytest with `pytest-cov` for coverage
- **Frontend**: Vitest + React Testing Library

**TDD State Tracking**:
- `.bifrost/tdd-state.json` enforces test-first development
- States: IDLE → TEST_FAILING → IMPLEMENTING → TEST_PASSING → COMMITTED

---

## Constraints & Risks

### Technical Constraints

1. **Database Design**:
   - SQLite uses `is_placeholder` flag for TBD playoff teams
   - Frontend must handle `null` team IDs for knockout matches
   - **Mitigation**: Already handled in POC (`getTeamName()` function)

2. **API-Football Quotas**:
   - Free tier: 100 requests/day
   - **Risk**: Could exceed during development
   - **Mitigation**: Aggressive local JSON caching (24-hour TTL)

3. **Gemini AI Costs**:
   - ~$0.10 per 104 predictions
   - **Risk**: Repeated calls during development/testing
   - **Mitigation**: 1-retry max, then rule-based fallback

### Architectural Risks

1. **POC → Production Migration**:
   - POC is Vite/React, production requires Next.js
   - **Impact**: Cannot directly reuse POC code
   - **Reusable**: `types.ts`, `constants.ts`, component logic patterns

2. **No Python Code Exists**:
   - Core FIFA engine logic (standings, 3rd place ranking) not implemented
   - Round of 32 bracket resolution is complex
   - **Risk**: High-complexity logic with zero test coverage
   - **Mitigation**: TDD approach mandated by spec

3. **TDD Enforcement vs. No Tests**:
   - `.bifrost/tdd-state.json` enforces test-first development
   - **Conflict**: No tests exist currently
   - **Resolution**: Start backend implementation with pytest setup first

---

## Recommendations

### What to Reuse from POC

✅ **Highly Reusable**:

1. **Type Definitions** (`types.ts`):
   - `TeamStats`, `Match`, `Venue`, `Stage`, `MatchPrediction`, `AIAnalysis`
   - Use in both Next.js frontend and Python backend (via OpenAPI spec)

2. **Component Logic** (`GroupCard.tsx`, `App.tsx`):
   - Team sorting logic (by points, then AI rank)
   - Match prediction display patterns
   - TBD matchup handling

3. **Constants** (`constants.ts`):
   - Venues, stages data structure
   - Initial groups structure
   - **NOTE**: Migrate to reading from SQLite instead of hardcoding

4. **Gemini Prompt Structure** (`geminiService.ts`):
   - JSON schema for AI responses
   - Prompt format requesting group predictions + tournament path
   - **ADAPT**: Move to Python, add team stats to prompts

⚠️ **Do NOT Reuse Directly**:
1. Vite configuration (Next.js has different build system)
2. Client-side Gemini calls (must be server-side in Python)
3. Hardcoded match data (should read from SQLite)

### What to Rebuild for Production

🔨 **Critical Backend Components** (Priority Order):

1. **`db_manager.py`** - Priority: CRITICAL
   - Read tournament structure from `worldcup2026.db`
   - Test: Verify 104 matches, 48 teams loaded correctly

2. **`fifa_engine.py`** - Priority: CRITICAL
   - Calculate group standings (3pts win, 1pt draw, tiebreakers)
   - Rank top 8 third-place teams
   - Resolve Round of 32 matchups
   - **COMPLEXITY**: High - requires TDD per vmkula-init.md

3. **`data_aggregator.py`** - Priority: HIGH
   - Fetch team stats from API-Football
   - Calculate avg xG, clean sheets, form string
   - Cache results locally (24-hour TTL)

4. **`ai_agent.py`** - Priority: HIGH
   - Build prompts with aggregated stats
   - Call Gemini with structured schema
   - Parse responses (strip markdown, validate JSON)
   - Implement retry + fallback logic (1 retry max)

5. **`firestore_publisher.py`** - Priority: MEDIUM
   - Assemble TournamentSnapshot
   - Publish to Firestore predictions/latest

🎨 **Critical Frontend Components**:

1. **App Router Structure** (`app/`):
   - `page.tsx` - Main landing with tabs
   - `groups/page.tsx` - Group stage tables
   - `matches/page.tsx` - Match schedule
   - `bracket/page.tsx` - Knockout bracket visualization

2. **Firestore Integration** (`lib/firestore.ts`):
   - Fetch predictions from Firestore
   - Display last updated timestamp
   - Trigger backend refresh if stale

3. **Component Ports**:
   - Port `GroupCard.tsx` to Next.js component
   - Port match display logic
   - Add mobile-responsive Tailwind styles

---

## Architectural Decisions

### Decision 1: Backend-First TDD Approach

**Recommendation**: Implement `fifa_engine.py` first with full test coverage

**Rationale**:
- Core "logic in Python" philosophy per spec
- Complex tiebreaker logic (Fair Play Points, head-to-head)
- High risk of bugs without tests

**Risk**: Medium effort - need to handle edge cases carefully

---

### Decision 2: Monorepo Structure

**Recommendation**: Keep monorepo (frontend/ + backend/ in same repo)

**Rationale**:
- Easier coordination between frontend and backend
- Shared type definitions (can generate OpenAPI spec from Python → TypeScript)
- Simplified CI/CD pipeline

**Structure**:
```
vmkula/
├── frontend/       # Next.js
├── backend/        # Python
├── shared/         # SQLite DB, configs
└── poc/            # Keep as reference
```

---

### Decision 3: Aggressive Caching for Cost Optimization

**Recommendation**: Implement caching layer FIRST before fetching live data

**Rationale**:
- API-Football free tier: 100 requests/day
- Development/testing will exceed quota quickly
- Production needs predictable costs

**Implementation**:
```python
# backend/src/data_aggregator.py
CACHE_DIR = Path("cache")
CACHE_TTL_HOURS = 24

def get_cached_stats(team_id: int) -> TeamStatistics | None:
    """Load from cache if less than 24 hours old"""
    today = datetime.now().strftime("%Y-%m-%d")
    cache_file = CACHE_DIR / f"team_stats_{team_id}_{today}.json"
    
    if cache_file.exists():
        age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if age < timedelta(hours=CACHE_TTL_HOURS):
            return load_from_cache(cache_file)
    return None
```

---

### Decision 4: Firestore Single-Document Strategy

**Recommendation**: Use single Firestore document for all predictions

**Rationale**:
- Simplifies frontend queries (one read operation)
- Atomic updates (all predictions consistent)
- Cost-effective (1 document read per frontend load)

**Schema**:
```
predictions/
└── latest/
    ├── updated_at
    ├── groups { A: [...], B: [...], ... }
    ├── bracket [ {match73}, {match74}, ... ]
    ├── ai_summary
    ├── favorites
    └── dark_horses
```

---

## Next Steps for Planning Phase

### Immediate Actions Before `/tasks`

1. ✅ **Review this research report** - Confirmed with user
2. ✅ **Create data-model.md** - Complete entity definitions
3. ✅ **Create plan.md** - Comprehensive technical plan
4. ⏳ **Validate plan** - Run validate-plan.sh script
5. ⏳ **Commit artifacts** - Git commit plan + research docs

### Ready for `/tasks vmkula-website`

When user executes `/tasks`, generate task breakdown for:

**Sprint 1: Backend Foundation** (TDD-first)
- Task 1.1: Set up Python environment + pytest
- Task 1.2: Implement `db_manager.py` + tests
- Task 1.3-1.5: Implement `fifa_engine.py` with full tiebreaker logic + tests

**Sprint 2: Data Integration**
- Task 2.1-2.2: Implement `data_aggregator.py` with caching + metrics
- Task 2.3: Implement `ai_agent.py` + Gemini integration + retry logic
- Task 2.4: Implement `firestore_publisher.py`

**Sprint 3: API Orchestration**
- Task 3.1: Implement `main.py` FastAPI app
- Task 3.2: Dockerize backend for Cloud Run

**Sprint 4: Frontend (Next.js)**
- Task 4.1: Set up Next.js App Router project
- Task 4.2: Port POC types and create Firestore client
- Task 4.3-4.5: Implement components (GroupCard, MatchCard, BracketView)

**Sprint 5: Integration & Deployment**
- Task 5.1-5.2: End-to-end integration tests
- Task 5.3-5.4: Deploy to Cloud Run + Firebase Hosting
- Task 5.5: Set up Cloud Scheduler for periodic updates

---

## Appendix: Files Examined

### Source Code Files
- ✅ `poc/App.tsx` (409 lines) - Main React app
- ✅ `poc/types.ts` (90 lines) - TypeScript interfaces
- ✅ `poc/services/geminiService.ts` (95 lines) - AI integration
- ✅ `poc/components/GroupCard.tsx` (174 lines) - Group table component
- ✅ `poc/constants.ts` - Static data (venues, teams, matches)
- ✅ `poc/vite.config.ts` - Build configuration

### Configuration Files
- ✅ `poc/package.json` - Dependencies
- ✅ `poc/tsconfig.json` - TypeScript config
- ✅ `opencode.json` - AI development settings
- ✅ `.gitignore` - Version control exclusions

### Documentation Files
- ✅ `vmkula-init.md` (204 lines) - Original technical spec
- ✅ `specs/vmkula-website/spec.md` (139 lines) - Detailed requirements
- ✅ `AGENTS.md` - AI development workflow guide
- ✅ `init-rules.md` - Constitution generation template

### Database Files
- ✅ `worldcup2026.db` - SQLite schema verified, 4 tables, 104 matches confirmed

### Files NOT Found
- ❌ `requirements.txt` - Python dependencies
- ❌ `frontend/` - Next.js production code
- ❌ `backend/` - Python production code
- ❌ `.env.local` - Environment variables (in .gitignore, expected)
- ❌ Test files (`.test.ts`, `.spec.py`, `.test.tsx`)

---

**End of Research Report**
