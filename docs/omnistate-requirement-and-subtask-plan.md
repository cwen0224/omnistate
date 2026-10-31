# OMNISTATE Requirement, Checklist, and Subtask Plan

This proposal makes planning a first-class part of every prompted transaction. Before implementation, OMNISTATE records the original user request, references, non-goals, acceptance criteria, checklist items, implementation subtasks, verification subtasks, and assigned agents.

The audit gate blocks a planned transaction when the memo is missing, a checklist item has no linked subtask, a subtask is unfinished, or a checklist item is not `PASS`/`DEFERRED`. Conflicting agent conclusions must be recorded as `CONFLICTED` and cannot be treated as a pass.

Required lifecycle:

1. `begin` creates the transaction and declares scope.
2. `memo --prompt` records the complete user request and references.
3. `checklist add` records each acceptance item.
4. `subtask add` and `checklist link` build the dependency-aware work graph.
5. `subtask assign` delegates implementation or independent verification.
6. `plan-review` activates an independent subagent after the first plan and records alignment findings, omissions, conflicts, and better approaches.
7. Resolve review findings with `APPROVED` or `RESOLVED`; `CHANGES_REQUIRED` and `CONFLICTED` block audit.
8. `subtask result` and `checklist status` record evidence and PASS/FAIL.
9. Primary inspection and independent subagent inspection run on fresh artifacts.
10. `audit` enforces scope, tests, memo/checklist/subtask completion, review completion, and evidence.
11. `finish` is allowed only after every required item passes.

The regression case is a card-hand hover requirement: hover must enlarge and lift the card, and exit must restore its original scale and position. It must be represented in the memo, checklist, implementation subtask, visual verification subtask, and evidence before a transaction can finish.
