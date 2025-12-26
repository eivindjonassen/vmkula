# API-Football Integration Setup Guide

## Overview

This guide explains how to set up API-Football integration to fetch real match data and upcoming fixtures for World Cup 2026 teams.

## Database Schema Changes

### Teams Table

Added `api_football_id` column to the `teams` table to map internal team IDs to API-Football team IDs:

```sql
ALTER TABLE teams ADD COLUMN api_football_id INTEGER;
```

### Norway Setup (Testing)

For testing purposes, Norway's API-Football team ID has been configured:

```sql
UPDATE teams SET api_football_id = 1090 WHERE team_name = 'Norway';
```

**Note**: The correct Norway national team ID is **1090**, not 772 (which is Ukraine).

## API-Football Team ID Mapping

To enable real data fetching for teams, you need to add their API-Football team IDs. Here's how to find them:

### Finding Team IDs

1. Visit [API-Football Documentation](https://www.api-football.com/documentation-v3#tag/Teams)
2. Use the `/teams` endpoint with country parameter:
   ```
   GET https://v3.football.api-sports.io/teams?country=Norway
   ```
3. The response will include the team ID

### Common National Team IDs

Here are some common national team IDs for World Cup 2026:

| Team          | API-Football ID | FIFA Code |
|---------------|-----------------|-----------|
| Norway        | 1090            | NOR       |
| England       | 10              | ENG       |
| France        | 2               | FRA       |
| Germany       | 25              | GER       |
| Spain         | 9               | ESP       |
| Brazil        | 6               | BRA       |
| Argentina     | 26              | ARG       |
| USA           | 2384            | USA       |
| Mexico        | 16              | MEX       |
| Canada        | 1118            | CAN       |
| Senegal       | 13              | SEN       |

### Adding Team IDs to Database

```sql
-- Example: Add England
UPDATE teams SET api_football_id = 10 WHERE fifa_code = 'ENG';

-- Example: Add France
UPDATE teams SET api_football_id = 2 WHERE fifa_code = 'FRA';

-- Bulk update (run individual UPDATEs for each team)
```

## Usage

### Fetching Team Statistics (Past 5 Matches)

```python
from src.data_aggregator import DataAggregator

aggregator = DataAggregator()

# Fetch team stats (uses cache if available)
stats = aggregator.fetch_team_stats(team_id=1090)  # Norway

print(stats)
# Output:
# {
#     'avg_xg': None,  # May be None for free tier
#     'clean_sheets': 1,
#     'form_string': 'W-W-D-W-W',
#     'data_completeness': 0.0,
#     'confidence': 'low',
#     'fallback_mode': 'traditional_form'
# }
```

### Fetching Past and Upcoming Fixtures

**Important**: The API-Football API does not support using `last` and `next` parameters together. The `fetch_team_fixtures` method automatically makes **two separate API calls** to retrieve both past and upcoming fixtures.

```python
from src.data_aggregator import DataAggregator

aggregator = DataAggregator()

# Fetch both past and upcoming fixtures (makes 2 API calls internally)
fixtures = aggregator.fetch_team_fixtures(
    team_id=1090,  # Norway
    last=5,        # Last 5 completed matches
    next=5         # Next 5 upcoming matches
)

print(f"Total fixtures: {fixtures['total_count']}")
print(f"Past: {len(fixtures['past_fixtures'])}")
print(f"Upcoming: {len(fixtures['upcoming_fixtures'])}")

# Access past fixtures
for match in fixtures['past_fixtures']:
    home = match['home_team']['name']
    away = match['away_team']['name']
    score = f"{match['goals']['home']}-{match['goals']['away']}"
    date = match['date'][:10]
    league = match['league']
    print(f"[{match['status']}] {date}: {home} {score} {away} - {league}")

# Access upcoming fixtures
for match in fixtures['upcoming_fixtures']:
    home = match['home_team']['name']
    away = match['away_team']['name']
    date = match['date'][:10]
    venue = match['venue']
    league = match['league']
    print(f"[{match['status']}] {date}: {home} vs {away}")
    print(f"  Venue: {venue}, Competition: {league}")
```

**Example Output** (Norway - December 2025):
```
Total fixtures: 7
Past: 5
Upcoming: 2

[FT] 2025-11-16: Italy 1-4 Norway - World Cup - Qualification Europe
[FT] 2025-11-13: Norway 4-1 Estonia - World Cup - Qualification Europe
[FT] 2025-10-14: Norway 1-1 New Zealand - Friendlies
[FT] 2025-10-11: Norway 5-0 Israel - World Cup - Qualification Europe
[FT] 2025-09-09: Norway 11-1 Moldova - World Cup - Qualification Europe

[NS] 2026-06-23: Norway vs Senegal
  Venue: MetLife Stadium, Competition: World Cup
[NS] 2026-06-26: Norway vs France
  Venue: Gillette Stadium, Competition: World Cup
```

## Testing the Integration

### Run Norway Integration Test

```bash
cd backend
source venv/bin/activate
python test_norway_integration.py
```

Expected output:
```
================================================================================
NORWAY API-FOOTBALL INTEGRATION TEST
================================================================================

✓ API Key configured: 4aa3dd1bdd...

✓ Norway loaded from database
  Internal ID: 36
  FIFA Code: NOR
  Group: I
  API-Football ID: 772

--------------------------------------------------------------------------------
TEST 1: Fetching Norway team statistics (last 5 matches)
--------------------------------------------------------------------------------
✅ SUCCESS! Team statistics fetched

--------------------------------------------------------------------------------
TEST 2: Fetching Norway fixtures (last 5 + next 5)
--------------------------------------------------------------------------------
✅ SUCCESS! Fixtures fetched

================================================================================
✅ NORWAY API-FOOTBALL INTEGRATION TEST PASSED!
================================================================================
```

### Run Unit Tests

```bash
cd backend
source venv/bin/activate
pytest tests/test_data_aggregator.py -v
pytest tests/test_db_manager.py -v
```

## API Rate Limiting

### Upgraded Plan Features

✅ **`last` parameter**: Fetch recent completed matches
✅ **`next` parameter**: Fetch upcoming scheduled matches
✅ **Higher request limits**: More generous daily quota
✅ **Current season access**: Access to 2024+ data

**Important Limitation**: Cannot use `last` and `next` together in a single request. The `fetch_team_fixtures()` method handles this by making **2 separate API calls**.

### API Call Cost

| Operation | API Calls | Description |
|-----------|-----------|-------------|
| `fetch_team_stats(team_id)` | 1 | Last 5 matches only |
| `fetch_team_fixtures(team_id, last=5)` | 1 | Past fixtures only |
| `fetch_team_fixtures(team_id, next=5)` | 1 | Upcoming fixtures only |
| `fetch_team_fixtures(team_id, last=5, next=5)` | **2** | Both past and upcoming |

### Rate Limiting

- **0.5 second delay between requests** (enforced in code)
- **Retry strategy**: Exponential backoff (1s, 2s, 4s) on 429/5xx errors

### Caching Strategy

To minimize API requests:

1. **Local cache**: All API responses are cached in `backend/cache/`
2. **TTL**: 24 hours (expires when date changes)
3. **Cache hit**: Skip API call entirely
4. **Cache miss**: Fetch from API and save to cache

### Staying Within Limits

For **testing with Norway only**:

- 1 request = team stats (last 5 matches)
- 2 requests = fixtures (last 5 + next 5, requires separate calls)
- **Total per team**: 3 requests

**Recommendation**: With the upgraded plan, you can test with multiple teams. Monitor your quota usage via the API-Football dashboard.

## Next Steps

1. **Add more team IDs**: Update the database with API-Football IDs for all World Cup 2026 teams
2. **Update prediction pipeline**: Modify `/api/update-predictions` endpoint to use real fixture data
3. **Batch processing**: Implement team selection to limit API calls (e.g., only teams with upcoming matches)
4. **Production deployment**: Switch to paid API-Football tier for higher rate limits

## Troubleshooting

### "No fixtures found" for Norway

This is expected - Norway may not have recent international matches in the API-Football database. The integration is working correctly, but the response is empty.

**Solution**: Test with a club team instead (e.g., Manchester United, team_id=33) or wait for Norway's next international match window.

### Rate Limit Exceeded (429 Error)

```
APIRateLimitError: Rate limit exceeded for team 772
```

**Solution**:
1. Wait 24 hours for the API quota to reset
2. Use cached data if available
3. Reduce the number of teams being fetched

### Missing API-Football ID

```
ERROR: Norway missing API-Football ID in database
```

**Solution**:
```sql
UPDATE teams SET api_football_id = 772 WHERE team_name = 'Norway';
```

## Resources

- [API-Football Documentation](https://www.api-football.com/documentation-v3)
- [API-Football Team Search](https://www.api-football.com/documentation-v3#tag/Teams/operation/get-teams)
- [API-Football Fixtures](https://www.api-football.com/documentation-v3#tag/Fixtures)
- [Rate Limiting Guide](https://www.api-football.com/documentation-v3#section/Rate-limiting)
