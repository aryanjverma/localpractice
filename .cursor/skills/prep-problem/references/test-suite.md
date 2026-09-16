# Test suite checklist for input generation

Use this when designing the **input-only** cases file before `prep materialize`.

The suite is a **mix of typical cases and edge cases**. Edge cases are **required**, but they are not the whole suite.

## Required coverage

Every generated suite must include:

1. **Prompt examples** — every concrete example from the description, adapted to `args`.
2. **Typical / happy-path** — ordinary mid-size inputs that exercise the main logic (not boundary-only). Include at least **2** when the prompt is non-trivial.
3. **Edge cases** — at least **2–3** (more if constraints invite them). Name them with an `edge-` prefix.
4. **One harder / denser case** — slightly larger or structurally interesting, still cheap to run.

Aim for **8–15** cases unless the prompt is tiny. Prefer diversity over near-duplicates.

## Typical / happy-path ideas

- Representative inputs similar to interview “example 1” but not copied from the prompt
- Mixed values in the middle of the allowed range
- Multiple valid “normal” shapes (e.g. unsorted array, average-length string)
- Both a true/success path and a false/no-match path when the API returns a boolean or optional result

## Edge cases (required; when constraints allow)

1. **Minimum size** — empty structure, length 0/1, or smallest valid input
2. **Maximum-ish** — larger but still cheap (not full constraint max unless tiny)
3. **Duplicates** — repeated values when the domain allows them
4. **Negatives / zero** — if numeric inputs can be ≤ 0
5. **Boundaries** — values at stated min/max (e.g. `target` equal to sum of extremes)
6. **Order sensitivity** — already sorted, reverse sorted, arbitrary order
7. **Ambiguous outputs** — if multiple answers are valid, set `"unordered": true` (or encode the problem’s tie-break in the solution and keep outputs ordered)

## By input shape (extra edges)

| Shape | Extra edge cases |
| --- | --- |
| Array / list | single element; all equal; two elements that form the answer; no-op / identity |
| Two arrays / strings | one empty; different lengths; identical inputs |
| String | empty; single char; palindrome; all same char; unicode only if relevant |
| Matrix / grid | 1×1; 1×n; n×1; all zeros / all ones |
| Tree / linked list (as nested arrays) | single node; skewed; balanced small tree |
| Graph | single node; disconnected; cycle if allowed |
| Intervals | touching; nested; disjoint; unsorted input |

## Determinism rules

- Cases files must be **pure data** (no randomness at materialize time).
- If you need “random-looking” data, hard-code a fixed list — do not call `random` without a fixed seed baked into the written JSON.
- Expected values come only from running `solution.py` via `prep materialize`.

## Anti-patterns

- Suite that is **only** edge cases (missing ordinary coverage)
- Suite with **no** edge cases
- Dozens of near-identical mid cases
- Hand-written `expected` values instead of oracle materialization
