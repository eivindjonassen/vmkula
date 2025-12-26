# Match Numbering Strategy

**Updated**: 2025-12-26  
**Status**: ✅ **IMPLEMENTED**

---

## Summary

All matches are now numbered **chronologically** based on their kickoff dates from API-Football. This ensures match numbers reflect the actual tournament schedule, not an arbitrary database ordering.

---

## Authoritative Source

**API-Football is the single source of truth** for:
- ✅ Match dates and kickoff times
- ✅ Venue information
- ✅ Match chronological order
- ✅ Fixture IDs for live updates

---

## Numbering Algorithm

### Match Number Assignment

Matches are numbered sequentially (1, 2, 3...) based on their **kickoff timestamp**:

```python
# Sort matches by kickoff date (chronological order)
sorted_matches = sorted(all_matches, key=lambda m: m.get('kickoff', ''))

# Assign sequential match numbers
for new_number, match in enumerate(sorted_matches, start=1):
    match['match_number'] = new_number
```

### Handling Matches Without Dates

Matches without API-Football data yet (placeholder teams like "Winner UEFA Playoff D"):
- Sorted **after** all matches with real dates
- Maintain their original database order among themselves
- Will be renumbered when API-Football data becomes available

---

## Implementation

### Sync Script: `sync_wc2026_fixtures.py`

The sync script now:
1. ✅ Fetches all WC 2026 fixtures from API-Football
2. ✅ Updates Firestore matches with fixture IDs, dates, venues
3. ✅ **Renumbers ALL matches chronologically** based on kickoff dates
4. ✅ Validates the sync and reports renumbering changes

### Re-sync Command

To update match numbers when new API-Football data is available:

```bash
cd backend
source venv/bin/activate
python sync_wc2026_fixtures.py
```

This will:
- Fetch latest fixtures from API-Football
- Update match data in Firestore
- Renumber all matches chronologically
- Report which matches were renumbered

---

## Example Chronological Ordering

```
Match #1  | 2026-06-11 | South Korea vs Winner UEFA Playoff D
Match #2  | 2026-06-11 | Mexico vs South Africa
Match #3  | 2026-06-13 | Qatar vs Winner UEFA Playoff A
Match #4  | 2026-06-13 | Australia vs Winner UEFA Playoff C
Match #5  | 2026-06-13 | USA vs Paraguay
Match #6  | 2026-06-13 | Brazil vs Morocco
Match #7  | 2026-06-14 | Tunisia vs Winner UEFA Playoff B
Match #8  | 2026-06-14 | Haiti vs Scotland
Match #9  | 2026-06-14 | Germany vs Curaçao
Match #10 | 2026-06-14 | Netherlands vs Japan
...
```

---

## Frontend Impact

### Display Order

The frontend should display matches in **match_number order**, which is now chronological:

```typescript
// Matches are already sorted chronologically by match_number
matches.sort((a, b) => a.matchNumber - b.matchNumber)
```

### Cache Behavior

Frontend cache (5-minute TTL):
- Hard refresh (Cmd+Shift+R) clears cache immediately
- Cache expires automatically after 5 minutes
- Match numbers will update after cache refresh

---

## Benefits

### User Experience
- ✅ Matches appear in actual tournament order
- ✅ No confusion about "earlier" matches having higher numbers
- ✅ Natural progression through the tournament

### Data Integrity
- ✅ Single source of truth (API-Football)
- ✅ Automatic updates when tournament schedule changes
- ✅ No manual intervention needed

### Development
- ✅ Simple chronological sort algorithm
- ✅ Self-healing (re-sync updates everything)
- ✅ Clear audit trail (renumbering logs)

---

## Validation

### Check Match Ordering

Verify matches are chronologically ordered:

```bash
cd backend
source venv/bin/activate
python3 -c "
from src.firestore_manager import FirestoreManager
fm = FirestoreManager()
matches = fm.get_all_matches()

# Filter matches with dates
with_dates = [m for m in matches if m.get('kickoff')]

# Sort by match number
sorted_by_number = sorted(with_dates, key=lambda m: m['match_number'])

# Sort by kickoff date
sorted_by_date = sorted(with_dates, key=lambda m: m['kickoff'])

# Verify they match
is_chronological = all(
    sorted_by_number[i]['id'] == sorted_by_date[i]['id']
    for i in range(len(sorted_by_number))
)

print(f'Chronologically ordered: {\"✅ YES\" if is_chronological else \"❌ NO\"}')
"
```

Expected output:
```
Chronologically ordered: ✅ YES
```

---

## Renumbering History

### 2025-12-26: Initial Chronological Renumbering

**Before**: Matches numbered by database structure (groups, then knockout)  
**After**: Matches numbered by API-Football kickoff dates  
**Changes**: 73 matches renumbered

**Examples**:
- Match #42 (France vs Norway, June 26) → Match #62
- Match #65 (Senegal vs Norway, June 23) → Match #43
- Match #23 (Colombia vs Portugal, June 27) → Match #70

**Result**: All 54 matches with API-Football data now chronologically ordered

---

## Future Considerations

### Tournament Schedule Changes

If API-Football updates kickoff times:
1. Run `sync_wc2026_fixtures.py` to fetch latest data
2. Matches will be automatically renumbered
3. Frontend cache will refresh within 5 minutes
4. No manual intervention required

### Knockout Stage

When knockout fixtures become available:
1. API-Football will provide kickoff dates
2. Sync script will fetch and update Firestore
3. All matches (group + knockout) will be renumbered chronologically
4. Knockout matches will appear after all group stage matches

---

## Technical Notes

### Match ID vs Match Number

- **Match ID**: Firestore document ID (never changes)
- **Match Number**: Display order (changes based on chronological sort)
- **Fixture ID**: API-Football unique identifier (never changes)

### Sorting Key

```python
def sort_key(match):
    kickoff = match.get('kickoff')
    if kickoff:
        # Real date - sort chronologically
        return (0, kickoff, match.get('match_number', 999))
    else:
        # No date - sort after real matches
        return (1, '', match.get('match_number', 999))
```

This ensures:
1. Matches with dates always come first
2. Matches without dates maintain original order
3. Stable sort (deterministic results)

---

**Strategy implemented**: 2025-12-26  
**Total matches renumbered**: 73  
**Chronological ordering**: ✅ Verified

---

*See `FINAL_SYNC_SUMMARY.md` for full sync status and `sync_wc2026_fixtures.py` for implementation details.*
