---
name: prep-problem
description: >-
  Turn a coding-interview / LeetCode / FastPrep problem description into a local
  practice problem: solve it, invent edge-case inputs, and deterministically
  generate expected outputs from the solution oracle. Use when the user pastes
  a problem statement, asks to prep a question, generate tests, or set up local
  practice without manually entering testcases.
---

# Prep Problem (description → solved + tests)

Build a local practice problem from **only a question description**. Do **not** ask the user to supply test cases or expected outputs.

## Goal

1. Solve the problem correctly in Python.
2. Design strong **input** cases (examples + edge cases).
3. Generate **expected** values deterministically by running the solution as an oracle (`prep materialize`).
4. Verify with `prep run`. Optionally stash the solution for practice.

## Workflow (follow in order)

### 1. Extract metadata

From the description, determine:

- **title** — short problem name
- **slug** — kebab-case folder name (or let `prep` slugify the title)
- **entry** — usually `Solution.<methodName>` matching the signature in the prompt
- **constraints** — sizes, value ranges, uniqueness, sortedness, etc.

If the signature is ambiguous, pick a clear LeetCode-style `Solution` method and state it briefly.

### 2. Scaffold

```bash
python3 -m prep scaffold \
  --title "TITLE" \
  --entry "Solution.methodName" \
  --description-file /tmp/problem-desc.md
```

Write the full prompt into `/tmp/problem-desc.md` (or pass `--description`).

### 3. Write the solution

Edit `problems/<slug>/solution.py` with a correct, readable implementation.

- Prefer the standard library; no network I/O.
- Match the declared `entry`.
- Handle stated constraints and natural edge cases in the logic.

### 4. Design input-only cases

Write `/tmp/<slug>-cases.json` as a list of **inputs only** (no `expected`):

```json
{
  "cases": [
    { "name": "example-1", "args": [[2, 7, 11, 15], 9], "unordered": true },
    { "name": "empty-or-min", "args": [[1, 2], 3] },
    { "name": "edge-duplicates", "args": [[3, 3], 6], "unordered": true }
  ]
}
```

Follow `references/edge-cases.md` for what to cover. Include:

- Every example from the prompt (when runnable)
- Boundary / empty / single-element cases allowed by constraints
- Duplicates, negatives, zeros, sorted/unsorted as relevant
- At least one non-trivial mid-size case
- Set `"unordered": true` only when the problem allows any order

**Do not invent expected outputs by hand.** The oracle fills them.

### 5. Materialize expecteds (deterministic)

```bash
python3 -m prep materialize <slug> --cases-file /tmp/<slug>-cases.json --run
```

Same solution + same cases file ⇒ same `tests.json`. If materialize fails, fix the solution or invalid inputs, then retry.

### 6. Optional practice mode

If the user wants to re-solve it themselves:

```bash
python3 -m prep materialize <slug> --cases-file /tmp/<slug>-cases.json --run --practice
```

or after the fact:

```bash
python3 -m prep practice <slug>
```

This copies `solution.py` → `reference.py` and leaves a stub.

### 7. Report back

Tell the user:

- Problem path (`problems/<slug>/`)
- Entry point
- How many tests were generated
- `prep run <slug>` / `prep show <slug>` commands
- Whether a reference solution was stashed

## Rules

- **Never** require the user to paste testcases or expected values when they gave a description.
- **Never** hand-author `expected` when the oracle can compute it.
- Prefer `python3 -m prep ...` so PATH setup is unnecessary.
- Keep one folder per problem under `problems/`.
- If the problem is not solvable in pure Python (needs unavailable APIs), say so and stop before scaffolding.

## Quick reference

| Step | Command |
| --- | --- |
| Scaffold | `python3 -m prep scaffold --title ... --entry ... --description-file ...` |
| Fill expecteds | `python3 -m prep materialize <slug> --cases-file ... --run` |
| Practice stub | `python3 -m prep practice <slug>` |
| Re-check | `python3 -m prep run <slug>` |

See `references/edge-cases.md` for the edge-case checklist.
