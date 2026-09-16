from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .core import (
    PROBLEMS_DIR,
    create_problem,
    list_problems,
    load_problem,
    materialize_tests,
    parse_cases_payload,
    run_tests,
    save_tests,
    stash_reference_solution,
    TestCase,
)


def _print_results(slug: str, results: list) -> int:
    if not results:
        print(f"No tests defined for '{slug}'. Add some in tests.json or via `prep add-test`.")
        return 1

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"\nRunning {slug} — {passed}/{total} passed\n")

    failed = 0
    for result in results:
        if result.passed:
            print(f"  PASS  {result.name}")
            continue
        failed += 1
        print(f"  FAIL  {result.name}")
        if result.args is not None:
            print(f"        args:     {result.args!r}")
        if result.kwargs:
            print(f"        kwargs:   {result.kwargs!r}")
        if result.error:
            print("        error:")
            for line in result.error.strip().splitlines():
                print(f"          {line}")
        else:
            print(f"        expected: {result.expected!r}")
            print(f"        actual:   {result.actual!r}")
        print()

    if failed:
        print(f"{failed} test(s) failed.")
        return 1
    print("All tests passed.")
    return 0


def _read_multiline(prompt: str) -> str:
    print(prompt)
    print("(Finish with a blank line, or Ctrl-D / Ctrl-Z)")
    lines: list[str] = []
    try:
        while True:
            line = input()
            if line == "" and lines:
                break
            lines.append(line)
    except EOFError:
        pass
    return "\n".join(lines).strip()


def _parse_json_value(raw: str, label: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON for {label}: {exc}") from exc


def cmd_new(args: argparse.Namespace) -> int:
    title = args.title or input("Problem title: ").strip()
    if not title:
        print("Title is required.")
        return 1

    entry = args.entry or input("Entry point [Solution.solve]: ").strip() or "Solution.solve"
    description = args.description
    if not description:
        if args.description_file:
            description = Path(args.description_file).read_text(encoding="utf-8")
        else:
            description = _read_multiline("Paste the problem description:")

    tests: list[dict[str, Any]] = []
    if args.tests_file:
        tests = json.loads(Path(args.tests_file).read_text(encoding="utf-8"))
        if isinstance(tests, dict) and "tests" in tests:
            tests = tests["tests"]
    elif not args.no_tests and sys.stdin.isatty():
        print("\nAdd test cases (blank name to stop).")
        while True:
            name = input("  Test name (optional): ").strip()
            if name == "" and not tests:
                # allow skipping entirely on first blank if they also skip args
                raw_args = input("  args JSON (blank to finish): ").strip()
                if not raw_args:
                    break
            elif name == "" and tests:
                raw_args = input("  args JSON (blank to finish): ").strip()
                if not raw_args:
                    break
            else:
                raw_args = input('  args JSON e.g. [[2,7,11,15], 9]: ').strip()
                if not raw_args:
                    print("  Skipping empty test.")
                    continue

            raw_expected = input("  expected JSON: ").strip()
            case: dict[str, Any] = {
                "args": _parse_json_value(raw_args, "args"),
                "expected": _parse_json_value(raw_expected, "expected"),
            }
            if name:
                case["name"] = name
            unordered = input("  unordered list compare? [y/N]: ").strip().lower()
            if unordered in {"y", "yes"}:
                case["unordered"] = True
            tests.append(case)

    try:
        meta = create_problem(
            title=title,
            entry=entry,
            description=description or "No description yet.",
            tests=tests,
            slug=args.slug,
        )
    except FileExistsError as exc:
        print(exc)
        return 1

    print(f"\nCreated problem: {meta.slug}")
    print(f"  Description: {meta.problem_md}")
    print(f"  Solution:    {meta.solution_py}")
    print(f"  Tests:       {meta.tests_json}")
    print(f"\nEdit the solution, then run:\n  prep run {meta.slug}")
    return 0


def cmd_list(_: argparse.Namespace) -> int:
    problems = list_problems()
    if not problems:
        print(f"No problems yet. Create one with `prep new`.\n(Problems live in {PROBLEMS_DIR})")
        return 0
    print(f"Problems in {PROBLEMS_DIR}:\n")
    for path in problems:
        try:
            meta = load_problem(path.name)
            n = len(meta.tests)
            print(f"  {meta.slug:30}  {meta.title}  ({n} test{'s' if n != 1 else ''})")
        except Exception as exc:  # noqa: BLE001
            print(f"  {path.name:30}  (invalid: {exc})")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    try:
        meta = load_problem(args.slug)
    except FileNotFoundError as exc:
        print(exc)
        return 1

    print(f"{meta.title} ({meta.slug})")
    print(f"Entry: {meta.entry}")
    print(f"Tests: {len(meta.tests)}")
    print("-" * 60)
    if meta.problem_md.exists():
        print(meta.problem_md.read_text(encoding="utf-8"))
    else:
        print("(no problem.md)")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    try:
        meta = load_problem(args.slug)
    except FileNotFoundError as exc:
        print(exc)
        return 1
    results = run_tests(meta)
    return _print_results(meta.slug, results)


def cmd_add_test(args: argparse.Namespace) -> int:
    try:
        meta = load_problem(args.slug)
    except FileNotFoundError as exc:
        print(exc)
        return 1

    raw_args = args.args_json or input('args JSON e.g. [[2,7,11,15], 9]: ').strip()
    if not raw_args:
        print("args are required.")
        return 1

    case_data: dict[str, Any] = {
        "args": _parse_json_value(raw_args, "args"),
    }
    if args.expected_json is not None:
        case_data["expected"] = _parse_json_value(args.expected_json, "expected")
    elif not args.oracle and sys.stdin.isatty() and args.args_json is None:
        raw_expected = input("expected JSON (blank = fill via oracle/materialize): ").strip()
        if raw_expected:
            case_data["expected"] = _parse_json_value(raw_expected, "expected")
    if args.name:
        case_data["name"] = args.name
    if args.unordered:
        case_data["unordered"] = True

    meta.tests.append(TestCase.from_dict(case_data, len(meta.tests)))
    save_tests(meta)

    if args.oracle or "expected" not in case_data:
        try:
            materialize_tests(meta)
        except Exception as exc:  # noqa: BLE001
            print(f"Saved input case, but oracle failed: {exc}")
            return 1
        print(f"Added oracle-filled test to {meta.slug}. Total tests: {len(meta.tests)}")
        return 0

    print(f"Added test to {meta.slug}. Total tests: {len(meta.tests)}")
    return 0


def cmd_scaffold(args: argparse.Namespace) -> int:
    title = args.title
    if not title:
        print("--title is required")
        return 1
    entry = args.entry or "Solution.solve"
    if args.description_file:
        description = Path(args.description_file).read_text(encoding="utf-8")
    else:
        description = args.description or ""
    solution = None
    if args.solution_file:
        solution = Path(args.solution_file).read_text(encoding="utf-8")

    try:
        meta = create_problem(
            title=title,
            entry=entry,
            description=description or "No description yet.",
            tests=[],
            slug=args.slug,
            solution=solution,
            overwrite=args.overwrite,
        )
    except FileExistsError as exc:
        print(exc)
        return 1

    print(f"Scaffolded: {meta.slug}")
    print(f"  {meta.problem_md}")
    print(f"  {meta.solution_py}")
    print(f"  {meta.tests_json}")
    return 0


def cmd_materialize(args: argparse.Namespace) -> int:
    try:
        meta = load_problem(args.slug)
    except FileNotFoundError as exc:
        print(exc)
        return 1

    cases = None
    if args.cases_file:
        raw = json.loads(Path(args.cases_file).read_text(encoding="utf-8"))
        try:
            cases = parse_cases_payload(raw)
        except ValueError as exc:
            print(exc)
            return 1

    try:
        meta = materialize_tests(meta, cases=cases)
    except Exception as exc:  # noqa: BLE001
        print(f"Materialize failed: {exc}")
        return 1

    print(f"Materialized {len(meta.tests)} test(s) for {meta.slug} using solution.py as oracle.")
    if args.practice:
        ref = stash_reference_solution(meta)
        print(f"Practice mode: solution stubbed; reference saved at {ref}")
    if args.run:
        return _print_results(meta.slug, run_tests(meta))
    return 0


def cmd_practice(args: argparse.Namespace) -> int:
    try:
        meta = load_problem(args.slug)
    except FileNotFoundError as exc:
        print(exc)
        return 1
    ref = stash_reference_solution(meta)
    print(f"Stashed solution at {ref} and left a stub in solution.py")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prep",
        description="Local LeetCode / FastPrep practice — store problems and run your tests.",
    )
    parser.add_argument("--version", action="version", version=f"prep {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    new_p = sub.add_parser("new", help="Create a new problem")
    new_p.add_argument("--title", help="Problem title")
    new_p.add_argument("--slug", help="Folder name (default: slugified title)")
    new_p.add_argument("--entry", help="Function entry, e.g. Solution.twoSum")
    new_p.add_argument("--description", help="Problem description text")
    new_p.add_argument("--description-file", help="Read description from a file")
    new_p.add_argument("--tests-file", help="JSON file with a list of tests (or {tests: [...]})")
    new_p.add_argument("--no-tests", action="store_true", help="Skip interactive test entry")
    new_p.set_defaults(func=cmd_new)

    scaffold_p = sub.add_parser(
        "scaffold",
        help="Create problem files from title/entry/description (no interactive prompts)",
    )
    scaffold_p.add_argument("--title", required=True)
    scaffold_p.add_argument("--entry", default="Solution.solve")
    scaffold_p.add_argument("--slug")
    scaffold_p.add_argument("--description")
    scaffold_p.add_argument("--description-file")
    scaffold_p.add_argument("--solution-file", help="Optional initial solution.py contents")
    scaffold_p.add_argument("--overwrite", action="store_true")
    scaffold_p.set_defaults(func=cmd_scaffold)

    mat_p = sub.add_parser(
        "materialize",
        help="Fill expected outputs by running solution.py as a deterministic oracle",
    )
    mat_p.add_argument("slug")
    mat_p.add_argument(
        "--cases-file",
        help="JSON list of input-only cases ({name,args,...}); replaces existing tests",
    )
    mat_p.add_argument("--run", action="store_true", help="Run tests after materializing")
    mat_p.add_argument(
        "--practice",
        action="store_true",
        help="After materializing, move solution to reference.py and leave a stub",
    )
    mat_p.set_defaults(func=cmd_materialize)

    practice_p = sub.add_parser(
        "practice",
        help="Move solution.py to reference.py and leave a stub to re-solve",
    )
    practice_p.add_argument("slug")
    practice_p.set_defaults(func=cmd_practice)

    list_p = sub.add_parser("list", help="List local problems")
    list_p.set_defaults(func=cmd_list)

    show_p = sub.add_parser("show", help="Show a problem description")
    show_p.add_argument("slug")
    show_p.set_defaults(func=cmd_show)

    run_p = sub.add_parser("run", help="Run tests for a problem")
    run_p.add_argument("slug")
    run_p.set_defaults(func=cmd_run)

    add_p = sub.add_parser("add-test", help="Append a test case to a problem")
    add_p.add_argument("slug")
    add_p.add_argument("--name")
    add_p.add_argument("--args-json")
    add_p.add_argument("--expected-json")
    add_p.add_argument(
        "--oracle",
        action="store_true",
        help="Compute expected by running the current solution",
    )
    add_p.add_argument("--unordered", action="store_true")
    add_p.set_defaults(func=cmd_add_test)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
