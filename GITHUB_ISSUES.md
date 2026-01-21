# GitHub Issues for CoSenseus

This document contains all the issues to be created in the GitHub repository. Each section represents a single issue.

---

## Issue 1: Fix JSON parsing to handle deeply nested structures

**Labels**: `bug`, `high-priority`, `backend`, `ai`

### Description

The JSON extraction logic in `ollama_client.py` fails to properly parse deeply nested JSON structures that LLMs often return.

### Problem

The regex in Strategy 4 (`\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}`) only handles one level of nesting. When Ollama returns JSON with deeper nesting (common in analysis responses), the parsing fails silently and uses fallback data.

### Location

- File: `backend/nlp_service/ollama_client.py`
- Lines: 74-78

### Expected Behavior

JSON responses with any level of nesting should be parsed correctly.

### Proposed Solution

Replace the regex-based extraction with a brace-counting algorithm:

```python
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

### Acceptance Criteria

- [ ] JSON with 3+ levels of nesting parses correctly
- [ ] Existing tests continue to pass
- [ ] Fallback behavior still works when JSON is malformed

---

## Issue 2: Add JSON array response handling

**Labels**: `bug`, `high-priority`, `backend`, `ai`

### Description

LLMs sometimes return JSON arrays `[{...}, {...}]` instead of objects `{...}`. The current extraction logic only looks for `{` as the start of JSON.

### Problem

When Ollama returns an array response, the extraction fails because it expects an object.

### Location

- File: `backend/nlp_service/ollama_client.py`
- Lines: 35-91 (entire `_extract_json_from_response` method)

### Expected Behavior

Array responses should be handled, either by:
1. Extracting the first object from the array
2. Wrapping the array in an object `{"items": [...]}`

### Proposed Solution

Add array detection at the beginning of the extraction:

```python
# Add to _extract_json_from_response before Strategy 1:
# Strategy 0: Check for array response first
stripped = response.strip()
if stripped.startswith('['):
    try:
        result = json.loads(stripped)
        if isinstance(result, list) and len(result) > 0:
            if isinstance(result[0], dict):
                return result[0]
            return {"items": result}
    except json.JSONDecodeError:
        pass
```

### Acceptance Criteria

- [ ] Array responses like `[{"key": "value"}]` are handled
- [ ] Empty arrays return appropriate fallback
- [ ] Mixed content arrays work correctly

---

## Issue 3: Fix wrong field name in regenerate_individual_prompt endpoint

**Labels**: `bug`, `critical`, `backend`

### Description

The `regenerate_individual_prompt` endpoint uses `request.creativity` but the Pydantic model defines `creativity_level`, causing the endpoint to fail.

### Problem

```python
# Line 599 - Bug:
temperature = temperature_map.get(request.creativity, 0.7)
# Should be:
temperature = temperature_map.get(request.creativity_level, 0.7)
```

### Location

- File: `backend/api-gateway/routers/ai_analysis_local.py`
- Line: 599

### Expected Behavior

The endpoint should correctly read the `creativity_level` field from the request.

### Proposed Solution

Change `request.creativity` to `request.creativity_level`.

### Acceptance Criteria

- [ ] Endpoint works with all creativity levels: conservative, moderate, creative
- [ ] No AttributeError when regenerating prompts

---

## Issue 4: Complete fallback structures in Ollama client

**Labels**: `bug`, `backend`, `ai`

### Description

Error fallbacks in the Ollama client are missing fields that the frontend expects, causing incomplete data to be displayed.

### Problem

When an Ollama call fails, the fallback dictionary doesn't include all fields:

```python
# Current fallback (incomplete):
return {
    "key_themes": [],
    "common_concerns": [],
    "suggested_actions": [],
    "participant_sentiment": "neutral",
    "summary": f"Error: {e}"
}
```

Missing: `consensus_points`, `dialogue_opportunities`, `common_desired_outcomes`, `common_strategies`, `common_values`

### Location

- File: `backend/nlp_service/ollama_client.py`
- Lines: 475-481 (`generate_insights` exception handler)
- Lines: 549-551 (`generate_round_insights` exception handler)

### Expected Behavior

Fallback structures should include all fields the frontend expects.

### Proposed Solution

Update all fallback structures to include complete field sets:

```python
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
    "summary": f"Error: {e}"
}
```

### Acceptance Criteria

- [ ] All fallback structures include all expected fields
- [ ] Frontend doesn't show undefined/null for any analysis field

---

## Issue 5: Update SynthesisReview TypeScript interface

**Labels**: `bug`, `frontend`, `typescript`

### Description

The `SynthesisReview` interface in `DialogueModeration.tsx` is missing fields that the backend API returns.

### Problem

The interface only has basic fields but the backend returns analysis fields (`key_themes`, `consensus_points`, etc.) that the frontend should display.

### Location

- File: `frontend/src/components/DialogueModeration.tsx`
- Lines: 19-28

### Expected Behavior

The interface should include all fields returned by the `/ai/synthesis-review/{event_id}/{round_number}` endpoint.

### Proposed Solution

Update the interface:

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
  // Analysis fields:
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

### Acceptance Criteria

- [ ] No TypeScript errors related to synthesis data
- [ ] Analysis fields can be displayed in the moderation UI

---

## Issue 6: Add missing database columns for prompt tracking

**Labels**: `enhancement`, `backend`, `database`

### Description

The code tries to access `prompt_history` and `regeneration_history` on the Synthesis model, but these columns don't exist.

### Problem

Lines in `ai_analysis_local.py` access:
- `synthesis.prompt_history` (line 505-512)
- `synthesis.regeneration_history` (line 655)

But these fields aren't defined in the Synthesis model in `database.py`.

### Location

- File: `backend/shared/models/database.py` (model definition)
- File: `backend/api-gateway/routers/ai_analysis_local.py` (usage)

### Expected Behavior

Either:
1. Add the columns to the Synthesis model
2. Remove the code that tries to use them

### Proposed Solution

Add the columns to the Synthesis model:

```python
class Synthesis(Base):
    # ... existing fields ...

    # Prompt regeneration tracking
    prompt_history = Column(JSON, nullable=True)
    regeneration_history = Column(JSON, nullable=True)
```

### Acceptance Criteria

- [ ] No AttributeError when regenerating prompts
- [ ] Prompt history is saved and can be viewed

---

## Issue 7: Consolidate duplicate SynthesisResponse Pydantic models

**Labels**: `refactoring`, `backend`

### Description

There are two different `SynthesisResponse` Pydantic models with different fields, causing confusion and potential bugs.

### Problem

- `events_local.py:121-136` - Minimal fields (id, round_number, content, created_at)
- `ai_analysis_local.py:132-166` - Full fields including all analysis data

### Location

- File: `backend/api-gateway/routers/events_local.py:121-136`
- File: `backend/api-gateway/routers/ai_analysis_local.py:132-166`

### Expected Behavior

A single, complete `SynthesisResponse` model should be used across the application.

### Proposed Solution

1. Move the complete `SynthesisResponse` to a shared location
2. Update both routers to use it
3. Or rename one to `SynthesisSummary` for the minimal version

### Acceptance Criteria

- [ ] Single source of truth for synthesis response structure
- [ ] All endpoints return consistent data

---

## Issue 8: Remove duplicate JSON parsing in get_event_summary

**Labels**: `refactoring`, `backend`

### Description

The `get_event_summary` endpoint duplicates JSON parsing logic instead of using the Ollama client's `_extract_simple_json` method.

### Location

- File: `backend/api-gateway/routers/ai_analysis_local.py`
- Lines: 250-265

### Problem

```python
# Duplicated logic:
try:
    if "{" in ai_summary and "}" in ai_summary:
        start = ai_summary.find("{")
        end = ai_summary.rfind("}") + 1
        json_str = ai_summary[start:end]
        parsed_summary = json.loads(json_str)
```

### Expected Behavior

Use the existing JSON extraction method from the Ollama client.

### Proposed Solution

Refactor to use `ollama_client._extract_simple_json()` or create a shared utility function.

### Acceptance Criteria

- [ ] JSON parsing is centralized
- [ ] All parsing edge cases are handled consistently

---

## Issue 9: Verify SQLite local-first setup is complete

**Labels**: `testing`, `database`

### Description

After the Supabase free tier lapsed, need to verify that the local SQLite setup works completely for all operations.

### Tasks

- [ ] Test event creation
- [ ] Test response submission
- [ ] Test AI analysis triggering
- [ ] Test synthesis generation
- [ ] Test synthesis approval
- [ ] Test round advancement
- [ ] Test export functionality
- [ ] Remove any remaining Supabase-specific code

### Location

- Database file: `~/.cosenseus/cosenseus_local.db`
- Config: `backend/api-gateway/core/database_local.py`

### Acceptance Criteria

- [ ] All features work with local SQLite
- [ ] No references to Supabase remain in active code
- [ ] Clear documentation for local setup

---

## Issue 10: Make debug logging configurable

**Labels**: `enhancement`, `backend`, `code-quality`

### Description

Multiple `[DEBUG]` print statements throughout the codebase should be configurable via environment variable or settings.

### Locations

- `backend/nlp_service/ollama_client.py` - Lines 532, 547
- `backend/api-gateway/routers/events_local.py` - Lines 373, 382, 404, 412, 420, 424, 445, 503
- `frontend/src/components/EventDetails.tsx` - Line 99

### Expected Behavior

Debug logging should be:
1. Disabled by default in production
2. Enabled via `DEBUG=true` environment variable
3. Use proper logging framework instead of print statements

### Proposed Solution

Backend:
```python
import logging
logger = logging.getLogger(__name__)

# Replace print statements:
# print(f"[DEBUG] Starting analysis...")
logger.debug(f"Starting analysis for event {event_id}")
```

Frontend:
```typescript
const DEBUG = process.env.REACT_APP_DEBUG === 'true';
if (DEBUG) console.log('...');
```

### Acceptance Criteria

- [ ] No debug output in production builds
- [ ] Easy to enable debug mode for development

---

## Issue Summary Table

| # | Title | Priority | Type | Est. Time |
|---|-------|----------|------|-----------|
| 1 | Fix JSON parsing for nested structures | High | Bug | 1 hour |
| 2 | Add JSON array response handling | High | Bug | 30 min |
| 3 | Fix wrong field name in regenerate endpoint | Critical | Bug | 5 min |
| 4 | Complete fallback structures | High | Bug | 30 min |
| 5 | Update SynthesisReview TypeScript interface | High | Bug | 30 min |
| 6 | Add missing database columns | Medium | Enhancement | 30 min |
| 7 | Consolidate duplicate models | Medium | Refactoring | 1 hour |
| 8 | Remove duplicate JSON parsing | Low | Refactoring | 30 min |
| 9 | Verify SQLite setup | Medium | Testing | 1 hour |
| 10 | Make debug logging configurable | Low | Enhancement | 30 min |

**Total estimated time**: 6-7 hours
