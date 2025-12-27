# Project Constitution: vmkula-website

**Last Updated**: 2025-12-25

---

## 1. Code Style Guidelines

### Python (Backend)
- **Formatter**: Black (line length: 88)
- **Linter**: mypy for type checking
- **Naming Conventions**:
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
  - Private methods: `_leading_underscore`

### TypeScript/JavaScript (Frontend)
- **Formatter**: Biome (replaces Prettier)
- **Linter**: Biome (replaces ESLint)
- **Configuration**: `frontend/biome.json`
- **Naming Conventions**:
  - Functions/variables: `camelCase`
  - Components: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
  - Types/Interfaces: `PascalCase`
- **Scripts**:
  - `npm run lint` - Check for issues
  - `npm run lint:fix` - Auto-fix issues
  - `npm run format` - Format code

---

## 2. Test-Driven Development (TDD) Requirements

### Mandatory TDD Workflow
- ✅ **Write tests FIRST** before implementation
- ✅ **Run tests** to verify they fail (Red phase)
- ✅ **Implement code** to make tests pass (Green phase)
- ✅ **Refactor** while keeping tests green

### Coverage Requirements
- **Minimum Coverage**: 80% for all code (per spec.md)
- **Backend**: Use pytest with pytest-cov
- **Frontend**: Use Vitest with coverage plugin

### Test File Naming
- **Backend**: `test_*.py` in `backend/tests/`
- **Frontend**: `*.test.tsx` or `*.test.ts` in `frontend/__tests__/`

---

## 3. Technology Stack (Approved)

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Testing**: Pytest
- **Database**: SQLite (worldcup2026.db)
- **Cache**: Firestore
- **AI**: Google Gemini 3.0 Pro
- **Data Source**: API-Football v3
- **Deployment**: Google Cloud Run

### Frontend
- **Framework**: Next.js 15+ (App Router)
- **Language**: TypeScript 5.8+
- **Styling**: Tailwind CSS
- **Testing**: Vitest + React Testing Library
- **Database**: Firestore (client SDK)
- **Deployment**: Firebase Hosting

---

## 4. MCP Server Configuration

### Firebase MCP Server

This project uses the Firebase MCP server for Firestore operations during development and deployment.

**Configuration** (in `opencode.json`):
```json
{
  "mcpServers": {
    "firebase": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-firebase"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "${env:GOOGLE_APPLICATION_CREDENTIALS}"
      }
    }
  }
}
```

**Setup Instructions**:

1. **Download Service Account Key**:
   - Go to Firebase Console → Project Settings → Service Accounts
   - Click "Generate New Private Key"
   - Save the JSON file securely (DO NOT commit to git)

2. **Set Environment Variable**:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
   ```

3. **Add to .env** (local development):
   ```bash
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/firebase-service-account-key.json
   ```

**Available MCP Tools**:

**Authentication & Project Management**:
- `firebase_login` - Sign in to Firebase CLI
- `firebase_logout` - Sign out of Firebase CLI
- `firebase_get_environment` - Get current Firebase environment config
- `firebase_update_environment` - Update environment (project, user, project_dir)
- `firebase_get_project` - Get active project info
- `firebase_list_projects` - List available projects
- `firebase_create_project` - Create new Firebase project
- `firebase_list_apps` - List Firebase apps (iOS, Android, Web)
- `firebase_create_app` - Create new Firebase app
- `firebase_get_sdk_config` - Get Firebase SDK configuration

**Firestore Operations**:
- `firebase_firestore_get_documents` - Get specific documents by path
- `firebase_firestore_query_collection` - Query collection with filters
- `firebase_firestore_list_collections` - List all collections
- `firebase_firestore_delete_document` - Delete a document

**Realtime Database**:
- `firebase_realtimedatabase_get_data` - Read data from RTDB
- `firebase_realtimedatabase_set_data` - Write data to RTDB

**Authentication**:
- `firebase_auth_get_users` - Get users by UID/email/phone
- `firebase_auth_update_user` - Update user claims or disable/enable
- `firebase_auth_set_sms_region_policy` - Set SMS region restrictions

**Cloud Storage**:
- `firebase_storage_get_object_download_url` - Get download URL for storage objects

**Cloud Messaging**:
- `firebase_messaging_send_message` - Send push notifications

**Remote Config**:
- `firebase_remoteconfig_get_template` - Get Remote Config template
- `firebase_remoteconfig_update_template` - Update Remote Config

**Initialization & Security**:
- `firebase_init` - Initialize Firebase services (Firestore, Storage, Hosting, etc.)
- `firebase_validate_security_rules` - Validate security rules syntax
- `firebase_get_security_rules` - Get current security rules
- `firebase_read_resources` - Read firebase:// resources

**Usage Guidelines**:
- ✅ Use Firebase MCP for manual data inspection and testing
- ✅ Use Firebase MCP for seeding test data
- ✅ Use `firebase_firestore_query_collection` with filters for complex queries
- ✅ Use `firebase_update_environment` to switch between projects or set active project
- ✅ Use `firebase_validate_security_rules` before deploying security rules
- ❌ Do NOT use Firebase MCP in production backend code (use Python SDK instead)
- ❌ Do NOT commit service account keys to git
- ❌ Do NOT use `use_emulator: true` parameter in production queries

**Common Command Patterns**:

1. **Query Firestore Collection**:
   ```typescript
   firebase_firestore_query_collection({
     collection_path: "predictions",
     filters: [{
       field: "timestamp",
       op: "GREATER_THAN",
       compare_value: { integer_value: 1735132800 }
     }],
     limit: 10,
     order: {
       orderBy: "timestamp",
       orderByDirection: "DESCENDING"
     }
   })
   ```

2. **Get Specific Document**:
   ```typescript
   firebase_firestore_get_documents({
     paths: ["predictions/latest"],
     database: "(default)"
   })
   ```

3. **Switch Active Project**:
   ```typescript
   firebase_update_environment({
     active_project: "vmkula-2026"
   })
   ```

4. **Validate Security Rules**:
   ```typescript
   firebase_validate_security_rules({
     type: "firestore",
     source_file: "firestore.rules"
   })
   ```

---

## 5. API-Football Usage Guidelines

### Rate Limiting
- **Free Tier**: 100 requests/day
- **Required**: 0.5 second delay between requests
- **Retry Strategy**: Exponential backoff (1s, 2s, 4s) on 429/5xx errors

### Caching Strategy
- **Local Cache**: Save API responses to `backend/cache/` directory
- **TTL**: 24 hours
- **File Format**: `team_stats_{team_id}_{YYYY-MM-DD}.json`
- **Purpose**: Minimize API calls during development

### Endpoints Used
1. `GET /fixtures?league=1&season=2026&status=FT` - Match results
2. `GET /fixtures?team={id}&last=5` - Team recent matches
3. `GET /fixtures/statistics?fixture={id}` - Match statistics (xG data)

---

## 6. Gemini AI Usage Guidelines

### Cost Optimization
- **Retry Strategy**: Maximum 1 retry (2 total attempts)
- **Fallback**: Use rule-based prediction if Gemini fails twice
- **JSON Mode**: Always use `response_mime_type: 'application/json'` for parsing stability

### Prompt Requirements
- ✅ Include aggregated team statistics (avg_xG, clean_sheets, form_string)
- ✅ Request structured JSON output with specific schema
- ✅ Provide context (not just team names)
- ❌ Do NOT send raw API-Football logs to Gemini

---

## 7. FIFA Tiebreaker Logic (Critical)

### Tiebreaker Sequence
When teams have equal points in group standings:

1. **Goal Difference** (GD)
2. **Goals Scored**
3. **Head-to-Head** (if applicable)
4. **Fair Play Points** (calculated from cards)
5. **Deterministic Seed** (final fallback)

### Fair Play Points Calculation
- Yellow card: -1 point
- Second yellow / Indirect red: -3 points
- Direct red card: -4 points

### CRITICAL: Deterministic Final Fallback
- ⚠️ **Do NOT use `random.choice()` or `random.random()`**
- ✅ **Use `hash(team_name)` for deterministic seed**
- **Why**: Prevents "flickering" where rankings change randomly on each backend run
- **Implementation**: `hash(team_a_name + team_b_name)` - higher hash wins

---

## 8. Firestore Schema Guidelines

### Main Document (Hot Data)
- **Path**: `predictions/latest`
- **Purpose**: Fast frontend reads (single document fetch)
- **Max Size**: Keep under 1MB (Firestore limit)
- **Contents**: Groups, bracket, AI summary, favorites, dark horses

### Sub-collections (Cold Data)
- **Path**: `matches/{match_id}/history/{timestamp}`
- **Purpose**: Historical prediction changes
- **Optimization**: Diff check before writing (only save if prediction changed)

### Diff Check Logic
Before writing to history sub-collection:
1. Fetch latest history entry for match
2. Compare winner AND reasoning
3. If **both unchanged**: skip write (cost optimization)
4. If **either changed**: write new document

---

## 9. Commit Message Conventions

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat: Add new feature`
- `fix: Fix bug`
- `docs: Update documentation`
- `test: Add tests`
- `refactor: Refactor code`
- `chore: Update dependencies`
- `ci: Update CI/CD`

**Examples**:
```
feat(backend): Implement FIFA standings calculation with Fair Play Points
fix(frontend): Prevent flickering by using deterministic tiebreaker
docs(readme): Add Firebase MCP setup instructions
test(fifa-engine): Add test for third-place team ranking
```

---

## 10. Security Guidelines

### Environment Variables
- ✅ Store all secrets in environment variables
- ✅ Use `.env.example` for documentation
- ❌ NEVER commit `.env` or service account keys

### API Keys
- ✅ Rotate API keys regularly
- ✅ Use separate keys for development and production
- ✅ Store in Google Secret Manager for Cloud Run

### Firestore Security Rules
- ✅ Implement read-only access for public website
- ✅ Restrict writes to Cloud Run service account only
- ✅ Validate data schema on write

---

## 11. Deployment Checklist

### Pre-Deployment
- [ ] All tests passing (backend + frontend)
- [ ] Coverage >= 80%
- [ ] Environment variables configured
- [ ] Service accounts have correct permissions
- [ ] API keys have sufficient quotas

### Backend Deployment (Cloud Run)
- [ ] Docker image builds successfully
- [ ] Health endpoint returns 200
- [ ] Firestore writes working
- [ ] Cloud Scheduler configured

### Frontend Deployment (Firebase Hosting)
- [ ] Static export builds successfully
- [ ] All routes accessible
- [ ] Firestore reads working
- [ ] Social meta tags configured

---

## 12. Known Issues & Limitations

### API-Football Free Tier
- **Limit**: 100 requests/day
- **Mitigation**: Aggressive local caching (24-hour TTL)
- **Development**: Use mock data when quota exceeded

### Gemini AI Costs
- **Cost**: ~$0.10 per 104 predictions
- **Mitigation**: 1 retry max, then rule-based fallback
- **Development**: Use mock responses for testing

### Firestore 1MB Limit
- **Risk**: Main document could exceed limit with full history
- **Mitigation**: Use sub-collections for historical predictions
- **Monitoring**: Track document size in health endpoint

---

**Constitution Version**: 1.0
**Last Reviewed**: 2025-12-25
