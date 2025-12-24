---
description: Execute polish-refactor workflow step
---

# Code Refactoring

**Input**: Path to a source code file.
**Context**: The project constitution, especially rules regarding performance, patterns, and code style.

## Execution Flow
1.  Read the source code file provided.
2.  Analyze the code for potential improvements based on the project's constitution and general best practices.
3.  Look for: code smells, performance bottlenecks, overly complex logic, or deviations from established patterns.
4.  Provide specific, actionable suggestions for improvement. For each suggestion, show the **original code** and the **proposed refactored code**.
5.  Explain **why** each change is recommended.

---

## Refactoring Suggestions

### Suggestion 1: [e.g., Simplify Complex Conditional]

**Reasoning**: [Explain why the change is an improvement].

**Original Code**:
```[language]
// Snippet of the original code to be changed.
```

**Refactored Code**:
```[language]
// The proposed new code.
```
