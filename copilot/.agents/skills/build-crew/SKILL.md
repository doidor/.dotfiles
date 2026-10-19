---
name: build-crew
description: Implement a finalized plan with Copilot CLI engineering agents and a paranoid review-and-repair loop. Use only when the user explicitly invokes build-crew to execute a plan, not when planning or installing this skill. Requires Copilot CLI's native agent tools and the paranoid agent.
disable-model-invocation: true
---

# Build Crew

Turn a finalized plan into the smallest working change, then keep fixing and
checking it until the independent review is clear.

```text
Plan -> Engineers -> Checks -> Paranoid -> Clean? --yes--> Done
             ^                              |
             +--------- fixes/evidence -----+ no
```

## Start only when asked

- This is a Copilot CLI workflow, even though it lives in the shared personal
  skills directory. Require native agent delegation and the `paranoid` agent.
  If either is unavailable, explain what is missing and pause. Do not substitute
  another CLI, a generic reviewer, or a single-agent implementation.
- Run only on an explicit request to use `build-crew` to implement a plan.
  Do not run while creating a plan, reviewing a plan, or installing this skill.
- Read an explicitly supplied plan file if there is one. Otherwise read the
  current session's saved plan afresh, using its known path from the session
  context. If there is no saved plan, use the latest clearly finalized plan in
  the conversation. Do not search other sessions or projects for a plan.
- Ask for clarification if the plan is missing, unfinished, conflicting, or
  ambiguous. Do not invent missing requirements.
- Treat invocation as a request to implement that plan, not as permission to
  bypass plan-mode approval, tool permissions, or the agent tools' own rules.
- Respect configured models and resource limits. Do not invent model overrides,
  agent-count quotas, credit budgets, or a fixed review-round limit.

## Assign small, clearly owned tasks

Record the starting state, including existing staged, unstaged, and untracked
changes. Keep unrelated work untouched. For files outside Git, record their
starting contents or absence in private session storage so later review can
distinguish this task's changes. Do not copy credentials or unrelated app data.

Break the plan into meaningful tasks with dependencies and acceptance checks.
Use the fewest engineering agents needed. Run independent tasks concurrently
only when they own different files; sequence dependent work and coordinate
shared-file edits. Do not split a tightly coupled change just to create a team.
The coordinator owns task tracking and integration, not duplicate implementation
of an engineer's active assignment.

Use native engineering agents, normally `general-purpose`, with complete context.
Include all of the following in every assignment and repair request:

- The plan, assigned requirements, expected behavior, and acceptance checks.
- Allowed files, dependencies, existing work to preserve, and relevant commands.
- **KISS:** choose the smallest direct solution that fully solves the problem.
  Avoid unnecessary abstractions, dependencies, configurability, and cleanup.
- **DRY:** reuse existing helpers and shared behavior rather than copy-pasting
  logic. Do not create a new abstraction without a concrete need.
- **Least surprise:** follow existing patterns and preserve expected behavior.
  Make intentional behavior changes only when the plan requires them.
- Run focused checks and report actual changes, commands, results, and blockers.
  Do not report a check as passing if it was skipped or could not run.
- Do not invoke `build-crew` recursively, create duplicate worker teams, or
  commit, push, or deploy unless the selected plan explicitly requests it.

Retain agent identifiers and task ownership. Continue the same agents for
same-task repairs using the native follow-up tools. Do not repurpose an agent
for an unrelated task or duplicate an active assignment. Follow the tools'
completion and waiting rules before starting dependent work. If continuation
is unavailable, report the blocked step instead of silently starting over.

## Check, review, and repair

1. Collect the engineering results and check them against the entire plan.
   Run the project's appropriate tests, builds, and linters. Distinguish
   pre-existing failures and optional, unrelated skips from missing validation
   of the changed behavior.
2. Ask `paranoid` to independently review all changes made for this plan,
   including new and untracked files and any non-Git files. Supply the original
   plan, acceptance criteria, starting-state boundaries, changed files or
   before/after differences, and actual check commands and results.
   Exclude unrelated pre-existing changes from the proposed change.
3. Preserve the reviewer's existing read-only role and evidence requirements.
   It should inspect the changes itself, not accept an engineer's assurance
   that they are correct. Do not request edits, commits, or network changes
   from the reviewer.
4. Keep a list of confirmed findings, relevant unverified concerns, validation
   gaps, owners, and their current status. "No confirmed defects" is not a clean
   review if relevant concerns or required checks remain unresolved.
5. Send confirmed findings to their engineering owners for minimal repairs.
   Send unverified concerns for focused investigation before changing code.
   Engineers may disprove a concern with evidence; only close it after
   `paranoid` verifies that evidence and clears it.
6. After repairs, rerun the affected checks and continue the same `paranoid`
   agent. Request review of the complete task change against the original plan,
   not only the latest fix. Do not silently dismiss a finding or change the
   requirements to make the review pass.
7. Repeat while useful repair or verification work remains. Pause and explain
   the blocker if checks cannot run, a required agent is unavailable, limits
   are reached, or the same issue returns without meaningful progress or a
   viable new approach. Do not spin indefinitely or present a blocked run as
   complete.

## Finish honestly

Finish only when every plan item is satisfied, required checks pass, and
`paranoid` has no confirmed defects or unresolved relevant concerns or
validation gaps.

Follow the user's reply preferences. Summarize the implemented result, checks,
review scope, and any remaining limitations. Use a diagram when it helps explain
the result. Report that the reviewer found no confirmed defects in the inspected
scope; do not claim that this proves the change is correct in every situation.

Leave changes uncommitted unless the plan explicitly asks for publication.
Normal approval and permission requirements still apply to commits, pushes,
deployments, and all other actions.
