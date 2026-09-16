# Local LeetCode / FastPrep practice

Store problem descriptions and test cases locally, write a solution, and run your tests — no account required.

## Quick start

```bash
pip install -e .
prep list
prep show two-sum
prep run two-sum
```

If `prep` is not on your PATH after install, use:

```bash
python3 -m prep list
python3 -m prep run two-sum
```

## Create a problem

Interactive:

```bash
prep new
```

Or non-interactive:

```bash
prep new \
  --title "Valid Anagram" \
  --entry "Solution.isAnagram" \
  --description "Given two strings s and t, return true if t is an anagram of s." \
  --tests-file /tmp/anagram-tests.json \
  --no-tests
```

That creates:

```
problems/<slug>/
  problem.md     # description
  solution.py    # your code (edit this)
  tests.json     # test cases
```

Then implement `solution.py` and run:

```bash
prep run valid-anagram
```

## Test format

`tests.json` looks like:

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

- **entry** — function to call. Use `Solution.method` for LeetCode-style classes, or a bare function name like `two_sum`.
- **args** — positional arguments (JSON).
- **kwargs** — optional keyword arguments.
- **expected** — expected return value.
- **unordered** — if true, compare lists as sets of items (order ignored).

Add more cases later:

```bash
prep add-test two-sum \
  --name "extra" \
  --args-json "[[1,2,3], 5]" \
  --expected-json "[1, 2]" \
  --unordered
```

## Commands

| Command | What it does |
|---|---|
| `prep new` | Create a problem (description + tests + solution stub) |
| `prep list` | List local problems |
| `prep show <slug>` | Print the problem description |
| `prep run <slug>` | Run your solution against the tests |
| `prep add-test <slug>` | Append a test case |

## Tips

- Keep one folder per problem under `problems/`.
- Edit `solution.py` freely; tests reload it on every `prep run`.
- Failures print args, expected vs actual, and tracebacks for exceptions.
