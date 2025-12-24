---
description: Execute implement workflow step
---

# Implementation: $ARGUMENTS

**🚨 USER INPUT PROVIDED 🚨**

User invoked: `/implement $ARGUMENTS`

**IMMEDIATE ACTION REQUIRED**: Parse the arguments "$ARGUMENTS" below and proceed directly to Step 1 if valid format. DO NOT ask for clarification.

**⚠️ CRITICAL - CANONICAL PHASE NAMES**: This template uses phase name `implement`. See `templates/standards/workflow-markers.md` for EXACT format requirements. ONLY valid phase names are: `spec`, `plan`, `tasks`, `implement` (NOT "implementation"). These are parsed by TUI and MUST be exact.

## Input Parser (EXECUTE IMMEDIATELY)

**ARGUMENTS PROVIDED**: `$ARGUMENTS`

**⚠️ CRITICAL - DO NOT ASK FOR CLARIFICATION**: The user already provided input. Parse it and execute immediately if format is valid.

**Valid Input Formats**:
1. `[feature-name] [task-id]` → Single task mode
   - Example: "club-field-management T001"
   - Example: "annual-hours-settings-consolidation T014"
2. `[feature-name] phase [N]` → Batch mode
   - Example: "club-field-management phase 2"
   - Example: "annual-hours-settings-consolidation phase 4"
3. `[path/to/tasks.md] [task-id]` → Path-based single task
4. `[path/to/tasks.md] phase [N]` → Path-based batch

**Parser Algorithm**:
```python
# The arguments are available in $ARGUMENTS variable
# Example: if user typed "/implement annual-hours-settings-consolidation phase 4"
# then $ARGUMENTS = "annual-hours-settings-consolidation phase 4"

arguments = "$ARGUMENTS"
tokens = arguments.strip().split()

if len(tokens) == 2:
  # Format 1 or 3: Single task
  feature_or_path = tokens[0]
  task_id = tokens[1]
  mode = "single"
  # ✅ PROCEED IMMEDIATELY TO STEP 1
  
elif len(tokens) == 3 and tokens[1].lower() == "phase":
  # Format 2 or 4: Batch mode
  feature_or_path = tokens[0]
  phase_number = tokens[2]
  mode = "batch"
  # ✅ PROCEED IMMEDIATELY TO STEP 1
  
else:
  # Invalid format - show error
  print("ERROR: Invalid format. Got: '$ARGUMENTS'")
  print("Valid formats:")
  print("  - Single task: /implement [feature] [task-id]")
  print("  - Batch mode:  /implement [feature] phase [N]")
  exit()
```

**PARSING EXAMPLES** (current invocation):
- **THIS INVOCATION**: `$ARGUMENTS`
  - Parse this NOW and proceed to Step 1 if valid
  
- Example: If $ARGUMENTS = `"annual-hours-settings-consolidation phase 4"` 
  - tokens = ["annual-hours-settings-consolidation", "phase", "4"]
  - len(tokens) = 3, tokens[1] = "phase" ✅
  - Action: **PROCEED TO STEP 1** with feature="annual-hours-settings-consolidation", phase=4
  
- Example: If $ARGUMENTS = `"club-field-management T001"`
  - tokens = ["club-field-management", "T001"]
  - len(tokens) = 2 ✅
  - Action: **PROCEED TO STEP 1** with feature="club-field-management", task="T001"

**MANDATORY**: $ARGUMENTS is already provided above. Parse it NOW and **IMMEDIATELY PROCEED TO STEP 1** if valid format. DO NOT ask for clarification.

## Execution Flow

**🔄 BATCH MODE** (phase X): Loop steps 4-17 for EACH task. Update session/checkpoint/todo AFTER EACH (not at batch end). Todo list provides real-time progress visibility. Single task: Execute steps once.

---

1.  **Input Processing**: Parse feature name and task ID. Construct path as `specs/[feature-name]/tasks.md`.
2.  **Task Loading & Todo Initialization**: Load tasks.md and locate task by ID. If "phase X", load all phase tasks for batch mode. If not found, stop with error.
   
   **Phase Task Detection (supports 2 formats)**:
   - **Format 1 - Metadata Fields**: Tasks with `**Phase**: N` field
     ```markdown
     ## T001: Task Title
     **Phase**: 1
     **Status**: pending
     ```
   - **Format 2 - Section Headers**: Tasks grouped under phase section
     ```markdown
     ## Phase 1: Foundation & Types (T001-T004)
     ### T001: Task Title
     ### T002: Another Task
     ```
   
   **Phase Task Loading Algorithm**:
   1. First, search for tasks with `**Phase**: [N]` metadata field
   2. If none found, search for section headers matching:
      - `## Phase [N]:` or `### Phase [N]:`
      - `## Phase [N] -` or `## Phase [N] :`
   3. For section headers:
      - Extract task range from header (e.g., `(T001-T004)`)
      - OR collect all task IDs under that section until next phase/section
   4. Collect all matching tasks for the phase
   
   **Todo List Creation**:
   - **Single Task Mode**: Create todo with 1 item: "Implement [Task ID]: [Description]"
   - **Batch Mode (Phase X)**: Create todo list with ALL tasks in the phase (e.g., Phase 2 = T004, T005, T006, T007)
     - Each todo: "Implement [Task ID]: [Brief description]"
     - All marked as "pending" initially
     - Priority: "high" for all implementation tasks
   - This gives real-time visibility of progress for multi-task phases
3.  **Set Active Workflow Marker** *(CONDITIONAL)*: Check if the workflow marker is already set to implement phase for this feature.
   - Read current marker: `cat .bifrost/active-workflow 2>/dev/null || echo ""`
   - If marker already shows `specs/[feature-name]:implement|spec,plan,tasks`, skip this step (already set from previous task)
   - Otherwise, update the marker:
     - Execute: `mkdir -p .bifrost && echo "specs/[feature-name]:implement|spec,plan,tasks" > .bifrost/active-workflow`
     - This sets implement as active with previous phases marked complete
   - This prevents unnecessary marker updates when running multiple `/implement` tasks in sequence
4.  **🔴 Task Start (2 SUBSTEPS)**: Initialize task execution with all required tracking:

   **4a. Set Session Status to Active**:
   - Update `specs/[feature-name]/session.md` under `## 🎯 Active Focus` (IMPORTANT: Keep Feature and Phase unchanged):
      - **Feature-Specific Session Isolation**: Each feature maintains its own session file for isolated context tracking across concurrent features
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
     - **Update Active Focus section**:
       - **Feature**: [feature-name] (DO NOT CHANGE - keep from previous phase)
       - **Phase**: implement (should already be implement from first task, do not change)
       - **Status**: "Active" (work starting on this task)
       - **Active Task** → **Task ID**: Task being started (e.g., "T014")
       - **Active Task** → **Description**: Brief description of task about to be implemented
     - This shows "Active" status immediately when work begins, before task completes

   **4b. Set Task Status to In Progress**:
   - Update the task in `specs/[feature-name]/tasks.md`:
     - Find the specific task section being implemented (e.g., `### T014: Task title`)
     - Add or update the **Status** field to: `**Status**: In Progress`
     - This enables the TUI to display the task as actively running with the ⚡ icon
     - If the **Status** field doesn't exist, add it after the **Parallel** field
   - **Update Todo List**: Mark current task as "in_progress" in todo list
     - Find the todo item for this task ID
     - Update status from "pending" to "in_progress"
     - This provides real-time progress visibility to the user

---

⛔ **STOP - PRE-IMPLEMENTATION ASSESSMENT (DO NOT SKIP)**

**Before implementing (step 5), complete this mandatory checklist:**

□ **Task Complexity Assessment**
  - Complexity: [Simple/Medium/Complex]
  - Scope: [Number of files to modify, estimated lines of code]
  - Strategy: [Direct / Agent-Assisted] (see logic below)
  - Reasoning: [Brief justification]

□ **Task Validation**
  - Prerequisites: [List or "None"]
  - Dependencies: [List or "None"]
  - Status: [Ready / Blocked - explain]

□ **Context Loading**
  - spec.md: [Loaded/Summarized/Skipped - why]
  - plan.md: [Sections loaded]
  - Code Files: [List files + relevance]

□ **Constitution Review**
  - File: RULES.md
  - Rules: [2-3 relevant patterns]
  - Plan: [How you'll comply]

**✋ GATE**: All 4 boxes checked?
   → NO? Complete missing items.
   → YES? State: "Assessment complete. Proceeding to step 5."

**Strategy Logic**: Complex task (>5 files, multiple systems) → Agent-Assisted (use @general for complex tasks) | Simple/Medium → Direct

**Note**: Context window management is handled automatically by the CLI's auto-compact feature. Focus on task complexity, not context percentage.

---

5. **Focused Implementation**: Execute implementation based on strategy selected in assessment.

   **5a. Direct Implementation** (Strategy: Direct, Simple/Medium tasks):
   - Write code to satisfy the single task requirements
   - Do not exceed the scope of the task
   - Follow project patterns and constitutional requirements
   - Proceed to step 6

   **5b. Agent-Assisted Implementation** (Strategy: Agent-Assisted, Complex tasks with >5 files or multiple systems):
   - Use @general agent for complex implementation assistance
   - Provide minimal context package (5 elements: task spec, code files, constitution, success criteria, return format)
   - Focus on current task only, not entire batch
   - Integrate results and proceed to step 6
   - **CRITICAL**: Maintain batch loop control - focus ONLY on current task, never entire batch

   **IMPORTANT**: Regardless of path (5a/5b), parent continues to step 6 for quality/completion/metrics/session updates.

6. **Test Integration & TDD State**: If creating a test, ensure it fails appropriately. If implementing functionality, ensure tests pass.
   - **TDD State Tracking** (`.bifrost/tdd-state.json`):
     - **Phase 2 (Test Creation)**: Set state to `TEST_FAILING` after creating failing test
     - **Phase 3 (Implementation)**: Set state to `IMPLEMENTING` while writing code
     - **Phase 4 (Validation)**: Set state to `TEST_PASSING` when all tests pass
     - **Phase 5 (Commit)**: State returns to `IDLE` after successful commit
7. **Phase-Based Test Execution**:
    - **Phase 2 (Test Creation)**: Run tests to verify they fail appropriately with clear error messages (TDD: `TEST_FAILING`)
    - **Phase 4 (Validation)**: Run full test suite to verify all tests pass and no regressions (TDD: `TEST_PASSING`)
    - **Other Phases**: Skip automatic test execution
8. **Test Execution Prompt**: For Phase 2 and Phase 4 tasks, ask user: "Would you like to run tests to verify this implementation? (y/n)"
9. **Quality Review**: Review code for quality, correctness, and constitutional compliance.
10. **🔴 Task Completion (3 SUBSTEPS)**:
   - **10a. Mark Complete in tasks.md**: Update task Status to `✅ Complete`
   - **10b. Update Todo List**: Mark current task as "completed" in todo list
     - Update status from "in_progress" to "completed"
     - Provides clear completion feedback in real-time
   - **10c. Auto-Commit**: `git add . && git commit -m "Implement: [feature-name] - Task [task-id] completed"`
11. **🔴 Update Session Memory** (AFTER EACH TASK): Write to `specs/[feature-name]/session.md`:
     - **Update Last Updated** date (YYYY-MM-DD)
     - **Update Active Focus**: Status "Idle", Task ID "[task-id] complete", Progress "X/Y tasks (Z%)"
     - **Update Next Actions**: Show next task or polish commands if all complete
     - **Add Session History Entry**: `**YYYY-MM-DD** - Implement Phase X: Completed TXXX. [Brief summary]. X/Y tasks complete (Z%).`
       - **CRITICAL**: Add as #1 at TOP, renumber existing, DELETE entries 6+ (keep only 1-5)
       - **Validate**: `templates/scripts/validate-session-history.sh [feature-name] [--fix]`
     - **Update Progress Tracking**: Implementation progress "X/Y tasks (Z%)"
     - **Update Related Files**: List files changed with brief description
12. **🔴 Create Task Checkpoint** (AFTER EACH TASK): Add checkpoint in session.md Recovery Checkpoints:
     - Format: `**CP-00X** (YYYY-MM-DD HH:MM): Task [ID] complete - [brief description]`
     - Include: Phase, Status, Artifacts, Dependencies, Next action
     - Prepend to Checkpoint History, keep last 5
13. **Check All Tasks Complete**: Determine if this was the final task.
    - Count total tasks: `TOTAL=$(grep -c "^- \[" specs/[feature-name]/tasks.md)`
    - Count completed tasks: `DONE=$(grep -cE "^- \[(x|X|✅)\]" specs/[feature-name]/tasks.md)`
    - If `$DONE -eq $TOTAL`, all tasks are complete, proceed to step 14
    - Otherwise, skip to step 18 (MANDATORY STOP)
14. **Mark Implementation as Complete** *(CONDITIONAL)*: Only if all tasks are complete.
    - Read current completed phases: `CURRENT=$(cat .bifrost/active-workflow 2>/dev/null || echo ""); COMPLETED=$(echo "$CURRENT" | grep -o '|.*' || echo "|spec,plan,tasks")`
    - Execute: `mkdir -p .bifrost && echo "specs/[feature-name]:implement${COMPLETED},implement" > .bifrost/active-workflow`
    - This adds implement to the completed list (typically results in `|spec,plan,tasks,implement`)
15. **Update Session Memory (All Tasks Complete)**: If all tasks complete, update `specs/[feature-name]/session.md`:
     - **Update Active Focus section** under `## 🎯 Active Focus`:
       - **Feature**: [feature-name] (DO NOT CHANGE - keep unchanged)
       - **Phase**: implement (DO NOT CHANGE - keep as implement)
       - **Status**: "Awaiting next action" (no active task currently)
       - **Active Task** → **Task ID**: "All tasks complete"
       - **Active Task** → **Description**: "Implementation phase finished - ready for polish"
       - **Active Task** → **Progress**: "23/23 tasks complete (100%)"
     - **Update Progress Tracking** (under `## 📊 Progress Tracking` → `### Feature Progress`):
       - Set **Implementation** to "✓ Complete"
     - **REPLACE Next Actions** (under `## 🔄 Next Actions` → `### Immediate Next Steps`):
       - Clear previous next actions completely
       - Replace entire list with polish phase actions:
         1. Run `/polish-docs [feature-name]` to generate documentation
         2. Run `/polish-test-plus [feature-name]` for additional test coverage
         3. Run `/polish-pr-summary [feature-name]` to create PR summary
     - **Add completion entry to Session History** (under `## 📝 Recent Session Context` → `### Session History (Last 5)`):
       - Format: `**YYYY-MM-DD** - Implementation Complete: All 23 tasks finished for [feature-name]. Ready for polish phase.`
       - **CRITICAL - SESSION HISTORY MAINTENANCE (3 STEPS)**:
         1. **FIRST**: Count existing numbered entries (1. 2. 3. etc.) in Session History section
         2. **SECOND**: Add new entry as #1 at the TOP, renumber existing entries (+1 each)
         3. **THIRD**: DELETE ALL entries numbered 6 or higher (keep ONLY entries 1-5)
       - **Validation**: Run `templates/scripts/validate-session-history.sh [feature-name]` to verify
16. **Create Final Implementation Checkpoint** *(CONDITIONAL - MANDATORY if all tasks complete)*: Add completion checkpoint:
    - Update `specs/[feature-name]/session.md` under `## 📊 Progress Tracking` → `### Recovery Checkpoints`
    - **Update Latest Checkpoint** (use LOCAL time in format YYYY-MM-DD HH:MM, not UTC):
      ```
      **CP-00X** ([current-date] [current-time]): Implementation complete, all [Total] tasks done
        - **Phase**: implement
        - **Status**: Complete
        - **Artifacts**: All implementation files for [feature-name]
        - **Dependencies**: All [Total] tasks complete, tests passing
        - **Next**: Polish phase - `/polish-docs`, `/polish-test-plus`, `/polish-pr-summary`
      ```
    - **Add to Checkpoint History** (prepend to list, keep only last 5):
      - Same format as Latest Checkpoint
      - Insert at top of Checkpoint History list
      - Remove oldest checkpoint if list exceeds 5 entries
    - This checkpoint marks implementation phase completion for `/resume` capability
17. **✋ MANDATORY STOP OR CONTINUE**: Handle completion based on mode:
     - **BATCH MODE (phase X)**:
       - ✅ Verify session memory was just updated (step 11) and checkpoint created (step 12) for task just completed
       - If more tasks remain in the batch: **IMMEDIATELY LOOP BACK TO STEP 4** for the next task
       - Do NOT show completion message until entire batch is done
       - Do NOT defer updates - each task must update session memory individually
     - **BATCH MODE (phase X complete)**: If last task in batch, show: "🚦 **PHASE X COMPLETE** - [N] tasks finished. Session memory updated after each task."
     - **SINGLE TASK MODE**: Show: "🚦 **TASK [task-id] COMPLETE** - Run `/implement [feature-name] [next-task-id]` to continue or review remaining tasks."
     - **ALL TASKS COMPLETE**: Show: "🚦 **ALL TASKS COMPLETE** - Feature [feature-name] implementation finished! Run polish commands or create PR."

---

## Error Recovery Protocol

**Reference**: `templates/standards/error-recovery.md` for complete framework (6 error categories, 6 recovery strategies)

**Common Implement Phase Errors**:
- **Task/File Not Found**: Stop, verify feature name and task ID format
- **Test Failures**: Phase 2 (expect fail) | Phase 3 (fix impl) | Phase 4 (fix regression)
- **Scope Creep**: Narrow to task requirements or get user approval
- **Git Commit Fails**: Handle conflicts/hooks/permissions, preserve work
- **Context Overflow**: CLI handles auto-compact automatically; for complex tasks use @general agent
- **Missing Dependencies**: Install packages, update plan.md, document decision
- **Prerequisites Not Met**: Complete prerequisite tasks first (recommended)
- **Session Update Fails**: Check directory/permissions, gracefully degrade if needed
- **Constitutional Violations**: Identify violations, refactor to follow RULES.md

**Error State Tracking**: Update session.md Active Focus with status "Error Recovery" and add blocker to Known Issues with error type, recovery strategy, and next steps. Clear after resolution.

---

## Context Management

**Note**: Context window management is handled automatically by the CLI's auto-compact feature. You don't need to estimate or track context percentages.

**Agent Assistance** (Complex tasks): For tasks touching >5 files or multiple systems, consider using @general agent for assistance.

---

## Task Context
**ID**: [Task ID from tasks.md]
**Description**: [Task Description]
**Files**: [Files to modify]
**Tests**: [Test requirements]
**Dependencies**: [Prerequisites]

---

## Implementation

**Language-Specific Best Practices**:
- **Strongly-Typed** (TypeScript/Go/Rust/Java): Use type system, interface-driven
- **Dynamic** (JS/Python/Ruby): Clear signatures, consistent naming, TDD

**Quality Checklist**:
- [ ] Scope adherence (task only, no extras)
- [ ] Constitutional compliance (RULES.md patterns)
- [ ] Test integration (pass or appropriate fail)
- [ ] Code quality (readable, maintainable)
- [ ] Integration ready (connects properly)