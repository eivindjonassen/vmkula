---
description: Execute implement-yolo workflow step
---

# Implementation YOLO: Autonomous Task Execution

**⚠️ CRITICAL - CANONICAL PHASE NAMES**: This template uses phase name `implement`. See `templates/standards/workflow-markers.md` for EXACT format requirements. ONLY valid phase names are: `spec`, `plan`, `tasks`, `implement` (NOT "implementation"). These are parsed by TUI and MUST be exact.

**Input**: Feature name (e.g., "club-field-management"), "phase X" for active workflow phase, or no argument to use active workflow
**Context**: All design and planning documents from `/specs/[###-feature-name]/`.
**Mode**: Autonomous - implements ALL tasks sequentially without user verification between tasks.

## Input Argument Examples

- `/implement-yolo` - Use active workflow feature (from `.bifrost/active-workflow`)
- `/implement-yolo phase 2` - Implement Phase 2 of active workflow (e.g., tasks T008-T016)
- `/implement-yolo nextjs-migration` - Explicitly implement "nextjs-migration" feature (overrides active workflow)

## ⚡ YOLO Mode Overview

**YOLO Mode** processes the entire tasks.md sequentially, one task at a time, without stopping for user verification. This mode is designed for autonomous implementation when you trust the AI to complete all tasks hands-off.

**Key Characteristics**:
- ✅ Processes ALL tasks in tasks.md sequentially
- ✅ Loads ONE task at a time (context-efficient)
- ✅ Updates session memory after EACH task
- ✅ Creates checkpoint after EACH task
- ✅ Runs tests automatically (no prompts)
- ✅ Continues automatically to next task
- ❌ NO user verification between tasks
- ❌ NO prompts or questions during execution
- ⚠️ Stops only on critical errors or completion

**When to Use**:
- You've reviewed the tasks.md and trust the plan
- Tasks are well-defined and granular
- You want hands-off implementation
- Tasks are individually manageable in scope

**When NOT to Use**:
- Tasks are complex or ambiguous
- You want to review each implementation
- Tasks have high risk or uncertainty
- You prefer incremental verification

---

## Execution Flow

### 🔄 AUTONOMOUS LOOP STRUCTURE

**YOLO MODE**: Execute steps 5-21 in a LOOP for EACH task until all complete:

```
LOAD all task IDs from tasks.md
FOR EACH task in task list:
  ↓ Load ONLY current task context (step 5)
  ↓ Set session status to Active (step 6)
  ↓ Record task start (step 7) - METRICS TRACKING
  ↓ Implement current task (steps 8-15)
  ↓ Record task end (step 16) - METRICS TRACKING
  ↓ Update session memory IMMEDIATELY (step 17)
  ↓ Create checkpoint IMMEDIATELY (step 18)
  ↓ Mark task complete (step 19)
  ↓ Auto-commit (step 20)
  ↓ Check remaining tasks and loop (step 21)
NEXT task
↓ Mark implementation complete (steps 22-25)
```

**CRITICAL**:
- Process one task at a time, updating session memory and creating checkpoints after each task
- **Metrics tracking (steps 7 and 16) MUST execute for EACH task** to track timing data

---

1.  **Input Processing**: Parse input and resolve feature name intelligently.
    - **Check Active Workflow First**: Read `.bifrost/active-workflow` to get current feature
      - Execute: `ACTIVE=$(cat .bifrost/active-workflow 2>/dev/null | cut -d: -f1 | sed 's|^specs/||')`
      - If active workflow exists, use it as default feature context
    - **Parse Input Argument**:
      - **No argument**: Use active workflow feature (if exists), else error
      - **"phase X" or "Phase X"**: Extract tasks from Phase X of active workflow
        - Parse phase number: `PHASE=$(echo "$INPUT" | grep -oiE "phase [0-9]+" | grep -oE "[0-9]+")`
        - Load only tasks from Phase X: `grep -E "^## Phase ${PHASE}:" specs/[active-feature]/tasks.md`
        - Extract task range for phase (e.g., T008-T016)
        - Set feature to active workflow feature
      - **Feature name** (e.g., "club-field-management"): Use as explicit feature override
        - Check if `specs/[feature-name]/tasks.md` exists
        - If exists, use this feature (overrides active workflow)
        - If not exists, error: "Feature not found: [feature-name]"
    - **Construct path**: `specs/[feature-name]/tasks.md`
    - **Phase filtering**: If "phase X" specified, store phase filter for task loading
2.  **Task Loading**: Load the `tasks.md` file and extract ALL task IDs (or phase-specific tasks).
    - **Parse all tasks** from tasks.md using BOTH supported formats:
      - **Header format** (standard): `grep -E "^### T[0-9]{3}" specs/[feature-name]/tasks.md`
      - **Bullet format** (deprecated): `grep "^- \[" specs/[feature-name]/tasks.md`
      - Prefer header format if both exist
    - **Phase filtering** (if "phase X" specified):
      - Find phase header: `## Phase ${PHASE}:`
      - Extract task range from phase header (e.g., "T008-T016")
      - Filter tasks to only those in range
      - Example: For "Phase 2 (T008-T016)", only load T008 through T016
    - **Create execution list** of task IDs (T001, T002, T003, ..., TXXX)
    - **Filter to incomplete tasks**: Exclude tasks with `**Status**: ✅ Complete`
      - Use grep or awk to find tasks WITHOUT Complete status
      - Example: `awk '/^### (T[0-9]{3}):/{id=$2; status=""} /^\*\*Status\*\*:.*✅.*Complete/{status="done"} /^### T[0-9]{3}:/ && status=="" && id!=""{print id; status="printed"}' specs/[feature-name]/tasks.md`
    - **Validation**:
      - If no incomplete tasks: Show "✅ All tasks already complete!" and exit
      - If tasks found: Proceed to step 3
3.  **Set Active Workflow Marker**: Update workflow marker to implement phase.
    - Execute: `mkdir -p .bifrost && echo "specs/[feature-name]:implement|spec,plan,tasks" > .bifrost/active-workflow`
    - This sets implement as active with previous phases marked complete
4.  **Show Execution Plan**: Display autonomous execution plan (for transparency):
    ```
    🚀 **YOLO MODE ACTIVATED** - Autonomous Implementation

    Feature: [feature-name]
    Total Tasks: [N] tasks
    Mode: Autonomous (no user verification)

    Execution Plan:
    - Process all [N] tasks sequentially
    - One task at a time (context-efficient)
    - Automatic test execution
    - Session memory updated after each task
    - Checkpoints created incrementally

    Starting in 3 seconds... (Ctrl+C to cancel)
    ```
    - Wait 3 seconds to allow user cancellation
    - Proceed to task loop (step 5)

---

### 🔄 TASK LOOP (Steps 5-16)

**Execute for EACH task in the execution list:**

5.  **Load Current Task Context** *(ONE TASK ONLY)*: Load ONLY the current task being implemented.
    - **Task ID**: [Current task ID from list, e.g., T014]
    - **Task Description**: [Read description from tasks.md for this task only]
    - **Estimated Complexity**: [Simple/Medium/Complex based on description]
    - **Dependencies**: [Check if dependent tasks are complete]
    - **DO NOT**: Load all tasks into context - only current task
    - **DO NOT**: Load unnecessary historical context
    - **Focus**: Minimal, task-specific context for efficient implementation

6.  **Set Session Status to Active**: Update `specs/[feature-name]/session.md`:
    - **Feature-Specific Session Isolation**: Each feature maintains its own session file for isolated context tracking across concurrent features
    - **Initialize session file if missing**:
    - **Session File Location**: `specs/[feature-name]/session.md`
      - File should already exist from `/spec` and `/plan` and `/tasks` phases
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
    - **Update Active Focus section** under `## 🎯 Active Focus`:
      - **Feature**: [feature-name]
      - **Phase**: implement
      - **Status**: "Active (YOLO Mode)" (automated execution)
      - **Active Task**: (nested structure - update all three sub-bullets)
        - **Task ID**: [Current task ID, e.g., T014]
        - **Description**: Brief description of current task
        - **Progress**: "X/Y tasks complete (Z%)"
    - Shows work has started on this specific task

7.  **🔴 Task Start**: Initialize task execution with required tracking:

   **7a. Set Task Status to In Progress**:
   - Update the task in `specs/[feature-name]/tasks.md`:
     - Find the specific task section being implemented (e.g., `### T014: Task title`)
     - Add or update the **Status** field to: `**Status**: In Progress`
     - This enables the TUI to display the task as actively running with the ⚡ icon
     - If the **Status** field doesn't exist, add it after the **Parallel** field

---

⛔ **STOP - ASSESSMENT PHASE BEGINS (YOLO MODE)**

**DO NOT PROCEED TO IMPLEMENTATION YET.** You must complete steps 8-12 (assessment and planning) before writing any code. Implementation begins at step 13, NOT before. YOLO Mode runs autonomously, but still requires proper assessment.

---

8.  **🔴 MANDATORY Task Complexity Assessment (DO NOT SKIP - YOLO MODE)**: Evaluate task complexity and scope.

   **YOU MUST OUTPUT:**
   - **Task Complexity**: [Simple/Medium/Complex]
   - **Scope**: [Number of files to modify, estimated lines]
   - **Reasoning**: [Brief justification for complexity assessment]

   ✋ **CHECKPOINT A**: Have you documented your complexity assessment above?
      → NO? Do it now before proceeding.
      → YES? Continue to step 9.

9.  **🔴 MANDATORY Strategy Selection (DO NOT SKIP - YOLO MODE)**: Based on assessment in step 8, select implementation approach.

   **DECISION LOGIC:**
   - If task complexity is Complex (>5 files, multiple systems): Use @general agent for assistance
   - Otherwise: Proceed with direct implementation

   **YOU MUST STATE:**
   - **Strategy Selected**: [Direct Implementation / Agent-Assisted]
   - **Justification**: [Why this strategy based on step 8 assessment]

   **Note**: Context window management is handled automatically by the CLI's auto-compact feature. Focus on task complexity, not context percentage.

   ✋ **CHECKPOINT B**: Have you stated your strategy and justification above?
      → NO? Do it now before proceeding.
      → YES? Continue to step 10.

10. **🔴 MANDATORY Task Validation (DO NOT SKIP - YOLO MODE)**: Verify task is ready for implementation.

   **YOU MUST CHECK:**
   - **Prerequisites**: [List any tasks that must be complete first]
   - **Dependencies**: [List files/packages this task depends on]
   - **Status**: [Are all prerequisites satisfied? Yes/No]
   - **Action if blocked**: If prerequisites not met, document in session memory and skip to next task

   ✋ **CHECKPOINT C**: Have you confirmed task readiness above?
      → NO? Document blockers and skip to next task in YOLO mode.
      → YES? Continue to step 11.

11. **🔴 MANDATORY Context Loading (DO NOT SKIP - YOLO MODE)**: Load relevant context efficiently for THIS task only.

   **YOU MUST LIST:**
   - **spec.md**: [Loaded fully / Summarized / Skipped - explain why]
   - **plan.md**: [Which sections loaded - list them]
   - **Code Files**: [List specific files loaded and why relevant to current task]

   ✋ **CHECKPOINT D**: Have you documented all loaded context above?
      → NO? List what you loaded before proceeding.
      → YES? Continue to step 12.

12. **🔴 MANDATORY Constitution Adherence (DO NOT SKIP - YOLO MODE)**: Review project's constitution for applicable rules.

   **YOU MUST REFERENCE:**
   - **Constitution File**: RULES.md
   - **Applicable Rules**: [List 2-3 most relevant rules/patterns for this task]
   - **Compliance Plan**: [How you'll follow these rules during implementation]

   ✋ **CHECKPOINT E**: Have you identified applicable rules above?
      → NO? Review constitution and document rules before proceeding.
      → YES? Proceed to Implementation Gate.

---

✋ **CRITICAL IMPLEMENTATION GATE (YOLO MODE)**

**BEFORE PROCEEDING TO IMPLEMENTATION (STEP 13), VERIFY ALL CHECKPOINTS:**

□ **Checkpoint A** - Task complexity assessed and documented (step 8)
□ **Checkpoint B** - Strategy selected and justified (step 9)
□ **Checkpoint C** - Task validated and dependencies confirmed (step 10)
□ **Checkpoint D** - Context loaded and files listed (step 11)
□ **Checkpoint E** - Constitution reviewed and rules identified (step 12)

**ALL boxes must be checked. Missing any? Return to that step now.**

**🚦 SELF-CHECK:** Am I jumping to implementation without completing assessment?
   → YES? **STOP.** Return to the incomplete checkpoint.
   → NO? State: **"Pre-implementation complete (YOLO Mode). All 5 checkpoints verified. Proceeding to step 13."**

---

13. **Focused Implementation**: Execute implementation based on strategy selected in step 9 (YOLO Mode).

   **13a. Direct Implementation** (Strategy: Direct, Simple/Medium tasks):
   - Write code to satisfy the single task requirements
   - Do not exceed the scope of the task
   - Follow project patterns and constitutional requirements
   - Ensure code integrates with existing system
   - Proceed to step 14

   **13b. Agent-Assisted Implementation** (Strategy: Agent-Assisted, Complex tasks with >5 files or multiple systems):
   - **CRITICAL FOR YOLO MODE**: Maintain YOLO loop - focus ONLY on current task, not entire batch
   - Use @general agent for complex implementation assistance
   - **Context Package** (5 essential elements):
     1. Task specification (THIS task only from tasks.md)
     2. Relevant code files (specific files this task modifies)
     3. Constitution (RULES.md patterns)
     4. Success criteria (test requirements for THIS task)
     5. Return format (how to hand results back)
   - **Scope Boundaries**:
     ```
     IN SCOPE: Implement ONLY Task [task-id], follow constitution, return results
     OUT OF SCOPE: Other tasks, workflow files, metrics, session memory, YOLO loop control
     ```
   - Focus on current task implementation with agent assistance
   - Integrate results into workflow
   - Proceed to step 14 for test execution and completion

   **IMPORTANT FOR YOLO MODE**: Regardless of implementation path (13a/13b), parent ALWAYS continues to step 14. Parent is responsible for steps 14-18 (test execution, completion, metrics recording, session memory, checkpoints) and maintaining the YOLO loop.

14. **Automatic Test Execution** *(NO PROMPTS)*:
    - **Phase 2 (Test Creation)**: Run tests to verify they fail appropriately
      - Execute test suite automatically
      - Verify test fails for right reason
      - Check error message is clear and actionable
      - If test doesn't fail correctly, fix test and retry
    - **Phase 3 (Implementation)**: Run tests to verify they pass
      - Execute test suite automatically
      - Verify all tests pass
      - If tests fail, review and fix implementation
      - Retry until tests pass
    - **Phase 4 (Validation)**: Run full test suite
      - Execute complete test suite automatically
      - Verify no regressions
      - If regressions detected, fix and retry
    - **Other Phases**: Skip automatic test execution
    - **NO PROMPTS**: Tests run automatically without user confirmation

15. **🔴 Task Completion (2 SUBSTEPS)**: Complete the task with required tracking:

   **15a. Mark Task Complete in tasks.md**:
   - **CRITICAL**: Use the header-based format with `**Status**` field (NOT checkbox format)
   - Find the task header: `### T[ID]: Task Name`
   - Locate the `**Status**:` line in the task metadata (after **File**, **Description**, **Dependencies**, **Parallel**)
   - Update the status line to: `**Status**: ✅ Complete`
   - Use Edit tool or sed to update the status field:
     ```bash
     # Find the task section and update its Status field
     # Example sed command (adjust for specific task ID):
     sed -i '' '/^### T001:/,/^### T002:/{s/^\*\*Status\*\*:.*$/\*\*Status\*\*: ✅ Complete/;}' specs/[feature-name]/tasks.md
     ```
   - **Expected format**:
     ```markdown
     ### T001: Task Name
     **File**: `src/example.ts`
     **Description**: Task description
     **Dependencies**: None
     **Parallel**: No
     **Status**: ✅ Complete
     ```

   **15b. Auto-Commit Changes**:
   - Execute: `git add -A && git commit -m "Implement: [feature-name] - Task [ID] completed (YOLO Mode)"`
   - If commit fails, log warning but continue (don't stop YOLO mode)

16. **🔴 Update Session Memory** *(MANDATORY AFTER EACH TASK)*: Write to `specs/[feature-name]/session.md`:
    - **Update Last Updated date** at top of file with current date (YYYY-MM-DD format)
    - **Update Active Focus section** under `## 🎯 Active Focus`:
      - **Feature**: [feature-name] (unchanged)
      - **Phase**: implement (unchanged)
      - **Status**: "Idle (YOLO Mode)" (task finished, moving to next)
      - **Active Task**: (nested structure - update all three sub-bullets)
        - **Task ID**: "[Current task ID] complete"
        - **Description**: Brief description of what was completed
        - **Progress**: "X/Y tasks complete (Z%)"
    - **Update Next Actions** under `## 🔄 Next Actions` → `### Immediate Next Steps`:
      - If more tasks remain: "1. Automatically continuing with [next task ID] (YOLO Mode)"
      - If last task: Will be updated in step 18
    - **Add entry to Session History** (under `## 📝 Recent Session Context` → `### Session History (Last 5)`):
      - Format: `**YYYY-MM-DD** - YOLO Mode: Completed [task ID]. [Brief summary]. X/Y tasks complete (Z%).`
      - **CRITICAL - SESSION HISTORY MAINTENANCE (3 STEPS)**:
        1. **FIRST**: Count existing numbered entries (1. 2. 3. etc.) in Session History section
        2. **SECOND**: Add new entry as #1 at the TOP, renumber existing entries (+1 each)
        3. **THIRD**: DELETE ALL entries numbered 6 or higher (keep ONLY entries 1-5)
      - **Validation**: Run `templates/scripts/validate-session-history.sh [feature-name]` to verify
    - **Update Progress Tracking**:
      - Update implementation line with current task count
    - **Update Related Files**: Add files changed in this task

17. **🔴 Create Task Checkpoint** *(MANDATORY AFTER EACH TASK)*: Add checkpoint to session memory:
    - Update `specs/[feature-name]/session.md` under `## 📊 Progress Tracking` → `### Recovery Checkpoints`
    - **Update Latest Checkpoint** (use LOCAL time in format YYYY-MM-DD HH:MM):
      ```
      **CP-00X** ([current-date] [current-time]): Task [ID] complete (YOLO Mode)
        - **Phase**: implement (Task [X] of [Y])
        - **Status**: In Progress
        - **Artifacts**: [files modified/created in this task]
        - **Dependencies**: [X]/[Y] tasks complete
        - **Next**: Continuing automatically with [next-task-id] (YOLO Mode)
      ```
    - **Add to Checkpoint History** (prepend, keep last 5)

18. **Check Remaining Tasks**: Determine if more tasks remain.
    - Count tasks using header-based format with **Status** field:
      - Total tasks: `TOTAL=$(grep -cE "^### T[0-9]{3}:" specs/[feature-name]/tasks.md)`
      - Completed tasks: `DONE=$(grep -A 10 "^### T[0-9]{3}:" specs/[feature-name]/tasks.md | grep -c "^\*\*Status\*\*:.*✅.*Complete")`
    - Alternative (simpler): Count tasks with "Complete" status:
      - `DONE=$(awk '/^### T[0-9]{3}:/{task=$0} /^\*\*Status\*\*:.*✅.*Complete/{print task}' specs/[feature-name]/tasks.md | wc -l | tr -d ' ')`
    - If `$DONE -lt $TOTAL`: **IMMEDIATELY LOOP BACK TO STEP 7** for next task (Task Start substeps)
    - If `$DONE -eq $TOTAL`: All tasks complete, proceed to step 19

---

### ✅ ALL TASKS COMPLETE (Steps 19-22)

**Execute only when all tasks are finished:**

19. **Mark Implementation as Complete**: Update workflow marker to mark implement phase complete.
    - Read current completed phases: `CURRENT=$(cat .bifrost/active-workflow 2>/dev/null); COMPLETED=$(echo "$CURRENT" | grep -o '|.*' || echo "|spec,plan,tasks")`
    - Execute: `echo "specs/[feature-name]:implement${COMPLETED},implement" > .bifrost/active-workflow`
    - This adds implement to completed list (typically `|spec,plan,tasks,implement`)

20. **Update Session Memory (All Complete)**: Final session memory update:
    - **Update Active Focus section** under `## 🎯 Active Focus`:
      - **Feature**: [feature-name]
      - **Phase**: implement
      - **Status**: "Awaiting next action (YOLO Mode Complete)"
      - **Active Task**: (nested structure - update all three sub-bullets)
        - **Task ID**: "All tasks complete"
        - **Description**: "YOLO Mode finished - all [Y] tasks implemented"
        - **Progress**: "[Y]/[Y] tasks complete (100%)"
    - **Update Progress Tracking**:
      - Set **Implementation** to "✓ Complete"
    - **REPLACE Next Actions**:
      - Clear previous next actions
      - Replace with polish phase actions:
        1. Run `/polish-docs [feature-name]` to generate documentation
        2. Run `/polish-test-plus [feature-name]` for additional test coverage
        3. Run `/polish-pr-summary [feature-name]` to create PR summary
    - **Add completion entry to Session History** (under `## 📝 Recent Session Context` → `### Session History (Last 5)`):
      - Format: `**YYYY-MM-DD** - YOLO Mode Complete: All [Y] tasks finished for [feature-name]. Ready for polish phase.`
      - **CRITICAL - SESSION HISTORY MAINTENANCE (3 STEPS)**:
        1. **FIRST**: Count existing numbered entries (1. 2. 3. etc.) in Session History section
        2. **SECOND**: Add new entry as #1 at the TOP, renumber existing entries (+1 each)
        3. **THIRD**: DELETE ALL entries numbered 6 or higher (keep ONLY entries 1-5)
      - **Validation**: Run `templates/scripts/validate-session-history.sh [feature-name]` to verify

21. **Create Final Implementation Checkpoint**: Add completion checkpoint:
    - Update `specs/[feature-name]/session.md` under `## 📊 Progress Tracking` → `### Recovery Checkpoints`
    - **Update Latest Checkpoint** (use LOCAL time):
      ```
      **CP-00X** ([current-date] [current-time]): YOLO Mode complete - all [Y] tasks done
        - **Phase**: implement
        - **Status**: Complete
        - **Artifacts**: All implementation files for [feature-name]
        - **Dependencies**: All [Y] tasks complete, tests passing
        - **Next**: Polish phase - `/polish-docs`, `/polish-test-plus`, `/polish-pr-summary`
      ```
    - **Add to Checkpoint History** (prepend, keep last 5)

22. **Show Completion Summary**: Display final summary:
    ```
    🎉 **YOLO MODE COMPLETE** 🎉

    Feature: [feature-name]
    Tasks Completed: [Y]/[Y] (100%)
    Mode: Autonomous (YOLO Mode)

    Summary:
    - All tasks implemented successfully
    - Session memory updated after each task
    - Incremental checkpoints created
    - Tests executed automatically
    - [Y] commits created

    Next Steps:
    1. Run `/polish-docs [feature-name]` to generate documentation
    2. Run `/polish-test-plus [feature-name]` for additional test coverage
    3. Run `/polish-pr-summary [feature-name]` to create PR summary

    Ready for polish phase! 🚀
    ```

---

## Error Recovery Protocol

*Reference: `templates/standards/error-recovery.md` for complete framework*

### YOLO Mode Error Handling

**Critical Errors (STOP YOLO MODE)**:
- Task file or task ID not found (cannot proceed)
- Workflow state corrupted (cannot determine state)
- User interruption (Ctrl+C or explicit cancellation)

**Recoverable Errors (CONTINUE WITH WARNING)**:
- Test failures: Fix and retry automatically (up to 3 attempts)
- Git commit failures: Log warning and continue (preserve work)
- Missing dependencies: Install automatically if possible
- Constitutional violations: Fix automatically and retry

**Error Recovery Strategy**:
1. **Immediate Retry** (Strategy 1): For test failures, minor tool issues
   - Apply fix automatically
   - Retry up to 3 times
   - If still failing after 3 attempts, log error and skip to next task
2. **Agent Assistance** (Strategy 2): For complex tasks
   - Use @general agent for implementation assistance
   - Focus on current task with agent help
   - Integrate results
   - Continue to next task
3. **Graceful Degradation** (Strategy 3): For non-critical failures
   - Log warning in session memory
   - Preserve partial work
   - Continue to next task
4. **Checkpoint Rollback** (Strategy 4): For corrupted state
   - STOP YOLO MODE
   - Restore from last valid checkpoint
   - Inform user of state and recovery options

**Error State Tracking**:
When errors occur, update session memory with error details:
```markdown
## ⚠️ Known Issues & Blockers
### Current Blockers
- **[Error Type] (YYYY-MM-DD)**: [Description]
  - **Task**: [Task ID where error occurred]
  - **Recovery**: [Strategy applied]
  - **Status**: [Continuing/Stopped]
  - **Next**: [What happens next]
```

**Automatic vs. Manual Recovery**:
- **Automatic**: Test failures, context compaction, dependency installation, commit failures
- **Manual** (STOPS YOLO MODE): Corrupted state, user cancellation, critical errors

---

## Context Management for YOLO Mode

**Note**: Context window management is handled automatically by the CLI's auto-compact feature. You don't need to estimate or track context percentages.

### One-Task-At-A-Time Context Loading

**CRITICAL**: YOLO Mode loads ONE task at a time to maintain efficient context usage.

**Per-Task Context Loading**:
1. **Load Current Task Only**: Read only the current task from tasks.md
2. **Summarize Background**: Project context summarized to key principles
3. **Focus on Relevant Code**: Load only files directly related to current task
4. **Compact Non-Essential**: Previous task context → key patterns only

**Context Elements Per Task**:
- ✅ **Current task specification**: Full detail for task being implemented
- ✅ **Relevant code files**: Files to be modified or created
- ✅ **Test requirements**: Tests to make pass or create
- ✅ **Key interfaces**: APIs, data models directly used
- ❌ **All other tasks**: Do NOT load other tasks into context
- ❌ **Full project history**: Summarize to key principles only
- ❌ **Previous implementations**: Compact to patterns only

**Context Optimization Techniques**:
1. **Background Compaction**: Project history → 2-3 key principles
2. **Architecture Focus**: Full architecture → relevant modules only
3. **Pattern Reference**: Previous tasks → key patterns applied
4. **Selective File Loading**: Load only modified files, not entire codebase

### Agent Assistance Strategy

For complex tasks (>5 files, multiple systems), use @general agent for implementation assistance with **minimal context package**.

**Philosophy**: Pass ONLY essential context (minimal package), not comprehensive context.

**Minimal Context Package** (5 essential elements):
1. Task specification (THIS task only from tasks.md)
2. Relevant code files (specific files this task modifies)
3. Constitution (RULES.md patterns)
4. Success criteria (test requirements for THIS task)
5. Return format (how to hand results back)

**Agent-Assisted Workflow** (YOLO Mode):
1. **Record task-start** (step 7 already completed)
2. **Use @general agent** with minimal context package
3. **Provide focused context**: Task spec + relevant files + constitution + success criteria
4. **Agent assists with implementation** (ONLY this task)
5. **Integrate results** into main workflow
6. **Record task-end** (step 16 - metrics and completion)
7. **Continue YOLO Mode** with next task (maintain loop)

**Critical for YOLO Mode**:
- ALWAYS maintain the YOLO loop - never delegate loop control
- Focus ONLY on current task - never entire batch
- Track all metrics (task-start before, task-end after)
- Update session memory and checkpoints after each task
- Agent focuses exclusively on implementing ONE task

---

## Implementation Validation (Per Task)

**Quality checkpoints before moving to next task:**

- [ ] **Scope Adherence**: Implementation addresses exactly the specified task
- [ ] **Constitutional Compliance**: Code follows project patterns and standards
- [ ] **Test Integration**: Tests pass (implementation) or fail appropriately (test creation)
- [ ] **Code Quality**: Implementation is readable, maintainable, follows best practices
- [ ] **Integration Ready**: Code integrates properly with existing system
- [ ] **Session Memory Updated**: Task completion tracked in session memory
- [ ] **Checkpoint Created**: Recovery checkpoint created for this task
- [ ] **Task Marked Complete**: tasks.md updated with [✅] for this task
- [ ] **Changes Committed**: Implementation committed to git (or preserved if commit failed)

---

## YOLO Mode Best Practices

### When YOLO Mode Works Best

✅ **Use YOLO Mode when:**
- Tasks are well-defined and granular (clear requirements)
- Tasks.md has been reviewed and validated
- Each task is relatively simple (not highly complex)
- You trust the AI to implement without supervision
- Tasks have clear test cases or acceptance criteria
- You want continuous, hands-off implementation

❌ **Avoid YOLO Mode when:**
- Tasks are ambiguous or poorly defined
- Tasks are highly complex or risky
- Tasks require user decisions or clarifications
- You want to review each implementation before proceeding
- Tasks have uncertain scope or requirements
- You prefer incremental, verified progress

### Monitoring YOLO Mode Execution

**TUI Monitoring**:
- **Workflow+Tasks Pane**: Watch progress indicators update after each task
- **Agent Pane**: Scroll through implementation output
- **Session Memory**: Check `.bifrost/memory/session.md` for progress

**Checkpoints**:
- Incremental checkpoints created after each task
- Recovery checkpoints enable rollback if needed
- `/resume [feature-name]` can resume from any checkpoint

**Cancellation**:
- Press Ctrl+C to stop YOLO Mode at any time
- Current task will be preserved (may be incomplete)
- Session memory will reflect last completed task
- Resume with `/resume [feature-name]` or continue with `/implement [feature-name] [next-task-id]`

### YOLO Mode vs. Regular /implement

| Feature | `/implement` | `/implement-yolo` |
|---------|--------------|-------------------|
| **Task Processing** | Single task or batch (with prompts) | All tasks automatically |
| **User Verification** | Prompted between tasks | No prompts (autonomous) |
| **Test Execution** | Asks user confirmation | Automatic (no prompts) |
| **Context Loading** | One task at a time | One task at a time |
| **Session Memory Updates** | After each task | After each task |
| **Checkpoints** | After each task | After each task |
| **Error Handling** | Stops on errors | Tries to recover automatically |
| **Best For** | Incremental, verified progress | Hands-off, autonomous implementation |

Both commands use the same context management strategy (one task at a time) to prevent context overflow.

---

## Context Handoff Summary

**After YOLO Mode Completes**:
- **Completed**: All [Y] tasks implemented for [feature-name]
- **Session Memory**: Updated with complete session history and progress
- **Checkpoints**: Incremental checkpoints created for each task + final checkpoint
- **Next Phase**: Ready for polish commands (`/polish-docs`, `/polish-test-plus`, `/polish-pr-summary`)
- **Recovery**: Can resume from any checkpoint using `/resume [feature-name]` if needed
