---
description: Execute polish-test-plus workflow step
---

# Additional Test Generation

**Input**: Path to a source code file and its corresponding test file.
**Context**: The feature specification, which describes the intended behavior.

## Execution Flow
1.  Read both the source code file and its existing test file.
2.  Analyze the source code's logic to identify edge cases, boundary conditions, and potential error states that are not covered by the existing tests.
3.  Common areas to check: null inputs, empty arrays/objects, invalid data types, off-by-one errors.
4.  Generate new test cases to cover these identified scenarios.
5.  Add the new test cases to the existing test file.

---

## Analysis

**Identified Edge Cases Not Covered**:
- [Edge case 1]
- [Edge case 2]

## New Test Cases

```[language]
// The new test cases to be added to the test file.
```
