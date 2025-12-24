# Task Format Standard

**Version**: 1.0.0
**Last Updated**: 2025-10-17
**Status**: Proposed

## Overview

This document defines the **standard task format** for all Bifrost workflows. Consistent task formatting enables reliable parsing, progress tracking, and workflow automation across projects.

## Problem Statement

Bifrost currently supports multiple task formats, causing parsing ambiguity:

1. **Header-based format** (e.g., `specs/nextjs-migration/tasks.md`):
   ```markdown
   ### T001 [✅]: Initialize Next.js Project
   ```

2. **Bullet-based format** (e.g., `specs/equipment-phase2/tasks.md`):
   ```markdown
   - [✅] **T001**: Update Prisma schema to rename Team model
   ```

This inconsistency causes issues:
- Argument parsing ambiguity (e.g., `/implement-yolo phase 2` matching wrong feature)
- Workflow tracking confusion
- Task counting errors (grep patterns match different formats)
- Session memory update failures

## Standard Format

### Primary Standard: Header-Based Format

**All Bifrost workflows MUST use header-based task format:**

```markdown
### T001 [ ]: Task Title

**Description**: Detailed task description

**Acceptance Criteria**:
- Criterion 1
- Criterion 2

**Dependencies**: None (or T000, T000)
```

### Task ID Convention

- **Format**: `T` + zero-padded 3-digit number (e.g., `T001`, `T023`, `T154`)
- **Sequence**: Sequential, starting from `T001`
- **No gaps**: If tasks are removed, don't renumber - gaps are acceptable

### Status Indicators

**Use checkbox notation in the header:**

- `[ ]` - Not started (incomplete task)
- `[✅]` - Completed successfully
- `[⏸]` - Paused/blocked (optional)
- `[❌]` - Failed/skipped (optional)

**Examples**:
```markdown
### T001 [ ]: Setup database schema
### T002 [✅]: Create user authentication
### T003 [⏸]: Implement OAuth (blocked on T002)
```

### Phase Organization (Optional)

For large workflows, organize tasks into phases:

```markdown
## Phase 1: Project Setup (T001-T007)

### T001 [ ]: Initialize repository
...

## Phase 2: Authentication (T008-T016)

### T008 [ ]: Create login component
...
```

### Task Structure Template

```markdown
### TXXX [ ]: [Brief imperative title]

**Description**:
[1-3 sentences describing what needs to be done and why]

**Acceptance Criteria**:
- [Specific, testable criterion 1]
- [Specific, testable criterion 2]
- [Tests pass / Feature works as expected]

**Dependencies**: [Task IDs this task depends on, or "None"]

**Files to Modify**:
- `path/to/file1.ts`
- `path/to/file2.ts`

**Estimated Complexity**: [Simple | Medium | Complex]

---
```

## Parsing Specification

### Task Extraction

**Standard grep pattern for task extraction:**
```bash
# Extract all task IDs
grep -E "^### T[0-9]{3}" specs/[feature-name]/tasks.md

# Count total tasks
grep -c "^### T[0-9]{3}" specs/[feature-name]/tasks.md

# Count completed tasks
grep -cE "^### T[0-9]{3} \[✅\]" specs/[feature-name]/tasks.md

# Count incomplete tasks
grep -cE "^### T[0-9]{3} \[ \]" specs/[feature-name]/tasks.md
```

### Phase Extraction

**Standard pattern for phase detection:**
```bash
# Extract all phase headers
grep -E "^## Phase [0-9]+:" specs/[feature-name]/tasks.md
```

## Migration Guide

### Converting Bullet-Based to Header-Based

**Before (bullet-based)**:
```markdown
- [ ] **T001**: Update Prisma schema to rename Team model
```

**After (header-based)**:
```markdown
### T001 [ ]: Update Prisma schema to rename Team model

**Description**: Rename the Team model to better reflect its purpose.

**Acceptance Criteria**:
- Prisma schema updated
- Database migration created
- No breaking changes to existing code

**Dependencies**: None

---
```

### Automated Migration Script

```bash
# Convert bullet-based tasks.md to header-based
# Usage: ./convert-task-format.sh specs/feature-name/tasks.md

#!/bin/bash
TASKS_FILE="$1"
BACKUP="${TASKS_FILE}.backup"

# Create backup
cp "$TASKS_FILE" "$BACKUP"

# Convert bullet format to header format
sed -E 's/^- \[([ ✅⏸❌x])\] \*\*T([0-9]{3})\*\*: (.+)$/### T\2 [\1]: \3\n\n**Description**: [TODO: Add description]\n\n**Acceptance Criteria**:\n- [TODO: Add criteria]\n\n**Dependencies**: None\n\n---/' "$TASKS_FILE" > "${TASKS_FILE}.tmp"

mv "${TASKS_FILE}.tmp" "$TASKS_FILE"

echo "✓ Converted $TASKS_FILE from bullet format to header format"
echo "  Backup saved to: $BACKUP"
echo "  Please review and fill in Description and Acceptance Criteria"
```

## Template Updates Required

### Files to Update

1. **`templates/commands/tasks.md`** (line ~XX):
   - Update task generation template to use header format
   - Update examples to show header format

2. **`templates/commands/implement-yolo.md`** (line 60):
   - Change from: `grep "^- \[" specs/[feature-name]/tasks.md`
   - Change to: `grep "^### T[0-9]{3}" specs/[feature-name]/tasks.md`

3. **`templates/commands/implement.md`**:
   - Update task parsing logic to use header format

4. **`tui/` (bifrost-tui)**:
   - Update task counting logic to use header format

## Benefits

1. **Clear visual hierarchy**: Headers make tasks easy to scan
2. **GitHub navigation**: Headers appear in GitHub's document outline
3. **Consistent parsing**: Single grep pattern across all workflows
4. **Better documentation**: More space for detailed descriptions
5. **Phase organization**: Natural grouping with markdown headers

## Backward Compatibility

**Transition Period**: 2025-10-17 to 2025-11-17 (30 days)

During the transition period:
- Existing bullet-based tasks.md files remain valid
- New workflows MUST use header-based format
- Users should migrate existing workflows gradually
- Tools will support BOTH formats (with deprecation warnings)

**After Transition Period**:
- Bullet-based format considered deprecated
- Tools may drop support for bullet-based format
- Migration required for continued Bifrost compatibility

## Validation

### Linter Rules (Future)

A future `bifrost-lint` command could validate:
- [ ] All tasks use header format (`### TXXX`)
- [ ] All task IDs are sequential
- [ ] All tasks have Description section
- [ ] All tasks have Acceptance Criteria section
- [ ] Phase headers follow standard format
- [ ] No duplicate task IDs

## Examples

### Simple Workflow (No Phases)

```markdown
# Tasks: User Authentication Feature

## Overview
Implement basic user authentication with login/logout functionality.

---

### T001 [ ]: Create login form component

**Description**: Build a React form component for user login with email and password fields.

**Acceptance Criteria**:
- Form has email and password input fields
- Form validates input before submission
- Form shows error messages appropriately
- Tests pass for form validation

**Dependencies**: None

---

### T002 [ ]: Implement authentication API endpoint

**Description**: Create backend API endpoint to handle user login requests.

**Acceptance Criteria**:
- POST /api/auth/login endpoint created
- Validates credentials against database
- Returns JWT token on success
- Returns 401 on invalid credentials
- Tests pass for authentication logic

**Dependencies**: T001

---
```

### Complex Workflow (With Phases)

```markdown
# Tasks: Next.js Migration

## Overview
Migrate existing React application to Next.js framework.

---

## Phase 1: Project Setup (T001-T007)

### T001 [✅]: Initialize Next.js Project

**Description**: Create new Next.js project with TypeScript and configure initial settings.

**Acceptance Criteria**:
- Next.js 14+ project initialized
- TypeScript configured
- Project builds successfully
- All required dependencies installed

**Dependencies**: None

---

### T002 [ ]: Configure routing structure

**Description**: Set up Next.js app router structure to match existing React Router setup.

**Acceptance Criteria**:
- App router configured
- Route definitions match existing structure
- Navigation works correctly
- Tests pass for routing

**Dependencies**: T001

---

## Phase 2: Authentication (T008-T016)

### T008 [ ]: Migrate authentication components

**Description**: Port existing authentication components to Next.js structure with Server Components where appropriate.

**Acceptance Criteria**:
- Login component migrated
- Auth context works with Next.js
- Server-side session handling implemented
- Tests pass for authentication flow

**Dependencies**: T002

---
```

## References

- **Error Recovery Standard**: `templates/standards/error-recovery.md`
- **Implementation Guide**: `templates/commands/implement.md`
- **YOLO Mode**: `templates/commands/implement-yolo.md`
- **Workflow Tracking**: `.bifrost/workflow-tracking.md`

## Change Log

- **2025-10-17**: Initial standard proposed (v1.0.0)
