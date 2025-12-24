---
description: Execute polish-pr-summary workflow step
---

# Pull Request Summary Generation

**Input**: A git diff or a list of changed files for the feature.
**Context**: The original feature `spec.md` and `plan.md`.

## Execution Flow
1.  Analyze the provided diff to understand the scope of the changes.
2.  Reference the `spec.md` to understand the **"why"** behind the changes (the user-facing problem being solved).
3.  Reference the `plan.md` to understand the technical approach that was taken.
4.  Generate a clear and concise summary for the pull request body.
5.  The summary should include:
    - A high-level description of the feature or fix.
    - A list of the key technical changes.
    - Instructions on how to test or verify the changes.

---

## Generated PR Summary

### Description

This PR introduces [feature name or bug fix], which allows users to [achieve goal from spec.md]. It addresses [problem from spec.md].

### Key Changes

-   Created a new `[ServiceName]` to handle [business logic].
-   Added a new endpoint `POST /api/[resource]`.
-   Updated the `[Component]` to include the new UI elements.

### How to Test

1.  Run the application.
2.  Navigate to the `[new page or feature area]`.
3.  Follow the acceptance scenarios outlined in the `spec.md`.
4.  Verify that all new tests pass.
