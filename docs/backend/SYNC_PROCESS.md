# API-Football Sync Process

**Created**: 2025-12-27  
**Purpose**: Documentation for syncing teams and fixtures from API-Football to Firestore

---

## Overview

The API-Football sync process synchronizes tournament data (teams and fixtures) from the API-Football external API into Firestore. It includes:

- **Raw API response storage** for audit trail and rollback capability
- **Change detection** to identify differences between API data and Firestore data
- **Conflict resolution** to handle manual overrides gracefully
- **Backward compatibility** to work with existing Firestore documents

---

## Sync Endpoint Usage

### POST /api/sync-api-football

Syncs teams or fixtures from API-Football to Firestore.

**Request Body**:
```json
{
  "entity_type": "teams",
  "league_id": 1,
  "season": 2026,
  "force_update": false
}
```

**Parameters**:
- `entity_type` (string, required): `"teams"` or `"fixtures"`
- `league_id` (int, required): API-Football league ID
- `season` (int, required): Season year (e.g., 2026)
- `force_update` (bool, optional): If `true`, override manual changes with API data. Default: `false`

**Response** (Success):
```json
{
  "status": "success",
  "entity_type": "teams",
  "entities_added": 2,
  "entities_updated": 46,
  "entities_unchanged": 0,
  "conflicts_detected": 0,
  "conflicts_resolved": 0,
  "changes_detected": 48,
  "raw_document_id": "teams_1_2026",
  "synced_at": "2026-06-01T10:00:00Z",
  "errors": null
}
```

**Response** (Partial Success with Conflicts):
```json
{
  "status": "partial_success",
  "entity_type": "fixtures",
  "entities_added": 5,
  "entities_updated": 95,
  "entities_unchanged": 4,
  "conflicts_detected": 2,
  "conflicts_resolved": 0,
  "changes_detected": 100,
  "raw_document_id": "fixtures_1_2026",
  "synced_at": "2026-06-01T10:00:00Z",
  "errors": [
    "Conflict detected: Match 1 has manual override"
  ]
}
```

**Response** (Error):
```json
{
  "status": "error",
  "entity_type": "teams",
  "entities_added": 0,
  "entities_updated": 0,
  "entities_unchanged": 0,
  "conflicts_detected": 0,
  "conflicts_resolved": 0,
  "changes_detected": 0,
  "raw_document_id": "",
  "synced_at": "2026-06-01T10:00:00Z",
  "errors": [
    "API-Football rate limit exceeded"
  ]
}
```

---

## Request Examples

### Using curl

**Sync Teams**:
```bash
curl -X POST https://your-backend-url.run.app/api/sync-api-football \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "teams",
    "league_id": 1,
    "season": 2026,
    "force_update": false
  }'
```

**Sync Fixtures**:
```bash
curl -X POST https://your-backend-url.run.app/api/sync-api-football \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "fixtures",
    "league_id": 1,
    "season": 2026,
    "force_update": false
  }'
```

**Force Update (Override Manual Changes)**:
```bash
curl -X POST https://your-backend-url.run.app/api/sync-api-football \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "teams",
    "league_id": 1,
    "season": 2026,
    "force_update": true
  }'
```

### Using Python requests

```python
import requests

# Sync teams
response = requests.post(
    "https://your-backend-url.run.app/api/sync-api-football",
    json={
        "entity_type": "teams",
        "league_id": 1,
        "season": 2026,
        "force_update": False
    }
)

result = response.json()
print(f"Status: {result['status']}")
print(f"Entities added: {result['entities_added']}")
print(f"Entities updated: {result['entities_updated']}")
print(f"Conflicts detected: {result['conflicts_detected']}")

# Sync fixtures with force update
response = requests.post(
    "https://your-backend-url.run.app/api/sync-api-football",
    json={
        "entity_type": "fixtures",
        "league_id": 1,
        "season": 2026,
        "force_update": True
    }
)

result = response.json()
print(f"Status: {result['status']}")
print(f"Changes detected: {result['changes_detected']}")
```

---

## Conflict Resolution Workflow

### When Do Conflicts Occur?

Conflicts occur when:
1. A team or fixture has the `manual_override` flag set to `true` in Firestore
2. The API-Football data for that entity has changed since the last sync
3. The sync is run with `force_update=false` (default)

**Example Conflict Scenario**:
```
1. Team "Mexico" is synced from API-Football with name "Mexico"
2. Admin manually edits team name to "México" in Firestore and sets manual_override=true
3. API-Football updates team name to "Mexico National Team"
4. Next sync detects conflict: Firestore="México", API="Mexico National Team"
5. If force_update=false: Conflict logged, manual override preserved
6. If force_update=true: API value applied, manual_override flag cleared
```

### How to Review Sync Conflicts

**Step 1: Check sync response for conflicts**
```bash
curl -X POST https://your-backend-url.run.app/api/sync-api-football \
  -H "Content-Type: application/json" \
  -d '{"entity_type": "teams", "league_id": 1, "season": 2026}'
```

Look for `conflicts_detected > 0` in the response.

**Step 2: Inspect team/match document in Firestore**

Teams with conflicts will have the `sync_conflicts` field populated:

```json
{
  "id": 1,
  "name": "México",
  "manual_override": true,
  "sync_conflicts": [
    {
      "field": "name",
      "firestore_value": "México",
      "api_value": "Mexico National Team",
      "detected_at": "2026-06-01T10:00:00Z"
    }
  ]
}
```

**Step 3: Review conflict details**

The `sync_conflicts` array contains:
- `field`: Field name with conflicting data
- `firestore_value`: Current value in Firestore (manually overridden)
- `api_value`: New value from API-Football
- `detected_at`: Timestamp of conflict detection

### How to Resolve Conflicts Manually

**Option 1: Preserve Manual Override**

If you want to keep the manual changes, do nothing. The `manual_override=true` flag will continue to protect your changes.

**Option 2: Accept API-Football Update**

If you want to accept the API-Football data:

1. Update the team/match document in Firestore with the API value
2. Set `manual_override=false`
3. Clear the `sync_conflicts` array

**Using Firebase Console**:
```
1. Navigate to Firestore → teams → {team_id}
2. Edit the field with the conflict (e.g., name: "Mexico National Team")
3. Set manual_override: false
4. Clear sync_conflicts: []
5. Save
```

**Using Python Admin SDK**:
```python
from google.cloud import firestore

db = firestore.Client()

# Accept API-Football update for team 1
db.collection('teams').document('1').update({
    'name': 'Mexico National Team',
    'manual_override': False,
    'sync_conflicts': []
})
```

**Option 3: Force Update via Sync**

Run the sync with `force_update=true` to override ALL manual changes:

```bash
curl -X POST https://your-backend-url.run.app/api/sync-api-football \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "teams",
    "league_id": 1,
    "season": 2026,
    "force_update": true
  }'
```

**⚠️ Warning**: This will clear all `manual_override` flags and apply API data to ALL entities, not just conflicted ones.

---

## Troubleshooting

### Common Errors and Solutions

#### 1. "API-Football rate limit exceeded"

**Cause**: API-Football free tier limit (100 requests/day) exceeded.

**Solution**:
- Wait 24 hours for rate limit reset
- Upgrade to paid API-Football tier
- Use cached data from `api_football_raw` collection

**How to Check Rate Limit**:
```bash
# API-Football rate limit resets at midnight UTC
# Check current time vs last sync time in raw collection
```

#### 2. "Invalid entity_type"

**Cause**: Invalid `entity_type` in request (must be `"teams"` or `"fixtures"`).

**Solution**:
```bash
# Correct entity types
curl -X POST https://your-backend-url.run.app/api/sync-api-football \
  -d '{"entity_type": "teams", "league_id": 1, "season": 2026}'

# OR
curl -X POST https://your-backend-url.run.app/api/sync-api-football \
  -d '{"entity_type": "fixtures", "league_id": 1, "season": 2026}'
```

#### 3. "Firestore permission denied"

**Cause**: Service account lacks Firestore write permissions.

**Solution**:
```bash
# Grant Firestore User role to service account
gcloud projects add-iam-policy-binding [PROJECT_ID] \
  --member=serviceAccount:[SERVICE_ACCOUNT_EMAIL] \
  --role=roles/datastore.user
```

#### 4. "Team/fixture not found in API-Football"

**Cause**: League ID or season is incorrect.

**Solution**:
- Verify league ID via API-Football documentation
- Check season year matches tournament year
- For World Cup 2026, use league_id for FIFA World Cup

#### 5. "Sync completed but entities_updated=0"

**Cause**: No changes detected (API data matches Firestore data).

**Solution**: This is expected behavior when data hasn't changed. No action needed.

### How to Rollback Using Raw Collection

If a sync introduces bad data, you can rollback by re-running the sync from the previous raw response:

**Step 1: Find previous raw response**

```python
from google.cloud import firestore

db = firestore.Client()

# Get all raw responses for teams, sorted by fetched_at
raw_docs = db.collection('api_football_raw') \
    .where('entity_type', '==', 'teams') \
    .order_by('fetched_at', direction=firestore.Query.DESCENDING) \
    .limit(5) \
    .stream()

for doc in raw_docs:
    data = doc.to_dict()
    print(f"Document ID: {doc.id}, Fetched: {data['fetched_at']}")
```

**Step 2: Manually restore from raw response**

```python
# Get the raw response you want to restore from
raw_doc_id = "teams_1_2026_backup"  # Use appropriate document ID
raw_doc = db.collection('api_football_raw').document(raw_doc_id).get()
raw_response = raw_doc.to_dict()['raw_response']

# Extract teams from raw response
teams = raw_response.get('response', [])

# Update Firestore teams collection
for team_data in teams:
    team_info = team_data['team']
    team_id = team_info['id']
    
    db.collection('teams').document(str(team_id)).update({
        'name': team_info['name'],
        'api_football_raw_id': raw_doc_id,
        'last_synced_at': firestore.SERVER_TIMESTAMP,
        'manual_override': False,
        'sync_conflicts': []
    })
    
print(f"Restored {len(teams)} teams from {raw_doc_id}")
```

**Step 3: Verify restoration**

```bash
# Run sync again to check for differences
curl -X POST https://your-backend-url.run.app/api/sync-api-football \
  -d '{"entity_type": "teams", "league_id": 1, "season": 2026}'
```

### How to Replay Sync from Raw Data

The sync process stores raw API responses in the `api_football_raw` collection. You can replay the sync from stored raw data without calling the API again:

**Note**: The current implementation always fetches fresh data from API-Football. To replay from raw data, you would need to modify `api_football_sync.py` to accept a `use_cached_raw=true` parameter. This is a potential future enhancement.

---

## Usage Examples

### Initial World Cup 2026 Data Sync

**Step 1: Sync Teams**
```bash
# Sync all World Cup 2026 teams
curl -X POST https://your-backend-url.run.app/api/sync-api-football \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "teams",
    "league_id": 1,
    "season": 2026,
    "force_update": false
  }'
```

**Expected Result**:
```json
{
  "status": "success",
  "entities_added": 48,
  "entities_updated": 0,
  "entities_unchanged": 0
}
```

**Step 2: Sync Fixtures**
```bash
# Sync all World Cup 2026 fixtures
curl -X POST https://your-backend-url.run.app/api/sync-api-football \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "fixtures",
    "league_id": 1,
    "season": 2026,
    "force_update": false
  }'
```

**Expected Result**:
```json
{
  "status": "success",
  "entities_added": 104,
  "entities_updated": 0,
  "entities_unchanged": 0
}
```

### Periodic Fixture Updates

**Use Case**: During the tournament, fixture data changes (scores, status, etc.)

```bash
# Daily fixture sync (run via Cloud Scheduler)
curl -X POST https://your-backend-url.run.app/api/sync-api-football \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "fixtures",
    "league_id": 1,
    "season": 2026,
    "force_update": false
  }'
```

**Expected Result**:
```json
{
  "status": "success",
  "entities_added": 0,
  "entities_updated": 12,
  "entities_unchanged": 92
}
```

**Note**: Only changed fixtures are updated, reducing API calls and processing time.

### Historical Tournament Data Sync

**Use Case**: Import data from past World Cups for analysis

```bash
# Sync 2022 World Cup teams
curl -X POST https://your-backend-url.run.app/api/sync-api-football \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "teams",
    "league_id": 1,
    "season": 2022,
    "force_update": false
  }'

# Sync 2022 World Cup fixtures
curl -X POST https://your-backend-url.run.app/api/sync-api-football \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "fixtures",
    "league_id": 1,
    "season": 2022,
    "force_update": false
  }'
```

**Note**: Historical data may have different API-Football IDs. Ensure your Firestore schema supports multiple tournaments if importing historical data alongside 2026 data.

---

## Best Practices

1. **Run Team Sync Before Fixture Sync**: Teams must exist before fixtures can reference them via `api_football_id`.

2. **Use `force_update=false` by Default**: This preserves manual overrides and prevents accidental data loss.

3. **Monitor Conflicts Regularly**: Check `conflicts_detected` in sync responses and review `sync_conflicts` fields in Firestore.

4. **Schedule Regular Syncs**: Use Cloud Scheduler to run daily fixture syncs during the tournament to capture score updates.

5. **Archive Raw Responses**: The `api_football_raw` collection grows over time. Consider implementing a retention policy (e.g., keep last 30 days).

6. **Test with `force_update=true` Carefully**: Always test force updates on a staging environment before running in production.

7. **Handle Rate Limits Gracefully**: If approaching API-Football rate limits, increase cache TTL or reduce sync frequency.

---

## Related Documentation

- **Data Model**: See `backend/docs/data-model.md` for full schema details
- **API Documentation**: See `backend/docs/api.md` for all API endpoints
- **Deployment Guide**: See `backend/DEPLOYMENT.md` for Cloud Run deployment

---

**End of Sync Process Documentation**
