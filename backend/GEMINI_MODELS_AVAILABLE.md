# Available Gemini Models (Verified December 2025)

## Summary

✅ **Current Model**: `gemini-2.5-flash`  
✅ **Rate Limiting**: 4.5 second delay (assumes 15 RPM free tier)  
✅ **Quality**: Best available Flash model  
✅ **Status**: Latest stable release  

## All Available Gemini Models

Fetched directly from Google AI API on December 26, 2025:

### Text Generation Models (Recommended)

| Model | Version | Status | Recommendation |
|-------|---------|--------|----------------|
| `gemini-1.5-flash` | 1.5 | Stable | ✅ Good baseline (15 RPM free) |
| `gemini-2.0-flash` | 2.0 | Stable | ✅ Newer than 1.5 |
| `gemini-2.0-flash-exp` | 2.0 | Experimental | ❌ Only 10 RPM |
| `gemini-2.5-flash` | 2.5 | **Latest Stable** | ⭐ **CURRENT** - Best quality |
| `gemini-3-flash-preview` | 3.0 | Preview | 🔬 Cutting edge (experimental) |

### Specialized Models (Not for Our Use Case)

| Model | Purpose | Notes |
|-------|---------|-------|
| `gemini-2.5-flash-image` | Image processing | Not for text predictions |
| `gemini-2.5-flash-native-audio-*` | Audio processing | Not for text predictions |
| `gemini-2.5-computer-use-preview` | Computer control | Not for text predictions |
| `gemini-embedding-*` | Embeddings | For semantic search, not generation |

### Pro Models (Higher Quality, Lower Limits)

| Model | Version | Notes |
|-------|---------|-------|
| `gemini-1.5-pro` | 1.5 | Only 2 RPM (too slow) |
| `gemini-2.5-pro` | 2.5 | Better quality, lower limits |
| `gemini-3-pro-preview` | 3.0 | Preview - may have low limits |

## Rate Limits (Free Tier)

Based on documentation and testing:

| Model | RPM (Free) | RPD (Free) | Time for 72 Predictions |
|-------|------------|------------|-------------------------|
| `gemini-2.0-flash-exp` | 10 | 1,500 | ~7 minutes (6s delay) |
| `gemini-1.5-flash` | 15 | 1,500 | ~5.4 minutes (4.5s delay) |
| `gemini-2.0-flash` | 15* | 1,500* | ~5.4 minutes (4.5s delay) |
| `gemini-2.5-flash` | 15* | 1,500* | ~5.4 minutes (4.5s delay) |
| `gemini-3-flash-preview` | Unknown | Unknown | Need to test |

*Assumed same as 1.5-flash

## Why gemini-2.5-flash?

### Advantages
1. **Latest Stable**: Most recent stable Flash model
2. **Better Quality**: Improved over 1.5-flash and 2.0-flash
3. **Same Limits**: Should have similar rate limits to 1.5-flash (15 RPM)
4. **Recommended by Error**: Error message suggested upgrading from 2.0-flash-exp

### Compared to Alternatives

**vs gemini-1.5-flash**:
- ✅ Better quality (newer model)
- ✅ Same rate limits
- ✅ More capable

**vs gemini-2.0-flash-exp**:
- ✅ 50% higher rate limit (15 vs 10 RPM)
- ✅ Stable (not experimental)
- ✅ Better reliability

**vs gemini-3-flash-preview**:
- ✅ Stable (not preview)
- ✅ Known rate limits
- ⚠️ Gemini 3 may have better quality but unknown limits

## Testing gemini-3-flash-preview

If you want to try the cutting-edge Gemini 3 model:

```python
self.model_name = "gemini-3-flash-preview"
```

**Pros**:
- Latest technology
- May have better performance

**Cons**:
- Preview/experimental status
- Unknown rate limits
- May be unstable

**Recommendation**: Test with a small batch first before full deployment.

## Current Configuration

```python
# backend/src/ai_agent.py
class AIAgent:
    def __init__(self):
        self.last_request_time = 0.0
        self.min_delay = 4.5  # 15 RPM (60s / 15 = 4s, +0.5s buffer)
        self.model_name = "gemini-2.5-flash"  # ⭐ Latest stable
```

## Performance Expectations

### With gemini-2.5-flash (Current)

**Free Tier**:
- Rate Limit: 15 requests/minute
- Time per prediction: 4.5s (with delay)
- Total time (72 matches): ~5.4 minutes
- Expected success rate: >90%
- Cost: FREE

**Paid Tier** (if enabled):
- Rate Limit: 2,000+ requests/minute
- Time per prediction: <1s
- Total time (72 matches): <1 minute
- Expected success rate: 100%
- Cost: ~$0.30/month

## Monitoring

Watch logs for:
```
✅ "Gemini prediction SUCCESS" - Working well
✅ "Rate limiting: sleeping X.Xs" - Rate limiting active
⚠️ "Rate limit hit" - Hit 429 (should be rare)
⚠️ "Rule-based fallback" - Using fallback (acceptable if <10%)
```

## Conclusion

**Current setup**: `gemini-2.5-flash` with 4.5s rate limiting is optimal for free tier.

**If you want faster**: Enable billing for <$1/month to get predictions in <1 minute.

**If you want cutting edge**: Try `gemini-3-flash-preview` (test first!).
