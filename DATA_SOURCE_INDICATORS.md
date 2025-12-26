# Data Source Indicators

This document explains the visual indicators that show whether data comes from API-Football (real data) or is mock/placeholder data.

## Overview

To help distinguish between real match data from API-Football and test/mock data, we've added visual indicators throughout the UI.

## Visual Badges

### MatchCard Component

Each match card displays a badge indicating the data source:

**Live Data Badge** (Green):
```
🗸 Live
```
- **Color**: Green background with green border
- **Meaning**: Both teams have real data from API-Football
- **Condition**: Both home and away teams have `hasRealData: true`

**Test Data Badge** (Amber):
```
⚠ Test
```
- **Color**: Amber/yellow background with amber border
- **Meaning**: At least one team is using mock/placeholder data
- **Condition**: Either team has `hasRealData: false`

### GroupCard Component

Each group standings table shows a badge in the header:

**Live Data Badge**:
```
🗸 Live Data
```
- **Meaning**: At least one team in the group has real data from API-Football

**Test Data Badge**:
```
⚠ Test Data
```
- **Meaning**: All teams in the group are using mock data

## Backend Implementation

### Data Flow

1. **Database Check**: When loading teams, check if `api_football_id` is present
2. **API Fetch**: If team has `api_football_id`, fetch real data from API-Football
3. **Flag Setting**: Set `has_real_data: true` if data comes from API, `false` otherwise
4. **Propagation**: Flag is included in Firestore snapshot and passed to frontend

### Code Locations

**Backend** (`backend/src/main.py`):
- Lines 447-508: Team stats fetching with `has_real_data` flag
- Lines 532-567: Match predictions with `has_real_data` flag
- Lines 326-342: Group standings with `has_real_data` flag

**Frontend Types** (`frontend/lib/types.ts`):
- `Match.hasRealData?: boolean`
- `TeamStats.hasRealData?: boolean`

**Frontend Components**:
- `frontend/components/MatchCard.tsx`: Lines 148-178 (badges in date/time header)
- `frontend/components/GroupCard.tsx`: Lines 44-68 (badge in group header)

## Current Status

### Teams with Real Data (API-Football ID)

| Team   | API-Football ID | Status |
|--------|-----------------|--------|
| Norway | 1090            | ✅ Live data available |

### Teams with Mock Data

All other teams currently use mock/placeholder data until their `api_football_id` is added to the database.

## Adding Real Data for More Teams

To enable real data for a team:

1. **Find API-Football ID**:
   ```bash
   # Search for team by country
   GET https://v3.football.api-sports.io/teams?country=France
   ```

2. **Update Database**:
   ```sql
   UPDATE teams SET api_football_id = <ID> WHERE fifa_code = '<CODE>';
   ```

3. **Run Prediction Pipeline**:
   ```bash
   POST /api/update-predictions
   ```

4. **Verify Badge**: The "Live" badge should appear for matches involving that team

## Example: Norway's Real Data

When Norway plays against another team:

- **Norway (has real data)** vs **Senegal (mock data)** → **Test Badge** (amber)
- **Norway (has real data)** vs **France (has real data)** → **Live Badge** (green)

## User Experience

The badges help users understand:

1. **Data Quality**: Whether predictions are based on real match statistics
2. **Coverage**: Which teams have been integrated with API-Football
3. **Testing Progress**: Visual feedback on integration progress

## Future Enhancements

Potential improvements:

1. **Tooltip Details**: Show last update time and data source details
2. **Confidence Correlation**: Link data source to prediction confidence
3. **Data Age Indicator**: Show how recent the data is (e.g., "Updated 2 hours ago")
4. **Coverage Percentage**: Show overall percentage of teams with real data

## Accessibility

All badges include:
- **ARIA Labels**: Screen reader-friendly descriptions
- **Color + Icon**: Not relying on color alone (WCAG compliant)
- **High Contrast**: Meets WCAG AA contrast requirements
- **Tooltips**: `title` attribute for additional context
