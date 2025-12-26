# Gemini API Rate Limiting

## Current Issue

Getting 429 (RESOURCE_EXHAUSTED) errors from Gemini API due to rate limits.

## Rate Limits

### gemini-2.0-flash-exp (Current Model)

**Free Tier Limits:**
- **10 requests per minute** (RPM)
- **1,500 requests per day** (RPD)

**Error Message:**
```
429 RESOURCE_EXHAUSTED
You exceeded your current quota. Please migrate to Gemini 2.5 Flash Image 
(models/gemini-2.5-flash-image) for higher quota limits.
```

### Recommended Models

| Model | RPM (Free) | RPD (Free) | Notes |
|-------|------------|------------|-------|
| `gemini-2.0-flash-exp` | 10 | 1,500 | Current (experimental) |
| `gemini-1.5-flash` | 15 | 1,500 | Stable, better limits |
| `gemini-2.5-flash` | Higher | Higher | Recommended by error |

## Current Implementation

### Rate Limiting Strategy

**AIAgent class** (`backend/src/ai_agent.py`):

1. **Minimum Delay**: 6 seconds between requests
   - Ensures we stay under 10 requests/minute
   - Formula: 60 seconds / 10 requests = 6 seconds minimum

2. **429 Error Handling**: 
   - Immediately use rule-based fallback
   - No retry with long wait (avoids blocking pipeline)
   - Logs retry delay from API response

3. **Per-Instance Tracking**:
   - `last_request_time`: Tracks last API call
   - `min_delay`: Minimum seconds between calls (6s)

### Code Changes

```python
class AIAgent:
    def __init__(self):
        self.last_request_time = 0.0
        self.min_delay = 6.0  # 10 requests/min = 1 every 6 seconds
        
    def generate_prediction(self, matchup):
        # Rate limiting before each request
        if self.last_request_time > 0:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_delay:
                time.sleep(self.min_delay - elapsed)
        
        response = self.call_gemini(matchup)
        self.last_request_time = time.time()
```

## Testing Rate Limits

### Calculate Expected Time

For **72 matches** (full tournament):
```
Time = (72 matches × 6 seconds) / 60 = 7.2 minutes minimum
```

With retries and processing:
```
Expected: ~8-10 minutes for full prediction pipeline
```

### Monitor Rate Limit Usage

Watch logs for:
```
Rate limiting: sleeping X.Xs
```

If you see:
```
429 RESOURCE_EXHAUSTED
Rate limit hit for match X, would need to wait 24s. Using fallback instead.
```

This means:
- We hit the 10 req/min limit
- Immediately switched to rule-based prediction
- No long wait/blocking

## Recommendations

### Short Term (Immediate)

1. ✅ **Implemented**: 6-second delay between requests
2. ✅ **Implemented**: Immediate fallback on 429 errors
3. **TODO**: Reduce number of predictions per run (batch by group)

### Medium Term

1. **Switch to `gemini-1.5-flash`**:
   ```python
   self.model_name = "gemini-1.5-flash"  # 15 RPM instead of 10
   ```
   - Stable (not experimental)
   - 50% higher rate limit (15 vs 10 RPM)

2. **Batch Processing**:
   - Process one group at a time
   - Wait between groups
   - Allow user to select which groups to update

### Long Term

1. **Upgrade to Paid Tier**:
   - Gemini API Pro: 360 RPM
   - Cost: $0.075 per 1K requests
   - For 72 matches: ~$0.005 per run

2. **Migrate to `gemini-2.5-flash`**:
   - As recommended by error message
   - Higher quota limits
   - Better performance

3. **Caching Strategy**:
   - Cache predictions for matches
   - Only re-generate when team stats change
   - Reduce redundant API calls

## Current Status

**Rate Limiting**: ✅ ACTIVE (6s delay)  
**429 Handling**: ✅ ACTIVE (immediate fallback)  
**Expected Time**: ~8-10 minutes for 72 predictions

## Testing

Run prediction pipeline and monitor:

```bash
curl -X POST http://localhost:8000/api/update-predictions
```

Check logs for:
- `Rate limiting: sleeping X.Xs` (good - working)
- `Rate limit hit for match X` (429 occurred, using fallback)
- `Gemini prediction SUCCESS` (successful API calls)
- `Rule-based fallback` (fallback predictions)

## Performance Metrics

Track in API response:
- `predictions_generated`: Total predictions
- `gemini_success`: Successful Gemini calls
- `gemini_fallback`: Rule-based fallbacks
- `elapsed_seconds`: Total time

**Good ratio**: >80% gemini_success  
**Acceptable ratio**: >50% gemini_success  
**Poor ratio**: <50% gemini_success (increase delays or upgrade plan)
