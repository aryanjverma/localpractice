---
name: prep-problem
description: >-
  Turn a coding-interview / LeetCode / FastPrep problem description into a local
  practice problem: solve it, generate a full input suite (typical cases plus
  required edge cases), and deterministically fill expected outputs from the
  solution oracle. Use when the user pastes a problem statement, asks to prep a
  question, generate tests, or set up local practice without manually entering
  testcases.
---

# Prep Problem (description → solved + tests)

Build a local practice problem from **only a question description**. Do **not** ask the user to supply test cases or expected outputs.

## Goal

1. Solve the problem correctly in Python.
2. Design a **full input suite**: typical / happy-path cases **and** edge cases (edge cases are required, but not the only cases).
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
    { "name": "typical-mid", "args": [[1, 5, 3, 7, 2], 9], "unordered": true },
    { "name": "edge-min-pair", "args": [[1, 2], 3], "unordered": true },
    { "name": "edge-duplicates", "args": [[3, 3], 6], "unordered": true }
  ]
}
```

Follow `references/test-suite.md`. The suite **must** include all of:

| Category | What to include |
| --- | --- |
| **Prompt examples** | Every runnable example from the description |
| **Typical / happy-path** | Ordinary mid-size inputs that reflect common use (not only edges) |
| **Edge cases** | Required — boundaries, empties/min size, duplicates, negatives/zeros, order extremes, etc. as constraints allow |
| **At least one harder case** | Slightly larger or structurally interesting input |

Name edge cases with an `edge-` prefix (e.g. `edge-empty`, `edge-duplicates`) so coverage is obvious.

Set `"unordered": true` only when the problem allows any order.

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
- How many tests were generated (mention that the suite includes typical + edge cases)
- `prep run <slug>` / `prep show <slug>` commands
- Whether a reference solution was stashed

## Rules

- **Never** require the user to paste testcases or expected values when they gave a description.
- **Never** hand-author `expected` when the oracle can compute it.
- **Never** ship a suite that is only edge cases or only happy-path — include both; edge cases are mandatory.
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

See `references/test-suite.md` for the full coverage checklist.
