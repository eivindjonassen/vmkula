---
description: Execute tasks workflow step
---

# Tasks: $ARGUMENTS

**User Input**: `/tasks $ARGUMENTS`
**Prerequisites**: `plan.md`, `research.md`, `data-model.md`, `contracts/*`

**⚠️ CRITICAL WORKFLOW BOUNDARY**: This command ONLY creates the task breakdown. It does NOT implement tasks. Implementation requires explicit `/implement [feature-name] T001` command from the user. DO NOT auto-proceed to implementation under any circumstances.

## Execution Flow
1.  **Input Processing**: If given a feature name, construct path as `specs/[feature-name]/plan.md`. If given a path, use it directly.
2.  **Plan Loading**: Load the `plan.md` and other design documents from the feature's spec directory. If not found, stop with an error: "❌ ERROR: Plan file not found. Run `/plan [feature-name]` first."
3.  **Set Active Workflow Marker** *(MANDATORY)*: You MUST update the active workflow marker file. This is CRITICAL for TUI tracking.
   - Execute: `mkdir -p .bifrost && echo "specs/[feature-name]:tasks|spec,plan" > .bifrost/active-workflow`
   - This sets tasks as active with spec and plan marked complete
   - Expected content: `specs/[feature-name]:tasks|spec,plan`
   - Verify: `cat .bifrost/active-workflow` should show the exact format above
   - If this step fails, STOP and report the error
4.  **Task Generation**: Generate tasks for each category below (Setup, Tests, Core Implementation, etc.).
5.  **Task Rules Application**: Mark tasks that can be run in parallel with `[P]` (i.e., they modify different files and have no dependencies). Order tasks to follow Test-Driven Development (TDD) - tests must be created before the code that makes them pass.
6.  **Task Numbering**: Number all tasks sequentially (T001, T002, ...).
7.  **Auto-Save Tasks**: Write the completed tasks to `specs/[feature-name]/tasks.md`.
8.  **Auto-Commit**: Stage and commit tasks with message: "Tasks: [feature-name] task breakdown completed".
9.  **Update Session Memory**: Write to `specs/[feature-name]/session.md` to track session progress:
    - **Feature-Specific Session Isolation**: Each feature maintains its own session file for isolated context tracking across concurrent features
    - **Initialize session file if missing**:
    - **Session File Location**: `specs/[feature-name]/session.md`
      - File should already exist from `/spec` phase
      - This command only UPDATES the existing session file
    - **Backward Compatibility Check**: Detect old session format and show migration warning:
      ```bash
      # Warn if old format exists (transition period support)
      OLD_SESSION=".bifrost/memory/session.md"
      NEW_SESSION="specs/[feature-name]/session.md"
      if [[ -f "$OLD_SESSION" && ! -f "$NEW_SESSION" ]]; then
        echo "⚠️  Using legacy session format. Consider migrating: .bifrost/scripts/migrate-session-memory.sh [feature-name]"
      fi
      ```
    - **Update Last Updated date** at top of file with current date (YYYY-MM-DD format)
    - **Update Active Focus section** under `## 🎯 Active Focus` (IMPORTANT: Keep Feature unchanged, only update Phase and Status):
      - **Feature**: [feature-name] (DO NOT CHANGE - keep from previous phase)
      - **Phase**: tasks (update from plan to tasks)
      - **Status**: In Progress
    - **Add entry to Session History** (under `## 📝 Recent Session Context` → `### Session History (Last 5)`):
      - Format: `**YYYY-MM-DD** - Tasks: Created [X] tasks across [Y] phases for [feature-name]. [Brief note about task approach, e.g., "12 tasks can run in parallel. Following TDD approach."]`
      - **CRITICAL - SESSION HISTORY MAINTENANCE (3 STEPS)**:
        1. **FIRST**: Count existing numbered entries (1. 2. 3. etc.) in Session History section
        2. **SECOND**: Add new entry as #1 at the TOP, renumber existing entries (+1 each)
        3. **THIRD**: DELETE ALL entries numbered 6 or higher (keep ONLY entries 1-5)
      - **Validation**: Run `templates/scripts/validate-session-history.sh [feature-name]` to verify
    - **Update Key Decisions** (under `## 🧠 Key Decisions & Context` → `### Context Carryover` → **From Tasks**):
      - Add task breakdown insights and implementation strategy (append to existing From Spec and From Plan content)
    - **Update Progress Tracking** (under `## 📊 Progress Tracking` → `### Feature Progress`):
      - Set **Tasks** to "⧗ In Progress"
      - Add **Implementation** line with: "0/[X] tasks complete (0%)"
10. **Validation Check**: Run the `Validation Checklist` to ensure all design artifacts are covered by a task.
11. **Mark Tasks as Complete** *(MANDATORY)*: Update the workflow marker to mark tasks phase as completed.
    - Execute: `mkdir -p .bifrost && echo "specs/[feature-name]:tasks|spec,plan,tasks" > .bifrost/active-workflow`
    - This marks spec, plan, and tasks as complete
    - Verify: `cat .bifrost/active-workflow` should show `specs/[feature-name]:tasks|spec,plan,tasks`
12. **Update Session Memory (Completion)**: Update `specs/[feature-name]/session.md`:
    - **Update Active Focus section** under `## 🎯 Active Focus`:
      - **Feature**: [feature-name] (DO NOT CHANGE - keep unchanged)
      - **Phase**: tasks (keep as tasks, implement command will change it)
      - **Status**: "Awaiting next action" (tasks complete, waiting for /implement)
      - **Active Task** → **Task ID**: "Ready to start T001"
      - **Active Task** → **Description**: "Task breakdown complete, ready to begin implementation"
      - **Active Task** → **Progress**: "0/[X] tasks complete (0%)"
    - **Update Progress Tracking** (under `## 📊 Progress Tracking` → `### Feature Progress`):
      - Set **Tasks** to "✓ Complete"
    - **REPLACE Next Actions** (under `## 🔄 Next Actions` → `### Immediate Next Steps`):
      - Clear previous next actions completely
      - Replace entire list with: `1. Run \`/implement [feature-name] T001\` to start first task`
      - **IMPORTANT**: This is a note for the USER, not an instruction for the AI to execute
13. **Create Checkpoint** *(MANDATORY)*: Add checkpoint to session memory for pause/resume capability:
    - Update `specs/[feature-name]/session.md` under `## 📊 Progress Tracking` → `### Recovery Checkpoints`
    - **Update Latest Checkpoint** (use LOCAL time in format YYYY-MM-DD HH:MM, not UTC):
      ```
      **CP-003** ([current-date] [current-time]): Tasks breakdown complete, T001-T[XXX] ready
        - **Phase**: tasks
        - **Status**: Complete
        - **Context**: [estimated-context-%] utilization
        - **Artifacts**: tasks.md ([X] tasks across 4 phases)
        - **Dependencies**: Plan validated, design artifacts present
        - **Next**: `/implement [feature-name] T001` to start implementation
      ```
      - **IMPORTANT**: The "Next" field is documentation for the USER, not an instruction to auto-execute
    - **Add to Checkpoint History** (prepend to list, keep only last 5):
      - Same format as Latest Checkpoint
      - Insert at top of Checkpoint History list
       - Remove oldest checkpoint if list exceeds 5 entries
14. **✋ MANDATORY STOP - DO NOT PROCEED TO IMPLEMENTATION**:
    - **CRITICAL**: The `/tasks` command ends here. DO NOT start implementing tasks.
    - **CRITICAL**: DO NOT run any T001, T002, etc. tasks without explicit user command.
    - **CRITICAL**: The user MUST explicitly run `/implement [feature-name] T001` to begin implementation.
    - End with this exact message: "🚦 **TASK BREAKDOWN COMPLETE** - Tasks phase finished. Run `/implement [feature-name] T001` when ready to start implementation."
    - After outputting this message, STOP all activity and wait for user input.

---

## Error Recovery Protocol

*Reference: `templates/standards/error-recovery.md` for complete framework*

### Tasks Phase Error Handling

**Common Errors & Recovery Strategies**:

1. **❌ Plan File Not Found** (Error Category: Dependency Issue)
   - **Detection**: Step 2 - Cannot load plan.md or design artifacts
   - **Recovery**: Strategy 1 (Immediate Retry with Corrections)
   - **Action**:
     - Stop with clear error message showing expected path
     - Check if feature name is correct
     - Verify plan.md exists in specs/[feature-name]/ directory
     - Check for design artifacts (data-model.md, contracts/)
     - Suggest running `/plan [feature-name]` first
     - Do not attempt to create tasks without valid plan

2. **❌ Task Numbering Conflicts or Gaps** (Error Category: Validation Failure)
   - **Detection**: Step 6 - Duplicate task IDs or non-sequential numbering
   - **Recovery**: Strategy 1 (Immediate Retry with Corrections)
   - **Action**:
     - Scan all task IDs for conflicts (e.g., two T005 tasks)
     - Check for gaps in sequence (e.g., T001, T002, T004 - missing T003)
     - Renumber tasks sequentially from T001
     - Update all cross-references to tasks
     - Verify no duplicates remain before proceeding

3. **❌ TDD Ordering Violations** (Error Category: Validation Failure)
   - **Detection**: Step 5 - Implementation tasks ordered before corresponding tests
   - **Recovery**: Strategy 1 (Immediate Retry with Corrections)
   - **Action**:
     - Identify implementation tasks in Phase 3 without Phase 2 tests
     - Create missing test tasks in Phase 2
     - Reorder tasks to enforce TDD: all Phase 2 (tests) before Phase 3 (impl)
     - Verify each implementation task has corresponding test
     - Add clear phase boundaries and phase completion markers

4. **❌ Incorrect Parallel Task Marking** (Error Category: Validation Failure)
   - **Detection**: Step 5 - `[P]` marked tasks have dependencies or shared files
   - **Recovery**: Strategy 1 (Immediate Retry with Corrections)
   - **Action**:
     - Review each `[P]` marked task for true independence
     - Check if tasks modify same files (not parallel if shared)
     - Verify no dependency relationships (e.g., T003 requires T002 complete)
     - Remove `[P]` marker from dependent tasks
     - Verify remaining `[P]` tasks can truly run in parallel

5. **❌ Missing Design Coverage** (Error Category: Validation Failure)
   - **Detection**: Step 10 - Validation checklist fails (missing contract tests, entity models, etc.)
   - **Recovery**: Strategy 1 (Immediate Retry with Corrections)
   - **Action**:
     - Check Validation Checklist items one by one
     - Identify missing task coverage:
       - Endpoints from contracts/ without contract test tasks
       - Entities from data-model.md without implementation tasks
       - User stories from spec.md without integration test tasks
     - Add missing tasks in appropriate phases
     - Renumber all tasks sequentially
     - Re-validate checklist before proceeding

6. **❌ Workflow Marker Update Failure** (Error Category: Tool Failure)
   - **Detection**: Step 3 - Cannot update `.bifrost/active-workflow` file
   - **Recovery**: Strategy 4 (Alternative Approach)
   - **Action**:
     - Check if `.bifrost/` directory exists
     - Verify file permissions
     - Attempt to create directory if missing
     - Retry marker update
     - If persistent failure, warn user (TUI tracking unavailable) but continue

7. **❌ Session Memory Update Failure** (Error Category: Tool Failure)
   - **Detection**: Step 10 - Cannot write to `specs/[feature-name]/session.md`
   - **Recovery**: Strategy 5 (Graceful Degradation)
   - **Action**:
     - Verify `specs/[feature-name]/` directory exists
     - Check file permissions
     - Attempt to create missing directory/file
     - If persistent failure, warn user (session continuity unavailable) but proceed
     - Document task count manually for user reference

8. **❌ Vague Task Descriptions** (Error Category: Validation Failure)
   - **Detection**: Step 4 - Task descriptions lack specific file paths or clear actions
   - **Recovery**: Strategy 1 (Immediate Retry with Corrections)
   - **Action**:
     - Identify vague tasks (e.g., "Implement auth" without file paths)
     - Enhance descriptions with specific file paths
     - Add clear action verbs (Create, Implement, Update, Test)
     - Specify exact artifacts (e.g., "Create contract test in tests/api/auth.test.ts")
     - Verify all tasks have concrete, actionable descriptions

9. **❌ Auto-Proceeding to Implementation** (Error Category: Workflow Violation)
   - **Detection**: Step 14 - AI begins implementing tasks (T001, T002, etc.) immediately after tasks.md creation
   - **Recovery**: Strategy 6 (User Escalation)
   - **Action**:
     - **STOP immediately** if you catch yourself starting implementation
     - **Rollback any implementation changes** made without user command
     - Output the required message: "🚦 **TASK BREAKDOWN COMPLETE**..."
     - Wait for explicit user command (`/implement [feature-name] T001`)
     - **Root Cause**: Misinterpreting session.md "Next" field as execution instruction
     - **Prevention**: Remember that session.md is documentation, not a command queue

### Error State Tracking

When errors occur during tasks phase, update session memory:

```markdown
## 🎯 Active Focus
- **Feature**: [feature-name]
- **Phase**: tasks
- **Status**: Error Recovery
- **Error Type**: [Category from error-recovery.md]
- **Recovery Strategy**: [Strategy name]
- **Recovery Action**: [Specific action being taken]

## ⚠️ Known Issues & Blockers
### Current Blockers
- **[Error Type] (2025-XX-XX)**: [Brief description of error]
  - **Recovery**: [Strategy being applied]
  - **Status**: [In Progress/Resolved]
  - **Next**: [What needs to happen to resolve]
```

After successful recovery, update status to "In Progress" and clear blocker.

### Recovery Quality Gates

Before proceeding after error recovery:

- [ ] **Error Resolved**: Root cause addressed and verified
- [ ] **State Consistent**: Workflow marker and session memory in sync
- [ ] **Tasks Valid**: tasks.md exists with sequential numbering, no conflicts
- [ ] **TDD Enforced**: All test tasks ordered before implementation tasks
- [ ] **Coverage Complete**: Validation checklist passes (all design artifacts covered)
- [ ] **Descriptions Clear**: All tasks have specific file paths and clear actions
- [ ] **Parallel Marking Correct**: `[P]` tasks truly independent with no shared files
- [ ] **User Informed**: User understands error and resolution
- [ ] **Recovery Logged**: Error and recovery tracked in session memory

---

## Task File Format Specification

**File**: `specs/[feature-name]/tasks.md`

**Structure**:
```markdown
# Tasks: [Feature Name]

**Feature**: [feature-name]
**Total Tasks**: [X]
**Parallel Tasks**: [Y] tasks can run in parallel
**Approach**: [Brief description of implementation strategy, TDD approach, etc.]

---

## Phase 1: [Phase Name]

### TXXX: [Task Title]
**File**: `path/to/file.ext`
**Description**: [Detailed multi-line description including:
- What needs to be done
- Specific implementation details
- Code locations (e.g., "Lines 310-320")
- Expected outcomes]
**Dependencies**: [None | T001, T002, ...]
**Parallel**: [Yes [P] | No]
**Status**: [✅ Complete | ❌ Not Needed | (empty for pending)]

### TXXX: [Next Task Title]
...

---

## Phase 2: [Next Phase Name]
...

---

## Validation Checklist

- [ ] All critical requirements from spec.md have corresponding tasks
- [ ] Every endpoint from contracts/ has a contract test task
- [ ] Every entity from data-model.md has a model implementation task
- [ ] All test tasks are ordered before their implementation tasks (TDD)
- [ ] All tasks have specific file paths and clear descriptions
- [ ] Parallel tasks are correctly identified (independent file modifications)
- [ ] Dependencies are explicitly noted where tasks must be sequential

---

## Summary

**Total Tasks**: [X]
**Estimated Effort**: ~[Y] hours
- Phase 1: [X] tasks, ~[Y] hours
- Phase 2: [X] tasks, ~[Y] hours
- ...

**Parallel Execution**: [Description of which tasks can run in parallel and why]

**Implementation Strategy**:
1. [Order of execution]
2. [Key dependencies]
3. [Critical paths]

**Success Criteria**:
- [What defines successful completion]
- [Quality gates]
- [Testing requirements]
```

---

## Task Format Rules

### Task Header Format
```markdown
### TXXX: [Concise, action-oriented task title]
```
- Use sequential numbering: T001, T002, T003, ...
- Title should be concise (60-80 chars) and action-oriented
- Use verbs: "Implement", "Add", "Create", "Update", "Fix", "Enhance"

### Task Metadata Fields

**File**: (Required)
- Specify exact file path(s) to be created or modified
- Use backticks for file paths: `src/components/Modal.tsx`
- For multiple files, list on separate lines
- For new files, indicate: `src/new-file.ts (new)`

**Description**: (Required)
- Multi-line, detailed explanation of what needs to be done
- Include specific implementation details
- Reference line numbers for modifications: "Lines 310-320"
- List sub-tasks or steps with bullet points
- Specify expected outcomes
- Reference design artifacts when applicable

**Dependencies**: (Required)
- List task IDs that must complete before this task: `T001, T002`
- If no dependencies, write: `None`
- For phase dependencies, note: `Phase 1 complete`

**Parallel**: (Required)
- `Yes [P]` if task can run in parallel with others
- `No` if task must run sequentially
- Parallel criteria: Different files, no shared state, no dependencies

**Status**: (Optional, added during implementation)
- In Progress - Task actively being implemented (set by /implement when starting)
- ✅ Complete - Task successfully implemented (set by /implement when finishing)
- ❌ Not Needed - Task determined unnecessary (with explanation)
- (empty) - Task pending (not yet started)

### Phase Organization

Group tasks into logical phases:

1. **Phase 1: Setup & Preparation**
   - Environment setup
   - Dependencies installation
   - Translation keys
   - Configuration

2. **Phase 2: Tests First (TDD)**
   - Contract tests for endpoints
   - Integration tests for user stories
   - Unit tests for core logic
   - **CRITICAL**: All test files created before implementation

3. **Phase 3: Core Implementation**
   - Data models and entities
   - Business logic and services
   - API endpoints
   - UI components

4. **Phase 4: Integration & Polish**
   - End-to-end integration
   - Error handling
   - Edge cases
   - Performance optimization

5. **Phase 5: Documentation & Validation**
   - Update documentation (README, API docs)
   - Constitution updates (RULES.md, etc.)
   - Final testing and validation
   - Validation checklist verification

---

## Example Tasks

### Example 1: Setup Task
```markdown
### T001: Add translation keys for authentication features
**File**: `src/i18n/lang/en.json`
**Description**: Add all missing translation keys for authentication features including:
- Login form labels (`auth.login.email`, `auth.login.password`)
- Error messages (`auth.errors.invalidCredentials`, `auth.errors.accountLocked`)
- Success messages (`auth.success.loginComplete`)
- Password reset flow messages
**Dependencies**: None
**Parallel**: Yes [P]
**Status**: ✅ Complete
```

### Example 2: Test Task (TDD)
```markdown
### T004: Create contract test for POST /api/auth/login endpoint
**File**: `tests/api/auth/login.contract.test.ts`
**Description**: Create contract test validating authentication endpoint behavior:
- Test successful login with valid credentials
- Test failure with invalid credentials (400)
- Test failure with missing fields (400)
- Test account lockout after failed attempts (429)
- Test CSRF token validation
- Verify response schema matches contract specification
**Code Location**: New file in tests/api/auth/
**Dependencies**: T001 (translation keys)
**Parallel**: Yes [P]
**Status**: (empty)
```

### Example 3: Implementation Task
```markdown
### T008: Implement authentication service with JWT tokens
**File**: `src/services/AuthService.ts`
**Description**: Create authentication service with the following functionality:
- Login method: validate credentials, generate JWT token, return user data
- Logout method: invalidate refresh token, clear session
- Token refresh method: validate refresh token, issue new access token
- Password hashing using bcrypt (12 rounds)
- Rate limiting: max 5 login attempts per 15 minutes per IP
- Implement token blacklist for logout
**Code Location**: New file, integrate with existing UserRepository (src/repositories/UserRepository.ts:45)
**Dependencies**: T004 (contract test created), T006 (User model)
**Parallel**: No
**Status**: (empty)
```

### Example 4: Accessibility Task
```markdown
### T015: Add ARIA labels and keyboard navigation to modal dialog
**File**: `src/components/Modal/Modal.tsx`
**Description**: Enhance modal accessibility to meet WCAG 2.1 AA compliance:
- Add `role="dialog"` to modal container (line 45)
- Add `aria-labelledby` pointing to title element (line 48)
- Add `aria-modal="true"` to prevent background interaction
- Implement focus trap: capture tab/shift-tab within modal
- Add ESC key handler to close modal
- Return focus to trigger element on close
- Add `aria-busy="true"` during loading states (line 310-320)
**Code Location**: Lines 45-85 (modal container), lines 310-320 (loading state)
**Dependencies**: T014 (modal structure refactored)
**Parallel**: No
**Status**: (empty)
```

---

## Validation Checklist Template

```markdown
## Validation Checklist

- [ ] All user stories from spec.md have corresponding implementation tasks
- [ ] All endpoints from contracts/ have contract test tasks
- [ ] All entities from data-model.md have model implementation tasks
- [ ] All UI components have accessibility tasks (ARIA, keyboard navigation)
- [ ] All critical workflows have integration test tasks
- [ ] Test tasks (Phase 2) are ordered before implementation tasks (Phase 3)
- [ ] All tasks have specific file paths and clear descriptions
- [ ] Parallel tasks are correctly identified (independent files, no dependencies)
- [ ] Dependencies are explicitly noted for sequential tasks
- [ ] Translation keys added for all user-facing text
- [ ] Documentation updates planned for new features
- [ ] Security considerations addressed (validation, auth, rate limiting)
```

---

## Summary Template

```markdown
## Summary

**Total Tasks**: [X]
**Estimated Effort**: ~[Y] hours (breakdown per phase)
- Phase 1 (Setup): [X] tasks, ~[Y] hours
- Phase 2 (Tests): [X] tasks, ~[Y] hours
- Phase 3 (Implementation): [X] tasks, ~[Y] hours
- Phase 4 (Integration): [X] tasks, ~[Y] hours
- Phase 5 (Documentation): [X] tasks, ~[Y] hours

**Parallel Execution**: [Description]
- Phase 1: Tasks T001-T003 can run in parallel (different files)
- Phase 2: Tasks T004-T012 can run in parallel (independent test files)
- Phase 3: Tasks T015, T016, T018 can run in parallel (different components)

**Implementation Strategy**:
1. Start with translations and setup (T001-T003)
2. Create all test files following TDD approach (T004-T012)
3. Implement core functionality to make tests pass (T013-T025)
4. Add integration and polish features (T026-T030)
5. Update documentation and validate (T031-T033)

**Critical Path**: T001 → T004 → T013 → T020 → T026 → T031

**Success Criteria**:
- All tests passing (100% pass rate)
- WCAG 2.1 AA compliance achieved
- Code coverage >80% for business logic
- All contract tests validating API specifications
- Documentation updated and reviewed
```