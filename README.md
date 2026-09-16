# Local LeetCode / FastPrep practice

Store problem descriptions locally, solve them, and run tests — **without hand-entering expected outputs**.

## Agent skill (recommended)

This repo includes a Cursor skill: **`prep-problem`**.

Paste a problem description (or say “prep this question”) and the agent will:

1. Scaffold `problems/<slug>/`
2. Write a correct `solution.py`
3. Invent edge-case **inputs**
4. Fill **expected** values deterministically via `prep materialize` (solution = oracle)
5. Verify with `prep run`

Invoke with `/prep-problem` or just paste a prompt — the skill description matches that intent.

## Quick start (CLI)

```bash
pip install -e .
python3 -m prep list
python3 -m prep show two-sum
python3 -m prep run two-sum
```

## Description → tests (oracle flow)

```bash
# 1. Scaffold from the prompt
python3 -m prep scaffold \
  --title "Valid Anagram" \
  --entry "Solution.isAnagram" \
  --description-file /tmp/desc.md

# 2. Write problems/valid-anagram/solution.py

# 3. Write input-only cases (no expected)
# /tmp/cases.json → { "cases": [ { "name": "...", "args": ["ab", "ba"] }, ... ] }

# 4. Materialize expecteds from the solution, then run
python3 -m prep materialize valid-anagram --cases-file /tmp/cases.json --run

# Optional: hide the solution so you can re-solve it
python3 -m prep practice valid-anagram
```

Same solution + same cases file ⇒ same tests every time.

## Problem layout

```
problems/<slug>/
  problem.md      # description
  solution.py     # your code / oracle
  tests.json      # entry + cases
  reference.py    # optional stashed solution (after prep practice)
```

## Test format

```json
{
  "title": "Two Sum",
  "entry": "Solution.twoSum",
  "tests": [
    {
      "name": "example 1",
      "args": [[2, 7, 11, 15], 9],
      "expected": [0, 1],
      "unordered": true
    }
  ]
}
```

- **entry** — `Solution.method` or a bare function name
- **args** / **kwargs** — call arguments
- **expected** — usually produced by `prep materialize`, not by hand
- **unordered** — compare lists ignoring order

## Commands

| Command | What it does |
|---|---|
| `prep scaffold` | Create problem files from title/entry/description |
| `prep materialize <slug>` | Fill expected outputs using `solution.py` as oracle |
| `prep practice <slug>` | Move solution → `reference.py`, leave a stub |
| `prep new` | Interactive create (optional manual tests) |
| `prep list` / `show` / `run` | Browse and execute |
| `prep add-test <slug>` | Append a case (`--oracle` fills expected) |

## Samples

- `two-sum` — 3 tests
- `plus-one` — 2 tests
