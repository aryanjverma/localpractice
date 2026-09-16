#!/usr/bin/env python3
"""Optional helper: scaffold + materialize in one shot for agents.

Writes under problems/local/ by default (gitignored). Pass --shared to put
samples under problems/ instead.

Usage:
  python3 build_problem.py \\
    --title "Two Sum" \\
    --entry "Solution.twoSum" \\
    --description-file desc.md \\
    --solution-file sol.py \\
    --cases-file cases.json \\
    [--practice] [--overwrite] [--shared]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running from the skill folder without install quirks.
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from prep.core import (  # noqa: E402
    create_problem,
    materialize_tests,
    parse_cases_payload,
    run_tests,
    stash_reference_solution,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True)
    parser.add_argument("--entry", required=True)
    parser.add_argument("--description-file", required=True)
    parser.add_argument("--solution-file", required=True)
    parser.add_argument("--cases-file", required=True)
    parser.add_argument("--slug")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--practice", action="store_true")
    parser.add_argument(
        "--shared",
        action="store_true",
        help="Write under problems/ (tracked samples) instead of problems/local/",
    )
    args = parser.parse_args()

    description = Path(args.description_file).read_text(encoding="utf-8")
    solution = Path(args.solution_file).read_text(encoding="utf-8")
    cases = parse_cases_payload(json.loads(Path(args.cases_file).read_text(encoding="utf-8")))

    meta = create_problem(
        title=args.title,
        entry=args.entry,
        description=description,
        tests=[],
        slug=args.slug,
        solution=solution,
        overwrite=args.overwrite,
        local=not args.shared,
    )
    meta = materialize_tests(meta, cases=cases)
    results = run_tests(meta)
    passed = sum(1 for r in results if r.passed)
    print(f"Built {meta.slug} at {meta.root}: {passed}/{len(results)} tests passed")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"  {status}  {r.name}")
        if not r.passed and r.error:
            print(f"        {r.error.splitlines()[0]}")
    if args.practice:
        ref = stash_reference_solution(meta)
        print(f"Practice mode: stubbed solution; reference at {ref}")
    return 0 if passed == len(results) and results else 1


if __name__ == "__main__":
    raise SystemExit(main())
