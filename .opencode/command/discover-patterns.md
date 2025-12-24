---
description: Pattern discovery - delegates to @pattern-discovery agent
---

# Pattern Discovery Command (Delegation Wrapper)

This command automatically delegates to the specialized `@pattern-discovery` subagent for comprehensive architectural analysis and design pattern identification.

## Usage

```bash
# Command syntax (auto-delegates)
/discover-patterns [target]

# Examples:
/discover-patterns .
/discover-patterns src/components/
/discover-patterns "How do we handle state in this app?"
```

## What Happens

1. Parses target input (file path, directory, or concept)
2. Invokes @pattern-discovery subagent with:
   - Target scope/concept
   - Project RULES.md (existing patterns)
   - Current pattern library in .bifrost/patterns/
3. Returns structured pattern discovery report

## Direct Agent Invocation

You can also invoke the agent directly:

```bash
@pattern-discovery src/features/payment/
```

## Output

Comprehensive architectural report covering:

### Evaluation Dimensions
- **High-Level Architecture**: Structure, data flow, layer separation.
- **Design Patterns**: Creational, structural, and behavioral patterns.
- **Modularity**: Boundary analysis and coupling.
- **Reusability**: Candidates for template formalization.

### Report Structure
- **High-Value Patterns**: Candidates for the template library.
- **Medium-Value Patterns**: Local or context-specific solutions.
- **Anti-Patterns**: Areas needing refactoring or standardization.
- **Action Plan**: Steps to formalize and adopt patterns.

## Agent Configuration

- **Temperature**: 0.3 (balanced analysis with creative pattern recognition)
- **Tools**: Read-only (no code modifications)
- **Webfetch**: Enabled (can reference standard architectural patterns)
