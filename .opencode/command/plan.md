---
description: Execute plan workflow step
---

# Implementation Plan: $ARGUMENTS

**⚠️ CRITICAL - CANONICAL PHASE NAMES**: This template uses phase name `plan`. See `templates/standards/workflow-markers.md` for EXACT format requirements. ONLY valid phase names are: `spec`, `plan`, `tasks`, `implement` (NOT "specification", "planning", or "implementation"). These are parsed by TUI and MUST be exact.

**User Input**: `/plan $ARGUMENTS`
**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link to spec.md]

## Execution Flow
1.  **Input Processing**: If given a feature name, construct path as `specs/[feature-name]/spec.md`. If given a path, use it directly.
2.  **Specification Loading**: Load the feature specification from the determined path. If not found, stop with an error: "❌ ERROR: Specification file not found. Run `/spec [feature-description]` first."
3.  **Set Active Workflow Marker** *(MANDATORY)*: You MUST update the active workflow marker file. This is CRITICAL for TUI tracking.
   - Execute: `mkdir -p .bifrost && echo "specs/[feature-name]:plan|spec" > .bifrost/active-workflow`
   - This sets plan as active with spec marked complete
   - Expected content: `specs/[feature-name]:plan|spec`
   - Verify: `cat .bifrost/active-workflow` should show the exact format above
   - If this step fails, STOP and report the error
4.  **Scope Assessment**: Evaluate codebase size and planning complexity to determine strategy.
5.  **Strategy Selection**:
    - If large codebase (>50 files to explore): Consider using @general agent for research assistance
    - Otherwise: Proceed with direct planning and research
6.  **Context Analysis**: Fill out the `Technical Context` section below. For any unknown, use `[NEEDS CLARIFICATION]`.
7.  **Constitution Compliance**: Based on the project's `RULES.md`, fill out the `Constitution Check` section, providing evidence for each rule.
8.  **Compliance Evaluation**: Evaluate the `Constitution Check`. If there are violations that cannot be justified in the `Complexity Tracking` section, stop with an error: "❌ ERROR: Constitution violations detected without valid justification."
9.  **Research Phase**: Execute **Phase 0 (Research)** using ACE-enhanced systematic exploration. Consider using @general agent for large codebases (>50 files). Consolidate findings into `research.md`.
10. **Design Phase**: Execute **Phase 1 (Design)** to produce the data model, API contracts, and failing tests.
11. **Context Compaction**: Apply context compaction strategies before proceeding to ensure optimal context utilization.
12. **Auto-Save Plan**: Write the completed plan to `specs/[feature-name]/plan.md`.
13. **Auto-Commit**: Stage and commit plan with message: "Plan: [feature-name] technical plan completed".
14. **Update Session Memory**: Write to `specs/[feature-name]/session.md` to track session progress:
    - **Feature-Specific Session**: Use feature session created by spec phase for isolated tracking
    - **Session File Location**: `specs/[feature-name]/session.md`
      - File should already exist from `/spec` phase
      - This command only UPDATES the existing session file
    - **Backward Compatibility**: Prefer new format, graceful fallback to old:
      ```bash
      SESSION_FILE="specs/[feature-name]/session.md"
      OLD_SESSION=".bifrost/memory/session.md"
      if [[ ! -f "$SESSION_FILE" && -f "$OLD_SESSION" ]]; then
        echo "⚠️  Using legacy session format. Consider migrating: .bifrost/scripts/migrate-session-memory.sh [feature-name]"
        SESSION_FILE="$OLD_SESSION"
      fi
      ```
    - **Update Last Updated date** at top of file with current date (YYYY-MM-DD format)
    - **Update Active Focus section** under `## 🎯 Active Focus` (IMPORTANT: Keep Feature unchanged, only update Phase and Status):
      - **Feature**: [feature-name] (DO NOT CHANGE - keep from spec phase)
      - **Phase**: plan (update from spec to plan)
      - **Status**: In Progress
    - **Add entry to Session History** (under `## 📝 Recent Session Context` → `### Session History (Last 5)`):
      - Format: `**YYYY-MM-DD** - Plan: Completed technical planning for [feature-name]. [Brief 1-line summary of approach].`
      - **CRITICAL - SESSION HISTORY MAINTENANCE (3 STEPS)**:
        1. **FIRST**: Count existing numbered entries (1. 2. 3. etc.) in Session History section
        2. **SECOND**: Add new entry as #1 at the TOP, renumber existing entries (+1 each)
        3. **THIRD**: DELETE ALL entries numbered 6 or higher (keep ONLY entries 1-5)
      - **Validation**: Run `templates/scripts/validate-session-history.sh [feature-name]` to verify
    - **Update Key Decisions** (under `## 🧠 Key Decisions & Context`):
      - **Architectural Decisions**: Add key technical architecture decisions from plan
      - **Context Carryover** → **From Plan**: Add critical technical approach details (append to existing From Spec content)
     - **Update Progress Tracking** (under `## 📊 Progress Tracking` → `### Feature Progress`):
       - Set **Plan** to "⧗ In Progress"
15. **Auto-Run Validation** *(MANDATORY)*: Execute validation script to verify plan quality:
    ```bash
    cd [project-root] && .bifrost/scripts/validate-plan.sh specs/[feature-name]/plan.md
    ```
    You MUST execute this command automatically. If validation fails, review and fix issues before proceeding.
16. **Mark Plan as Complete** *(MANDATORY)*: Update the workflow marker to mark plan phase as completed.
    - Execute: `mkdir -p .bifrost && echo "specs/[feature-name]:plan|spec,plan" > .bifrost/active-workflow`
    - This marks both spec and plan as complete
    - Verify: `cat .bifrost/active-workflow` should show `specs/[feature-name]:plan|spec,plan`
17. **Update Session Memory (Completion)**: Update `specs/[feature-name]/session.md`:
    - **Update Active Focus section** under `## 🎯 Active Focus`:
      - **Feature**: [feature-name] (DO NOT CHANGE - keep unchanged)
      - **Phase**: plan (keep as plan, tasks command will change it)
      - **Status**: "Awaiting next action" (plan complete, waiting for /tasks)
    - **Update Progress Tracking** (under `## 📊 Progress Tracking` → `### Feature Progress`):
      - Set **Plan** to "✓ Complete"
    - **REPLACE Next Actions** (under `## 🔄 Next Actions` → `### Immediate Next Steps`):
      - Clear previous next actions completely
      - Replace entire list with: `1. Run \`/tasks [feature-name]\` to proceed to task breakdown phase`
18. **Create Checkpoint** *(MANDATORY)*: Add checkpoint to feature session for pause/resume capability:
    - Update `specs/[feature-name]/session.md` under `## 📊 Progress Tracking` → `### Recovery Checkpoints`
    - **Update Latest Checkpoint** (use LOCAL time in format YYYY-MM-DD HH:MM, not UTC):
      ```
      **CP-002** ([current-date] [current-time]): Plan validated, ready for tasks
        - **Phase**: plan
        - **Status**: Complete
        - **Artifacts**: plan.md, research.md, data-model.md, contracts/
        - **Dependencies**: Spec validated, technical context resolved
        - **Next**: `/tasks [feature-name]` to break down into tasks
      ```
    - **Add to Checkpoint History** (prepend to list, keep only last 5):
      - Same format as Latest Checkpoint
      - Insert at top of Checkpoint History list
      - Remove oldest checkpoint if list exceeds 5 entries
    - Optional: Create mid-phase checkpoint after research complete (Step 10) if research was significant
19. **✋ MANDATORY STOP**: End here with message: "🚦 **PLANNING COMPLETE** - Run `/tasks [feature-name]` to proceed to task breakdown phase."

---

## Error Recovery Protocol

*Reference: `templates/standards/error-recovery.md` for complete framework*

### Plan Phase Error Handling

**Common Errors & Recovery Strategies**:

1. **❌ Specification File Not Found** (Error Category: Dependency Issue)
   - **Detection**: Step 2 - Cannot load spec.md from expected path
   - **Recovery**: Strategy 1 (Immediate Retry with Corrections)
   - **Action**:
     - Stop with clear error message showing expected path
     - Check if feature name is correct
     - Verify spec.md exists in specs/[feature-name]/ directory
     - Suggest running `/spec [feature-description]` first
     - Do not attempt to create plan without valid spec

2. **❌ Large Codebase Research** (Error Category: Scope Issue)
   - **Detection**: Step 4 - Codebase has >50 files to explore
   - **Recovery**: Strategy 3 (Agent Assistance)
   - **Action**:
     - Use @general agent for research assistance
     - Delegate systematic codebase exploration
     - Provide focused research questions
     - Integrate agent findings into planning context
     - **Note**: Context window management is handled automatically by the CLI's auto-compact feature

3. **❌ Constitution Violations Detected** (Error Category: Validation Failure)
   - **Detection**: Step 8 - Rules violations found without valid justification
   - **Recovery**: Strategy 4 (Alternative Approach)
   - **Action**:
     - Identify specific rule violations in Constitution Check
     - Review Complexity Tracking section for justifications
     - If no valid justification exists:
       - Present violation details to user
       - Offer alternative approaches that comply with rules
       - Redesign violating components to follow constitution
     - Re-validate Constitution Check before proceeding

4. **❌ Missing Technical Context** (Error Category: Dependency Issue)
   - **Detection**: Step 6 - Critical technical context contains `[NEEDS CLARIFICATION]`
   - **Recovery**: Strategy 1 (Immediate Retry with Corrections)
   - **Action**:
     - Identify which technical elements are unknown
     - Search project for evidence (package.json, go.mod, requirements.txt)
     - Check existing code for patterns and frameworks
     - If still unclear, ask user for clarification
     - Update Technical Context section with findings
     - Verify all critical elements resolved before design

5. **❌ Missing Design Artifacts** (Error Category: Validation Failure)
   - **Detection**: Step 10 - data-model.md, contracts/, or tests not created
   - **Recovery**: Strategy 1 (Immediate Retry with Corrections)
   - **Action**:
     - Identify which artifacts are missing
     - Create missing artifacts following plan structure
     - Verify all artifacts present:
       - data-model.md with entities and relationships
       - contracts/ directory with API definitions
       - Failing test files appropriate for project type
     - Validate artifact quality before proceeding

6. **❌ Workflow Marker Update Failure** (Error Category: Tool Failure)
   - **Detection**: Step 3 - Cannot update `.bifrost/active-workflow` file
   - **Recovery**: Strategy 4 (Alternative Approach)
   - **Action**:
     - Check if `.bifrost/` directory exists
     - Verify file permissions
     - Attempt to create directory if missing
     - Retry marker update
     - If persistent failure, warn user (TUI tracking unavailable) but continue

7. **❌ Validation Script Failure** (Error Category: Tool Failure)
   - **Detection**: Step 16 - `validate-plan.sh` not found or returns errors
   - **Recovery**: Strategy 5 (Graceful Degradation) or Strategy 1 (Immediate Retry)
   - **Action**:
     - **If script missing**:
       - Warn user validation unavailable
       - Perform manual quality review
       - Suggest running `bifrost-admin.py` to update scripts
       - Proceed if manual validation passes
     - **If validation errors**:
       - Show specific validation failures
       - Fix identified issues
       - Retry validation
       - Only proceed when validation passes

8. **❌ Agent Assistance Failure** (Error Category: Tool Failure)
   - **Detection**: Step 9 - Agent research fails or returns incomplete results
   - **Recovery**: Strategy 4 (Alternative Approach)
   - **Action**:
     - Review partial results from agent if available
     - Identify what research questions remain unanswered
     - Apply direct research approach with context compaction
     - Fill research gaps with targeted code exploration
     - Document findings in research.md
     - If critical gaps remain, consult user

### Error State Tracking

When errors occur during plan phase, update session memory:

```markdown
## 🎯 Active Focus
- **Feature**: [feature-name]
- **Phase**: plan
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
- [ ] **Artifacts Valid**: plan.md, research.md, data-model.md, contracts/, tests exist
- [ ] **Constitution Compliant**: No unresolved rule violations
- [ ] **User Informed**: User understands error and resolution
- [ ] **Recovery Logged**: Error and recovery tracked in session memory

---

## Planning Strategy

**Note**: Context window management is handled automatically by the CLI's auto-compact feature. Focus on codebase complexity and scope instead.

### Scope Assessment

- **Codebase Size**: [Small (<20 files) / Medium (20-50 files) / Large (>50 files)]
- **Research Scope**: [Small/Medium/Large] - Based on unknowns to resolve
- **Agent Assistance Recommended**: [Yes/No] - For large codebases (>50 files)

### Agent Assistance (If Applicable)
*Only fill if agent assistance is recommended for large codebase exploration*

- **Research Questions**: [List specific research questions for @general agent]
- **Analysis Tasks**: [List analysis tasks requiring deep focus]

---

## Technical Context
*This section is filled out by the AI based on the project's existing context and the new feature spec.*

- **Language/Framework**: [e.g., TypeScript, React, Node.js or NEEDS CLARIFICATION]
- **Primary Dependencies**: [e.g., Next.js, Express, Zod or NEEDS CLARIFICATION]
- **Storage**: [e.g., PostgreSQL, Firestore, S3 or NEEDS CLARIFICATION]
- **Testing**: [e.g., Jest, Playwright, Vitest or NEEDS CLARIFICATION]
- **Project Type**: [e.g., Monorepo, Web App, Standalone Service - determines source structure]

## Constitution Check
*GATE: Must pass before and after the design phase. The AI must list each applicable rule from the project's constitution and provide evidence of compliance.*

- **Rule 1 (e.g., Component Reusability)**: [EVIDENCE: Summary of search for existing components to reuse].
- **Rule 2 (e.g., Data Operation Handlers)**: [EVIDENCE: Link to proposed interface definitions with onSave/onEdit/onDelete handlers].
- **Rule 3 (e.g., Domain-First Principle)**: [EVIDENCE: Link to proposed domain model changes].

## Project Structure
*The AI selects the appropriate structure based on the `Project Type` identified in the Technical Context.*

### Option 1: Web Application
```
frontend/
backend/
packages/
```

### Option 2: Standalone Service
```
src/
  ├── api/
  ├── services/
  └── domain/
tests/
```

**Structure Decision**: [AI selects and justifies the chosen structure].

---

## Phase 0: ACE-Enhanced Research & Exploration
*The AI identifies and systematically researches all unknowns using Advanced Context Engineering principles.*

### Research Strategy Selection
*Choose strategy based on Scope Assessment above*

#### Option 1: Direct Research (Small/Medium Codebase)
- Systematically explore codebase to resolve `[NEEDS CLARIFICATION]` markers
- Focus on targeted exploration and pattern recognition
- Apply selective file reading

#### Option 2: Agent-Assisted Research (Large Codebase, >50 files)
- Use @general agent to assist with codebase research:
  - Focus research on resolving `[NEEDS CLARIFICATION]` markers
  - Investigate architecture, patterns, dependencies, and constraints
  - Provide detailed findings for technical planning
- Use @general for technical deep-dives if needed
- Integrate findings into planning context

### Systematic Exploration Protocol
*Apply regardless of strategy selected*

1. **Architecture Understanding**: Map high-level system architecture and data flow
2. **Pattern Recognition**: Identify existing patterns, conventions, and architectural decisions
3. **Dependency Analysis**: Understand technology stack and integration patterns
4. **Interface Discovery**: Locate key APIs, data models, and integration points
5. **Constraint Identification**: Discover technical, security, and performance constraints

### Research Quality Gates
- [ ] **Completeness**: All `[NEEDS CLARIFICATION]` markers resolved with evidence
- [ ] **Accuracy**: Technical findings verified through code examination
- [ ] **Relevance**: Research focused on feature implementation requirements

**Output**: A `research.md` file with all `[NEEDS CLARIFICATION]` markers resolved.

## Phase 1: Design & Contracts
*The AI designs the core components of the feature based on the spec and research.*

1.  **Data Models**: Define entities, fields, and relationships in `data-model.md`.
2.  **API Contracts**: Define endpoints and schemas (e.g., OpenAPI, gRPC) in the `/contracts` directory.
3.  **Failing Tests**: Create placeholder integration or unit tests that will fail until the implementation is complete.

**Output**: `data-model.md`, `/contracts/*`, failing test files.

## Phase 2: Task Planning Approach
*This section describes what the `/tasks` command will do. The `/plan` command does not execute this.*

- **Strategy**: The `/tasks` command will load the design artifacts from Phase 1 and generate a detailed, ordered list of implementation tasks in `tasks.md`, following a Test-Driven Development (TDD) approach.

---

## Complexity Tracking
*The AI documents any necessary deviations from the constitution here.*

| Violation | Justification | Alternative Rejected Because... |
| :--- | :--- | :--- |
| [e.g., Introducing new library] | [Why it is critically needed] | [Why existing libraries are insufficient] |