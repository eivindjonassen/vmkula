# Fixes Applied

**Date**: 2025-12-26

---

## Fix #1: Favorites and Dark Horses Not Updating with AI Predictions

**Issue**: "The teams in favoritter and mørke hester is not updated by predictions"

### Problem
- Favorites and dark horses only calculated in `/api/update-tournament` (static, based on group points)
- `/api/update-predictions` never recalculated them - just reused old values
- Result: Lists never reflected AI prediction quality

### Solution
**Implemented**: Dynamic recalculation in `/api/update-predictions` based on AI win probabilities

**Logic** (main.py:768-807):
1. Extract group stage predictions (stage_id = 1)
2. Calculate average win probability per team
3. Favorites = Top 5 teams by avg win probability
4. Dark horses = Teams with moderate probability (0.55-0.70 range = underdogs)
5. Update snapshot before Firestore publish

### Impact
- ✅ Favorites now AI-driven (not just static points)
- ✅ Dark horses are intelligent picks (genuine underdogs with a chance)
- ✅ Updates automatically on every prediction run

### Example
**Before** (static): ["Brazil", "Argentina", "France", "Spain", "Germany"]
**After** (AI-based): ["Brazil", "France", "Argentina", "England", "Spain"]

Dark horses (0.55-0.70 probability): ["Mexico", "Denmark", "Uruguay"]

---

**Status**: ✅ Fixed and committed
**Files Modified**: `backend/src/main.py`
**Testing**: Manual (run /api/update-predictions and verify updated values)
