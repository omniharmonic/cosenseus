# CoSenseus Completion Work Plan

## Executive Summary

This document outlines a comprehensive plan to complete the CoSenseus platform, which is approximately 90% complete. The primary issues identified relate to **LLM JSON parsing**, **frontend-backend data mismatches**, and **API bugs**. This work plan addresses all identified issues with prioritized tasks and implementation details.

## Current State Analysis

### What's Working
- Core event creation and management flow
- Multi-round dialogue structure
- SQLite local database setup
- Frontend React application with visualization components
- Ollama integration (when available)
- Basic AI analysis endpoints

### What's Broken/Incomplete
1. **LLM JSON Parsing Issues** - Ollama responses aren't being parsed reliably
2. **Frontend-Backend Data Mismatch** - TypeScript interfaces don't match API responses
3. **API Bugs** - Several endpoints have bugs preventing proper operation
4. **Missing Database Fields** - Code accesses fields not defined in models
5. **Supabase Lapsed** - Need to ensure local-first SQLite setup is complete

---

## Issue Categories and Fixes

### Category 1: LLM JSON Parsing Issues (HIGH PRIORITY)

These issues cause AI analysis to fail silently or return incomplete data.

#### Issue 1.1: JSON Regex Only Handles Single-Level Nesting
- **File**: `backend/nlp_service/ollama_client.py:74-78`
- **Problem**: Strategy 4's regex `\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}` only handles one level of JSON nesting. LLMs often return deeply nested structures.
- **Fix**: Replace with a recursive brace-matching algorithm or use a more robust regex pattern.

```python
# Current (broken):
json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)

# Fixed approach - use iterative brace counting:
def _extract_nested_json(self, text: str) -> Optional[str]:
    """Extract JSON using brace counting for proper nesting."""
    start = text.find('{')
    if start == -1:
        return None

    depth = 0
    for i, char in enumerate(text[start:], start):
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    return None
```

#### Issue 1.2: No Top-Level Array Handling
- **File**: `backend/nlp_service/ollama_client.py:35-91`
- **Problem**: LLMs sometimes return JSON arrays `[{...}, {...}]` instead of objects `{...}`. Current extraction only looks for `{`.
- **Fix**: Add array detection before object extraction.

```python
# Add to _extract_json_from_response:
# Strategy 0: Check for array response first
if response.strip().startswith('['):
    try:
        result = json.loads(response.strip())
        if isinstance(result, list) and len(result) > 0:
            return result[0] if isinstance(result[0], dict) else {"items": result}
    except json.JSONDecodeError:
        pass
```

#### Issue 1.3: Inconsistent Error Fallbacks
- **File**: `backend/nlp_service/ollama_client.py:475-481`
- **Problem**: The `generate_insights` exception fallback is missing fields the frontend expects.
- **Fix**: Ensure all fallback structures include complete field sets.

```python
# Current fallback (incomplete):
return {
    "key_themes": [],
    "common_concerns": [],
    "suggested_actions": [],
    "participant_sentiment": "neutral",
    "summary": f"Error in insights generation: {e}"
}

# Fixed fallback (complete):
return {
    "key_themes": [],
    "common_concerns": [],
    "suggested_actions": [],
    "consensus_points": [],
    "dialogue_opportunities": [],
    "common_desired_outcomes": [],
    "common_strategies": [],
    "common_values": [],
    "participant_sentiment": "neutral",
    "summary": f"Error in insights generation: {e}"
}
```

#### Issue 1.4: Duplicate JSON Parsing Logic
- **File**: `backend/api-gateway/routers/ai_analysis_local.py:250-265`
- **Problem**: `get_event_summary` duplicates JSON parsing instead of using Ollama client's `_extract_simple_json`.
- **Fix**: Refactor to use the Ollama client's method.

---

### Category 2: Frontend-Backend Data Mismatch (HIGH PRIORITY)

These issues cause TypeScript errors and missing data in the UI.

#### Issue 2.1: SynthesisReview Interface Missing Fields
- **File**: `frontend/src/components/DialogueModeration.tsx:19-28`
- **Problem**: Interface is missing analysis fields that the backend returns.
- **Fix**: Update interface to match backend `SynthesisResponse`:

```typescript
interface SynthesisReview {
  id: string;
  event_id: string;
  round_number: number;
  status: string;
  title?: string;
  content: string;
  summary: string;
  next_round_prompts: Prompt[];
  // Add missing fields:
  key_themes?: string[];
  consensus_points?: string[];
  dialogue_opportunities?: string[];
  consensus_areas?: string[];
  divergent_perspectives?: string[];
  nuanced_positions?: string[];
  common_desired_outcomes?: string[];
  common_strategies?: string[];
  common_values?: string[];
  created_at: string;
  updated_at: string | null;
}
```

#### Issue 2.2: EventAnalysis Interface Structure
- **File**: `frontend/src/components/EventDetails.tsx:35-47`
- **Problem**: The interface may not fully match the actual API response structure.
- **Fix**: Align interface with actual API response.

---

### Category 3: Backend API Bugs (HIGH PRIORITY)

#### Issue 3.1: Wrong Field Name in regenerate_individual_prompt
- **File**: `backend/api-gateway/routers/ai_analysis_local.py:599`
- **Problem**: Uses `request.creativity` but the `RegeneratePromptsRequest` model defines `creativity_level`.
- **Fix**: Change `request.creativity` to `request.creativity_level`.

```python
# Line 599 - Current (broken):
temperature = temperature_map.get(request.creativity, 0.7)

# Fixed:
temperature = temperature_map.get(request.creativity_level, 0.7)
```

#### Issue 3.2: Duplicate SynthesisResponse Models
- **Files**: `events_local.py:121-136` and `ai_analysis_local.py:132-166`
- **Problem**: Two different Pydantic models with the same name but different fields cause confusion.
- **Fix**: Consolidate into a single, complete model or rename to distinguish them.

#### Issue 3.3: Missing regeneration_history Field Access
- **File**: `backend/api-gateway/routers/ai_analysis_local.py:655`
- **Problem**: Code accesses `synthesis.regeneration_history` which isn't defined in the Synthesis database model.
- **Fix**: Either add the field to the database model or remove the code that accesses it.

---

### Category 4: Database/Model Issues (MEDIUM PRIORITY)

#### Issue 4.1: Synthesis Model Missing Fields
- **File**: `backend/shared/models/database.py:320-371`
- **Problem**: The code accesses `prompt_history` and `regeneration_history` but these aren't defined in the model.
- **Fix**: Add these columns to the Synthesis model:

```python
class Synthesis(Base):
    # ... existing fields ...

    # Add these:
    prompt_history = Column(JSON, nullable=True)  # History of prompt regenerations
    regeneration_history = Column(JSON, nullable=True)  # Track regeneration events
```

After adding, create a migration or reset the database.

#### Issue 4.2: Status Field Type Inconsistency
- **Problem**: Synthesis status is stored as string ("draft", "approved", "published") but sometimes compared as if it were an enum.
- **Fix**: Ensure consistent usage throughout the codebase.

---

### Category 5: Supabase/Database Configuration (MEDIUM PRIORITY)

#### Issue 5.1: Free Supabase Lapsed
- **Problem**: The original cloud database is no longer available.
- **Status**: SQLite local-first setup appears complete but should be verified.
- **Fix**:
  1. Verify all endpoints work with SQLite
  2. Remove or comment out Supabase-specific code if any remains
  3. Update documentation to reflect local-first approach

---

### Category 6: Code Quality Issues (LOW PRIORITY)

#### Issue 6.1: Debug Logging in Production Code
- **Problem**: Multiple DEBUG log statements throughout the code.
- **Fix**: Make debug logging configurable via environment variable.

#### Issue 6.2: Inconsistent Error Handling
- **Problem**: Some endpoints use try/catch with proper HTTP errors, others don't.
- **Fix**: Standardize error handling across all endpoints.

---

## Implementation Order

### Phase 1: Critical Fixes (Fix the core LLM flow)

1. **Fix JSON parsing** (Issues 1.1, 1.2)
   - Update `_extract_json_from_response` with proper nesting support
   - Add array handling

2. **Fix API field name bug** (Issue 3.1)
   - Change `request.creativity` to `request.creativity_level`

3. **Update fallback structures** (Issue 1.3)
   - Ensure all Ollama client fallbacks have complete field sets

### Phase 2: Frontend-Backend Alignment

4. **Update TypeScript interfaces** (Issues 2.1, 2.2)
   - Update `SynthesisReview` interface in DialogueModeration
   - Verify EventAnalysis interface matches API

5. **Consolidate SynthesisResponse models** (Issue 3.2)
   - Create single source of truth for synthesis data structure

### Phase 3: Database Model Fixes

6. **Add missing database fields** (Issue 4.1)
   - Add `prompt_history` and `regeneration_history` to Synthesis model
   - Reset or migrate database

7. **Verify SQLite setup** (Issue 5.1)
   - Test all endpoints with local database
   - Clean up any Supabase references

### Phase 4: Code Quality

8. **Standardize error handling** (Issue 6.2)
9. **Make debug logging configurable** (Issue 6.1)
10. **Add missing loading/error states** where needed

---

## Testing Plan

After each phase, test:

1. **Create new event** - Verify event creation works
2. **Add responses** - Submit participant responses
3. **Trigger AI analysis** - Click "End Round & Start Analysis"
4. **Verify synthesis generation** - Check that analysis data appears
5. **Approve synthesis** - Test the moderation flow
6. **Advance to next round** - Verify round progression works

---

## Estimated Effort

| Phase | Issues | Estimated Time |
|-------|--------|---------------|
| Phase 1 | 1.1, 1.2, 1.3, 3.1 | 2-3 hours |
| Phase 2 | 2.1, 2.2, 3.2 | 2-3 hours |
| Phase 3 | 4.1, 5.1 | 1-2 hours |
| Phase 4 | 6.1, 6.2 | 1-2 hours |
| **Total** | | **6-10 hours** |

---

## Files to Modify

### Backend
- `backend/nlp_service/ollama_client.py` - JSON parsing fixes
- `backend/api-gateway/routers/ai_analysis_local.py` - API bug fixes
- `backend/api-gateway/routers/events_local.py` - Remove duplicate models
- `backend/shared/models/database.py` - Add missing fields

### Frontend
- `frontend/src/components/DialogueModeration.tsx` - Update interfaces
- `frontend/src/components/EventDetails.tsx` - Update interfaces
- `frontend/src/components/DialogueRounds.tsx` - Verify data handling

---

## Success Criteria

The platform is considered complete when:

1. A user can create an event with inquiries
2. Participants can submit responses
3. AI analysis runs successfully (or fails gracefully with proper fallback)
4. Admin can review and approve synthesis
5. Dialogue advances to subsequent rounds
6. All visualizations display correctly (cluster map, sentiment timeline, word cloud, consensus graph)
7. Export functionality works
8. No TypeScript errors in the frontend
9. No unhandled Python exceptions in the backend

---

## Notes

- **Ollama Dependency**: The app requires Ollama to be running locally for AI features. When Ollama is unavailable, the fallback logic should work.
- **Local-First**: All data is stored in SQLite at `~/.cosenseus/cosenseus_local.db`
- **Session-Based Auth**: Users are identified by session codes, not email/password
