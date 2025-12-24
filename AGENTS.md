# vmkula - AI Development Context

**Project:** vmkula
**Setup Date:** 2025-12-24
**Location:** ./

## Project Overview

This project uses the Bifrost AI Spec Development Kit for structured AI-driven development.

## Bifrost Configuration

```yaml
# Machine-parseable Bifrost settings
bifrost:
  version: "1.0"
  tdd_enforcement: true
  working_memory_limit: 50
  auto_checkpoint: true
  context_pruning: true

workflow:
  default_branch: main
  spec_dir: specs/
  commands_dir: .opencode/command/

quality_gates:
  spec_validation: true
  plan_validation: true
  test_coverage_threshold: 80
```

## 🔒 Constitutional Compliance (MANDATORY)

**CRITICAL**: RULES.md is this project's constitution and MUST be followed for ALL code changes, whether using slash commands or conversational coding.

### Before ANY Code Change:

1. **Load RULES.md first** - Always review relevant sections before writing code
2. **Check for reusable components** - Search codebase for existing atoms/components (Storybook, design system, shared utilities)
3. **Check for MCP server instructions** - Review RULES.md for custom MCP server configuration and usage requirements
4. **Verify i18n requirements** - Ensure translations are complete for all supported languages
5. **Follow code style** - Match existing patterns, naming conventions, and formatting
6. **Validate architecture** - Use approved patterns and technologies from RULES.md

### Conversational Coding Guidelines

When working conversationally (without slash commands like /spec, /plan, /implement):

**You MUST still follow the constitution:**
- ✅ Load RULES.md sections relevant to your change
- ✅ Search for reusable components before creating new ones
- ✅ Check for MCP server instructions in RULES.md
- ✅ Check i18n/translation requirements
- ✅ Follow established code style and patterns
- ✅ Use approved libraries and technologies

**Quick != Skip Rules**
- Conversational coding is for speed, not for bypassing standards
- Constitutional compliance is mandatory regardless of workflow method

### Common Pitfalls to Avoid

❌ **Component Duplication**: Creating custom buttons/tables/forms instead of reusing Storybook atoms or design system components

❌ **Missing Translations**: Forgetting to add translations for all supported languages (check RULES.md for i18n requirements)

❌ **Style Inconsistency**: Not following established naming conventions, file structure, or formatting rules

❌ **Unapproved Libraries**: Using libraries or frameworks not listed in RULES.md technology stack

❌ **Reinventing Utilities**: Writing custom utilities when shared functions already exist

### Constitutional Compliance Checklist

Before committing ANY code change, verify:
- [ ] Loaded and reviewed relevant RULES.md sections
- [ ] Searched for reusable components/utilities
- [ ] Checked for MCP server instructions
- [ ] All translations added/updated
- [ ] Code style matches existing patterns
- [ ] Used approved technologies and patterns
- [ ] No duplicate functionality created

## Professional Objectivity

Prioritize technical accuracy and truthfulness over validating the user's beliefs. When the user proposes an approach:

1. **Evaluate independently** - Assess ideas on technical merits, not on who proposed them
2. **Disagree when warranted** - If you see issues or a better approach, say so directly
3. **Provide reasoning** - Back up disagreements with concrete technical rationale
4. **Avoid false agreement** - Don't say "Great idea!" then do something different
5. **Offer alternatives** - When disagreeing, propose what would work better and why

The goal is collaborative problem-solving, not approval-seeking. A respectful "I'd recommend a different approach because..." is more valuable than agreeing with a suboptimal solution.

## Development Workflow

### Structured Workflow (Recommended for Features)
- `/spec` - Create specifications from requirements
- `/plan` - Generate implementation plans
- `/tasks` - Break down into granular tasks
- `/implement` - Execute implementations
- `/polish-*` - Various polish operations (docs, refactor, security, etc.)

### Agent Assistance

For complex tasks spanning multiple files or systems, use @general agent for assistance:
- Focus on current task context
- Provide minimal context package (task spec, relevant files, constitution, success criteria)
- Maintain workflow control in main session

### Specialized Subagents

Bifrost includes specialized subagents for specific analysis tasks:

#### UX Review Agent (@ux-review)

**Type**: Subagent  
**Purpose**: Comprehensive user experience evaluation across 8 UX dimensions

**Expertise**:
- Accessibility compliance (WCAG 2.1 AA/AAA)
- Core UX laws (Fitts's, Hick's, Jakob's, Miller's)
- Mobile & responsive design
- Conversion optimization
- Information architecture
- Visual design & aesthetics
- Performance & perceived speed

**When to Use**:
- Evaluating component accessibility and usability
- Reviewing user flows and conversion funnels
- Auditing mobile responsiveness
- Assessing design consistency
- WCAG compliance checking

**Invocation**:
```bash
# Manual invocation
@ux-review src/components/LoginForm.tsx

# Multiple files
@ux-review src/pages/checkout/

# Conceptual review
@ux-review "Should I use bottom tabs or sidebar navigation?"

# Command wrapper (delegates to agent)
/ux-review src/components/Button.tsx
```

**Output**: Structured markdown report with severity-rated findings (Critical/High/Medium/Low) and actionable recommendations

**Configuration**:
- Temperature: 0.2 (balanced analysis with creative suggestions)
- Tools: Read-only (no code modifications)
- Webfetch: Enabled (can reference WCAG guidelines, design patterns)
- Model: Inherits from parent (flexible for fast vs comprehensive reviews)

#### Security Review Agent (@security-review)

**Type**: Subagent  
**Purpose**: Security vulnerability analysis and risk assessment

**Expertise**:
- OWASP Top 10 vulnerabilities
- Authentication & authorization patterns
- Input validation & sanitization
- Dependency vulnerability scanning
- Secrets management
- Secure configuration practices

**When to Use**:
- Identifying security flaws in code or architecture
- Reviewing authentication/authorization logic
- Auditing data handling and privacy
- General security hardening recommendations

**Invocation**:
```bash
# Manual invocation
@security-review src/auth/login.ts

# Command wrapper (delegates to agent)
/polish-security src/auth/login.ts
```

**Output**: Structured security report with severity-rated findings and prioritized remediation plan

**Configuration**:
- Temperature: 0.1 (deterministic security analysis)
- Tools: Read-only (no code modifications)
- Webfetch: Enabled (can reference CVE databases, OWASP)

#### Pattern Discovery Agent (@pattern-discovery)

**Type**: Subagent  
**Purpose**: Discovers and documents reusable architectural patterns

**Expertise**:
- Design patterns (GoF, etc.)
- Architectural styles (MVC, MVVM, etc.)
- Code organization and modularity
- Reusability analysis
- Anti-pattern detection

**When to Use**:
- Identifying recurring solutions for formalization
- Analyzing codebase for architectural consistency
- Finding candidates for template library
- Guidance on applying patterns to new features

**Invocation**:
```bash
# Manual invocation
@pattern-discovery src/components/

# Command wrapper (delegates to agent)
/discover-patterns src/components/
```

**Output**: Structured pattern discovery report with high-value reuse candidates and implementation templates

**Configuration**:
- Temperature: 0.3 (balanced analysis with creative pattern recognition)
- Tools: Read-only (no code modifications)
- Webfetch: Enabled (can reference standard architectural patterns)

#### Dependency Analysis Agent (@dependency-analysis)

**Type**: Subagent  
**Purpose**: Analyzes technology stack and dependency vulnerabilities

**Expertise**:
- Package ecosystems (npm, pip, cargo, go mod)
- Supply chain security
- Tech stack analysis & architectural inference
- License compliance
- Version management & upgrade planning

**When to Use**:
- Auditing project dependencies for vulnerabilities
- Identifying outdated packages and upgrade paths
- Inferring architecture from tech stack
- Cleaning up unused dependencies

**Invocation**:
```bash
# Manual invocation
@dependency-analysis .

# Command wrapper (delegates to agent)
/analyze-dependencies .
```

**Output**: Comprehensive dependency health report and tech stack overview

**Configuration**:
- Temperature: 0.1 (deterministic dependency analysis)
- Tools: Bash (read-only data collection), Webfetch (registry lookups)
- Permissions: Restricted bash access for `npm list`, `pip freeze`, etc.

### Quick Iterative Changes (Vibe-Coding)
For small, incremental changes you can work conversationally, but:
1. MUST still follow RULES.md (see Constitutional Compliance section above)
2. MUST check for reusable components first
3. MUST complete translations
4. MUST follow code style and patterns

## Development Rules

⚠️ **READ RULES.md BEFORE EVERY CODE CHANGE**

See `RULES.md` in project root for:
- **Code Style**: Naming conventions, file structure, formatting standards
- **Reusable Components**: Storybook atoms, design system, shared utilities
- **i18n Requirements**: Translation languages, format, completion requirements
- **Architecture Patterns**: Component structure, state management, data flow
- **Technology Stack**: Approved libraries, frameworks, tools
- **Testing Standards**: Test coverage, TDD approach, test structure
- **MCP Server Instructions**: Custom MCP server configuration and usage guidelines

## TDD State Machine

Bifrost enforces Test-Driven Development through a state machine:

```
IDLE → TEST_FAILING → IMPLEMENTING → TEST_PASSING → COMMITTED
```

State is tracked in `.bifrost/tdd-state.json`. Each implementation task should:
1. Start with a failing test (TEST_FAILING)
2. Implement until tests pass (IMPLEMENTING → TEST_PASSING)
3. Commit changes (COMMITTED → IDLE)

## Context Management

Bifrost automatically manages context through:
- **Working Memory**: Recent session context in `specs/[feature]/session.md`
- **Checkpoints**: Recovery points for pause/resume capability
- **Context Pruning**: Automatic summarization when context grows large

## Project Structure

Project structure will be updated as development progresses.

## Technologies

Technology stack will be auto-detected during development workflow.

---

**Remember**: RULES.md is your constitution. Quick changes don't mean skipping rules!
