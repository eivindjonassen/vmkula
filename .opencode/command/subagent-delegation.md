---
description: Delegate complex tasks to specialized subagents for optimal context management
---

# Subagent Delegation: Large-Scale Project Management

**Command**: `/subagent-delegate`
**Input**: Task scope and context requirements
**Purpose**: Delegate complex tasks to specialized subagents for optimal context management

## Execution Flow
1. **Scope Assessment**: Evaluate task complexity and context requirements
2. **Delegation Decision**: Determine if subagent delegation is warranted
3. **Subagent Selection**: Choose appropriate specialized agent type
4. **Context Package Creation**: Prepare focused context for subagent
5. **Mission Definition**: Create clear, bounded objectives
6. **Handoff Execution**: Transfer task to subagent with success criteria
7. **Integration Planning**: Define how results will integrate with main workflow

---

## Important Note

**Context window management is handled automatically by the CLI's auto-compact feature.** Base delegation decisions on task complexity and scope, not context percentages.

---

## Delegation Decision Matrix

### When to Delegate to Subagents

#### Scope-Based Triggers
- **Large Codebase Research**: >50 files to analyze or understand
- **Complex Implementation**: >5 files to modify, multiple systems involved
- **Multiple Domains**: Task spans different technical areas
- **Deep Analysis Required**: Security, performance, or architecture review

#### Task-Based Triggers
- **Large Codebase Exploration**: Understanding architecture across many files
- **Comprehensive Security Analysis**: Multiple attack vectors and components
- **Cross-Project Pattern Analysis**: Identifying patterns across repositories
- **Deep Dependency Analysis**: Understanding complex technology stacks
- **Performance Optimization**: Requires detailed profiling and analysis

### When NOT to Delegate
- **Simple Tasks**: Can be completed in <30 minutes of focused work
- **Focused Scope**: 1-3 files to modify
- **High Integration Overhead**: Task results require extensive re-integration
- **Critical Path Dependencies**: Task blocks other essential work

## Subagent Types and Specializations

### Research Agent (`/research-agent`)
**Purpose**: Systematic exploration and understanding of codebases, technologies, and patterns

#### Ideal For:
- Large codebase architecture analysis (>50 files)
- Technology stack research and evaluation
- Pattern discovery across multiple projects
- API and dependency exploration
- Competitor analysis and technical research

#### Input Package:
```
MISSION: [Specific research question or exploration goal]
SCOPE: [Directories, files, or domains to investigate]
FOCUS: [Key aspects to prioritize in research]
CONSTRAINTS: [Limitations, time bounds, access restrictions]
SUCCESS_CRITERIA: [Measurable outcomes expected]
INTEGRATION_NEEDS: [How results will be used in main workflow]
```

#### Expected Output:
- Executive summary (<500 words)
- Detailed findings report (research.md)
- Actionable recommendations
- Architecture diagrams or patterns identified
- Critical unknowns requiring follow-up

### Implementation Agent (`/implement-agent`)
**Purpose**: Focused implementation of specific features or components

#### Ideal For:
- Large feature implementation across multiple files
- Complex refactoring operations
- Integration of multiple components
- Performance optimization implementation
- Migration and upgrade tasks

#### Input Package:
```
TASK: [Specific implementation objective]
SPECIFICATIONS: [Requirements and design artifacts]
CODEBASE_CONTEXT: [Relevant existing code and patterns]
CONSTRAINTS: [Technical limitations, style requirements]
TEST_REQUIREMENTS: [Testing expectations and existing test patterns]
INTEGRATION_POINTS: [How this connects to broader system]
```

#### Expected Output:
- Implemented code with documentation
- Test coverage for new functionality
- Integration notes and requirements
- Performance impact assessment
- Rollback plan and risk mitigation

#### Minimal Context Package for Single-Task Delegation

**Use Case**: Delegating individual task implementation from `/implement` or `/implement-yolo` when task complexity is high (>5 files, multiple systems).

**Philosophy**: For single-task delegation during batch workflows, pass ONLY what's essential. Comprehensive context packages are for large multi-task features, not individual task delegation.

**Essential Context (Always Include)**:
1. **Task Specification**: Task ID, description, and requirements from tasks.md (THIS task only)
2. **Relevant Code Files**: Specific files this task modifies or creates (listed in task)
3. **Constitution**: Project constitution (RULES.md) - coding standards and patterns
4. **Success Criteria**: Test requirements and acceptance criteria for THIS task specifically
5. **Return Format**: How to hand results back to parent (implementation complete, test status)

**Exclude (Not Needed for Single Tasks)**:
- ❌ Full spec.md (task already has requirements distilled)
- ❌ Full plan.md (task already has design decisions distilled)
- ❌ Other tasks (subagent focuses on ONE task only)
- ❌ Session history (not relevant to implementation)
- ❌ Workflow coordination (parent handles this)

**Scope Boundaries**:
```
IN SCOPE:
- Implement ONLY Task [task-id]
- Follow constitution and patterns
- Return implementation for parent integration

OUT OF SCOPE:
- Do NOT implement other tasks
- Do NOT modify task list or workflow files
- Do NOT record metrics (parent handles this)
- Do NOT update session memory (parent handles this)
```

**Parent Responsibilities** (when delegating):
- Record task-start metrics BEFORE delegation
- Load spec/plan context to prepare minimal package
- Delegate task to subagent with focused context
- Integrate subagent implementation results
- Record task-end metrics AFTER integration
- Update session memory and checkpoint

**Example Minimal Context Package**:
```
## SUBAGENT MISSION: Implement Task T014

### Task Specification
**Task ID**: T014
**Description**: Add JWT token validation to auth middleware
**File**: src/middleware/auth.ts
**Dependencies**: T012 (JWT library integration) - Complete
**Parallel**: No

### Relevant Code Files
- src/middleware/auth.ts (modify - add validation logic)
- src/types/auth.ts (reference - JWT token interface)
- tests/middleware/auth.test.ts (update - add validation tests)

### Constitution (from RULES.md)
- Use TypeScript strict mode with explicit types
- Follow existing error handling patterns (throw AuthError)
- Middleware must be async and call next() on success
- Tests must cover success and failure cases

### Success Criteria
- JWT validation middleware function implemented
- Handles valid tokens (calls next())
- Handles invalid tokens (throws AuthError)
- Handles missing tokens (throws AuthError)
- Tests pass for all cases

### Return Format
Return implementation with:
- Modified files and code
- Test execution results (pass/fail)
- Integration notes (any breaking changes or dependencies)
```

**When to Use Minimal vs. Comprehensive**:
- **Minimal**: Single task from `/implement` batch (complex task >5 files)
- **Comprehensive**: Large multi-task feature, complex refactor, architectural change

### Analysis Agent (`/analysis-agent`)
**Purpose**: Deep analysis of architecture, security, performance, and quality

#### Ideal For:
- Security vulnerability assessment
- Performance bottleneck identification
- Architecture quality analysis
- Technical debt assessment
- Compliance and standards review

#### Input Package:
```
ANALYSIS_TYPE: [Security/Performance/Architecture/Quality]
TARGET: [Code areas, components, or systems to analyze]
CRITERIA: [Standards, benchmarks, or requirements to evaluate against]
DEPTH: [Surface/Detailed/Comprehensive analysis level]
RISK_TOLERANCE: [Acceptable vs. critical issues]
REPORTING_FORMAT: [Executive summary, detailed report, actionable plan]
```

#### Expected Output:
- Risk assessment and prioritization
- Detailed findings with evidence
- Remediation recommendations
- Impact analysis for suggested changes
- Monitoring and prevention strategies

## Context Package Preparation

### Essential Context (Always Include)
1. **Project Constitution**: Core principles and constraints from RULES.md
2. **Current Objective**: High-level goal that subagent task supports
3. **Technical Context**: Relevant languages, frameworks, and patterns
4. **Integration Requirements**: How subagent output will be used

### Mission-Specific Context
#### For Research Agents
- Specific research questions or hypotheses
- Existing knowledge and assumptions to validate
- Key technologies or patterns to investigate
- Success criteria for research completion

#### For Implementation Agents
- Feature specifications and requirements
- Relevant existing code and interfaces
- Testing patterns and quality standards
- Performance and security requirements

#### For Analysis Agents
- Analysis scope and depth requirements
- Standards and criteria for evaluation
- Risk tolerance and compliance needs
- Expected deliverable format and detail

### Context Optimization for Subagents
```
COMPRESSION STRATEGY:
- Project Background: High-level summary only (50-100 words)
- Technical Stack: Key technologies and versions only
- Architecture: Focus on areas relevant to subagent mission
- Constraints: Only those that affect subagent work

EXPANSION STRATEGY:
- Mission Details: Comprehensive and unambiguous
- Success Criteria: Specific and measurable
- Integration Points: Detailed handoff requirements
- Quality Standards: Complete expectations and examples
```

## Subagent Coordination Protocols

### Mission Definition Template
```
## SUBAGENT MISSION: [Agent Type]

### Primary Objective
[Clear, specific goal that subagent should achieve]

### Scope Boundaries
**IN SCOPE**: [Specific areas, files, or aspects to address]
**OUT OF SCOPE**: [Areas to explicitly avoid or defer]

### Success Criteria
1. [Measurable outcome 1]
2. [Measurable outcome 2]
3. [Measurable outcome 3]

### Constraints
- **Time**: [Expected completion timeframe]
- **Technical**: [Technology or architecture constraints]
- **Quality**: [Standards and requirements to maintain]
- **Integration**: [How output must fit with existing work]

### Deliverables
- **Primary**: [Main output expected]
- **Supporting**: [Additional documentation or artifacts]
- **Handoff Package**: [Information needed for integration]

### Integration Plan
[How subagent output will be incorporated into main workflow]
```

### Handoff Execution
1. **Context Validation**: Verify subagent has sufficient context
2. **Mission Clarity**: Confirm subagent understands objectives
3. **Success Criteria Agreement**: Align on measurable outcomes
4. **Communication Protocol**: Establish check-in and completion signals
5. **Escalation Path**: Define when to return control to main agent

### Integration Protocols
1. **Output Validation**: Verify subagent delivered expected results
2. **Quality Assessment**: Ensure output meets project standards
3. **Context Integration**: Incorporate findings into main workflow
4. **Next Steps Planning**: Define follow-up actions based on results
5. **Learning Capture**: Document insights for future delegations

## Quality Assurance

### Pre-Delegation Checklist
- [ ] **Clear Mission**: Objective is specific and measurable
- [ ] **Sufficient Context**: Subagent has information needed for success
- [ ] **Bounded Scope**: Task has clear boundaries and constraints
- [ ] **Integration Plan**: Clear path for incorporating results
- [ ] **Success Criteria**: Measurable outcomes defined
- [ ] **Risk Assessment**: Potential issues identified and mitigated

### Post-Integration Validation
- [ ] **Completeness**: All expected deliverables received
- [ ] **Quality**: Output meets project standards and requirements
- [ ] **Integration**: Results successfully incorporated into workflow
- [ ] **Value**: Delegation provided net benefit over direct execution
- [ ] **Learning**: Insights captured for improving future delegations

## Emergency Protocols

### When Subagent Delegation Fails
1. **Rapid Assessment**: Understand scope and impact of failure
2. **Context Recovery**: Reconstruct essential context for continuation
3. **Alternative Strategy**: Switch to direct execution or different subagent
4. **Timeline Adjustment**: Revise project timeline if necessary
5. **Learning Capture**: Document failure mode for prevention

### Context Continuity Failure
1. **Context Reconstruction**: Rebuild essential project context
2. **Progressive Recovery**: Gradually restore full workflow context
3. **Checkpoint Validation**: Verify reconstruction accuracy
4. **Quality Gate**: Ensure workflow quality maintained despite disruption

## Performance Optimization

### Delegation Efficiency Metrics
- **Task Completion Time**: Subagent completion vs. direct execution
- **Output Quality**: Comparable or superior to direct execution
- **Integration Effort**: Minimal effort required to incorporate results

### Continuous Improvement
- Track delegation success rates by task type
- Identify optimal context package sizes for each agent type
- Refine mission definition templates based on experience
- Optimize handoff protocols for efficiency

---

## Integration with Main Workflow

### Automatic Delegation Triggers
```
IF research_scope > 50_files
  THEN recommend_research_agent()

IF task_complexity > HIGH AND files_to_modify > 5
  THEN recommend_implementation_agent()

IF deep_analysis_required (security, performance, architecture)
  THEN recommend_analysis_agent()
```

### Manual Delegation Commands
- `/delegate-research [scope] [questions]` - Research agent delegation
- `/delegate-implement [task] [specifications]` - Implementation agent delegation
- `/delegate-analyze [type] [target] [criteria]` - Analysis agent delegation

This subagent delegation system enables the main workflow to maintain high-quality context while handling arbitrarily complex projects through systematic task distribution and coordination.