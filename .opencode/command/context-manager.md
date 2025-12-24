---
description: Guide effective use of subagent delegation for complex tasks
---

# Context Management: Subagent Delegation Guide

**Command**: `/context-manager`
**Input**: Current project state and task requirements
**Purpose**: Guide effective use of subagent delegation for complex tasks

## Important Note

**Context window management is handled automatically by the CLI's auto-compact feature.** You don't need to estimate or track context percentages - the CLI will automatically compact context when needed.

This template focuses on **when and how to use subagent delegation** based on task complexity and scope, not context utilization.

---

## When to Use Subagent Delegation

### Delegation Triggers (Based on Scope)
- **Large Codebase Research** (>50 files to analyze)
- **Comprehensive Dependency Analysis** (>20 technologies)
- **Cross-Pattern Discovery** (multiple modules/domains)
- **Security Analysis** (large attack surface)
- **Complex Implementation Tasks** (>5 files, multiple systems)

### When NOT to Delegate
- Simple, focused tasks (1-3 files)
- Tasks you can complete directly
- When the overhead of delegation exceeds the benefit

---

## Subagent Types and Responsibilities

### Research Agent
- **Purpose**: Systematic codebase exploration and analysis
- **Input**: Specific research questions + target directories/files
- **Output**: Structured findings summary + detailed research.md
- **Use When**: Exploring unfamiliar codebases or resolving many unknowns

### Implementation Agent
- **Purpose**: Focused implementation of specific tasks
- **Input**: Task specification + relevant code context + design artifacts
- **Output**: Implemented code + test results + integration notes
- **Use When**: Task touches >5 files or spans multiple systems

### Analysis Agent
- **Purpose**: Deep analysis of architecture, patterns, dependencies
- **Input**: Analysis scope + specific questions + target areas
- **Output**: Analysis report + recommendations + risk assessment
- **Use When**: Need comprehensive technical analysis

---

## Subagent Delegation Protocol

### 1. Delegation Decision

Ask yourself:
- Is this task touching >5 files or multiple systems? → Consider delegation
- Am I exploring >50 files in an unfamiliar codebase? → Delegate research
- Is this a focused, simple task? → Do it directly

### 2. Handoff Information Package

Provide subagents with:
- **Context Summary**: Current project state in <500 tokens
- **Specific Mission**: Clear, bounded objective
- **Success Criteria**: Measurable outcomes expected
- **Scope Boundaries**: What's IN and OUT of scope

### 3. Return Integration

Expect from subagents:
- **Executive Summary**: Key findings in <200 tokens
- **Detailed Report**: Full analysis in separate document (if needed)
- **Action Items**: Specific next steps
- **Integration Notes**: How to incorporate results

---

## Information Hierarchy

### Essential (Always Keep)
- Project constitution and core principles
- Current feature specification
- Critical architectural constraints
- Active task context

### Summarizable (Compact for Efficiency)
- Historical feature implementations → High-level patterns
- Detailed code analysis → Key architectural insights
- Research findings → Core conclusions with references

### Delegatable (Move to Subagents)
- Large codebase exploration
- Comprehensive dependency analysis
- Pattern discovery across multiple files
- Security analysis of large codebases

---

## Phase Transition Guidelines

### Spec → Plan
- **Preserve**: Complete specification, constitution, requirements
- **Summarize**: User research, stakeholder feedback
- **Delegate**: Large-scale technical research (>50 files)

### Plan → Tasks
- **Preserve**: Technical plan, architecture decisions, data models
- **Summarize**: Research findings into key constraints
- **Delegate**: Complex dependency analysis

### Tasks → Implementation
- **Preserve**: Current task, relevant test cases, interface definitions
- **Summarize**: Overall feature context into implementation context
- **Delegate**: Complex tasks (>5 files, multiple systems)

### Implementation → Polish
- **Preserve**: Recent implementation, test results, integration status
- **Summarize**: Development process into change summary
- **Delegate**: Comprehensive quality analysis

---

## Integration with Existing Workflow

Use this guide when:
- **Before Planning**: For large codebase research
- **Before Implementation**: For complex multi-file tasks
- **During Complex Features**: When tasks span multiple systems

The CLI handles context automatically - focus on task complexity and scope when deciding whether to delegate.
