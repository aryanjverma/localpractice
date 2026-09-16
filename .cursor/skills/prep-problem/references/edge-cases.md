# Edge-case checklist for input generation

Use this when designing the **input-only** cases file before `prep materialize`.

## Always try (when constraints allow)

1. **Prompt examples** — every concrete example, adapted to `args`.
2. **Minimum size** — empty structure, length 0/1, or smallest valid input.
3. **Maximum-ish** — a larger but still cheap case (not full constraint max unless tiny).
4. **Duplicates** — repeated values when the domain allows them.
5. **Negatives / zero** — if numeric inputs can be ≤ 0.
6. **Boundaries** — values at stated min/max (e.g. `target` equal to sum of extremes).
7. **Order sensitivity** — already sorted, reverse sorted, arbitrary order.
8. **Ambiguous outputs** — if multiple answers are valid, set `"unordered": true` (or encode the problem’s tie-break in the solution and keep outputs ordered).

## By input shape

| Shape | Extra cases |
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

## Size budget

Aim for **6–12** cases unless the prompt is tiny. Prefer diverse edges over dozens of near-duplicates.
