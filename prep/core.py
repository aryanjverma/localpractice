from __future__ import annotations

import importlib.util
import json
import re
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROBLEMS_DIR = Path(__file__).resolve().parent.parent / "problems"
LOCAL_PROBLEMS_DIR = PROBLEMS_DIR / "local"


@dataclass
class TestCase:
    args: list[Any]
    expected: Any
    kwargs: dict[str, Any]
    unordered: bool
    name: str | None
    has_expected: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any], index: int) -> TestCase:
        if "args" not in data and "input" in data:
            args = data["input"]
            if not isinstance(args, list):
                args = [args]
        else:
            args = data.get("args", [])
        has_expected = "expected" in data
        return cls(
            args=list(args),
            expected=data.get("expected"),
            kwargs=dict(data.get("kwargs", {})),
            unordered=bool(data.get("unordered", False)),
            name=data.get("name") or f"case {index + 1}",
            has_expected=has_expected,
        )


@dataclass
class ProblemMeta:
    slug: str
    title: str
    entry: str
    tests: list[TestCase]
    root: Path

    @property
    def problem_md(self) -> Path:
        return self.root / "problem.md"

    @property
    def solution_py(self) -> Path:
        return self.root / "solution.py"

    @property
    def tests_json(self) -> Path:
        return self.root / "tests.json"


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "problem"


def ensure_problems_dir() -> Path:
    PROBLEMS_DIR.mkdir(parents=True, exist_ok=True)
    return PROBLEMS_DIR


def ensure_local_problems_dir() -> Path:
    LOCAL_PROBLEMS_DIR.mkdir(parents=True, exist_ok=True)
    return LOCAL_PROBLEMS_DIR


def problem_roots() -> list[Path]:
    """Sample problems live in problems/; personal ones in problems/local/."""
    ensure_problems_dir()
    roots = [PROBLEMS_DIR]
    if LOCAL_PROBLEMS_DIR.is_dir():
        roots.append(LOCAL_PROBLEMS_DIR)
    return roots


def list_problems() -> list[Path]:
    found: list[Path] = []
    for root in problem_roots():
        for p in root.iterdir():
            if p.name == "local":
                continue
            if p.is_dir() and (p / "tests.json").exists():
                found.append(p)
    return sorted(found, key=lambda p: p.name)


def resolve_problem_root(slug: str) -> Path:
    """Prefer problems/local/<slug> when both exist."""
    local = LOCAL_PROBLEMS_DIR / slug
    shared = PROBLEMS_DIR / slug
    if (local / "tests.json").exists():
        return local
    if (shared / "tests.json").exists():
        return shared
    raise FileNotFoundError(
        f"No problem found for '{slug}' under {LOCAL_PROBLEMS_DIR} or {PROBLEMS_DIR}"
    )


def load_problem(slug: str) -> ProblemMeta:
    root = resolve_problem_root(slug)
    tests_path = root / "tests.json"
    data = json.loads(tests_path.read_text(encoding="utf-8"))
    entry = data.get("entry") or data.get("function")
    if not entry:
        raise ValueError(f"{tests_path} must define 'entry' (e.g. 'Solution.twoSum')")

    title = data.get("title") or slug.replace("-", " ").title()
    tests = [TestCase.from_dict(t, i) for i, t in enumerate(data.get("tests", []))]
    return ProblemMeta(slug=slug, title=title, entry=entry, tests=tests, root=root)


def save_tests(meta: ProblemMeta) -> None:
    payload = {
        "title": meta.title,
        "entry": meta.entry,
        "tests": [
            {
                **({"name": t.name} if t.name and not t.name.startswith("case ") else {}),
                "args": t.args,
                **({"kwargs": t.kwargs} if t.kwargs else {}),
                **({"expected": t.expected} if t.has_expected else {}),
                **({"unordered": True} if t.unordered else {}),
            }
            for t in meta.tests
        ],
    }
    meta.tests_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def solution_stub(title: str, entry: str) -> str:
    method = entry.split(".")[-1]
    if "." in entry:
        class_name, method_name = entry.split(".", 1)
        return f'''"""Solution for: {title}"""


class {class_name}:
    def {method_name}(self, *args, **kwargs):
        # TODO: implement
        raise NotImplementedError
'''
    return f'''"""Solution for: {title}"""


def {method}(*args, **kwargs):
    # TODO: implement
    raise NotImplementedError
'''


def create_problem(
    title: str,
    entry: str,
    description: str,
    tests: list[dict[str, Any]] | None = None,
    slug: str | None = None,
    solution: str | None = None,
    overwrite: bool = False,
    local: bool = False,
) -> ProblemMeta:
    ensure_problems_dir()
    slug = slugify(slug or title)
    parent = ensure_local_problems_dir() if local else PROBLEMS_DIR
    root = parent / slug
    if root.exists():
        if not overwrite:
            raise FileExistsError(f"Problem already exists: {slug} ({root})")
        # Keep directory; overwrite files below.
    else:
        root.mkdir(parents=True)

    (root / "problem.md").write_text(
        f"# {title}\n\n{description.strip()}\n", encoding="utf-8"
    )
    (root / "solution.py").write_text(
        solution if solution is not None else solution_stub(title, entry),
        encoding="utf-8",
    )

    meta = ProblemMeta(
        slug=slug,
        title=title,
        entry=entry,
        tests=[TestCase.from_dict(t, i) for i, t in enumerate(tests or [])],
        root=root,
    )
    save_tests(meta)
    return meta


def parse_cases_payload(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict):
        if "tests" in data:
            data = data["tests"]
        elif "cases" in data:
            data = data["cases"]
        else:
            raise ValueError("JSON object must contain 'tests' or 'cases'")
    if not isinstance(data, list):
        raise ValueError("Cases must be a JSON list")
    return list(data)


def materialize_tests(
    meta: ProblemMeta,
    cases: list[dict[str, Any]] | None = None,
) -> ProblemMeta:
    """Fill missing expected values by running the current solution (oracle).

    Given the same solution and the same input cases, output is deterministic.
    """
    raw_cases = cases
    if raw_cases is None:
        raw_cases = [
            {
                **({"name": t.name} if t.name else {}),
                "args": t.args,
                **({"kwargs": t.kwargs} if t.kwargs else {}),
                **({"expected": t.expected} if t.has_expected else {}),
                **({"unordered": True} if t.unordered else {}),
            }
            for t in meta.tests
        ]

    fn = load_solution(meta)
    materialized: list[TestCase] = []
    for i, raw in enumerate(raw_cases):
        case = TestCase.from_dict(raw, i)
        if not case.has_expected:
            try:
                actual = fn(*case.args, **case.kwargs)
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError(
                    f"Oracle failed on {case.name}: {type(exc).__name__}: {exc}"
                ) from exc
            case.expected = actual
            case.has_expected = True
        materialized.append(case)

    meta.tests = materialized
    save_tests(meta)
    return meta


def stash_reference_solution(meta: ProblemMeta) -> Path:
    """Copy solution.py to reference.py and replace solution with a stub."""
    ref = meta.root / "reference.py"
    ref.write_text(meta.solution_py.read_text(encoding="utf-8"), encoding="utf-8")
    meta.solution_py.write_text(solution_stub(meta.title, meta.entry), encoding="utf-8")
    return ref


def _values_equal(actual: Any, expected: Any, unordered: bool) -> bool:
    if unordered and isinstance(actual, list) and isinstance(expected, list):
        try:
            return sorted(actual) == sorted(expected)
        except TypeError:
            # Fall back when items are unorderable (e.g. nested lists)
            remaining = list(expected)
            for item in actual:
                if item not in remaining:
                    return False
                remaining.remove(item)
            return not remaining
    return actual == expected


def _resolve_entry(module: Any, entry: str):
    parts = entry.split(".")
    obj = module
    for part in parts:
        if not hasattr(obj, part):
            raise AttributeError(f"Could not find '{entry}' in solution.py")
        obj = getattr(obj, part)

    # LeetCode style: Solution.method -> instantiate Solution, bind method
    if len(parts) == 2:
        class_name, method_name = parts
        cls = getattr(module, class_name)
        if isinstance(cls, type):
            instance = cls()
            return getattr(instance, method_name)
    return obj


def load_solution(meta: ProblemMeta):
    path = meta.solution_py
    if not path.exists():
        raise FileNotFoundError(f"Missing solution file: {path}")

    # Unique module name avoids stale imports across runs
    mod_name = f"prep_solution_{meta.slug.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return _resolve_entry(module, meta.entry)


@dataclass
class TestResult:
    name: str
    passed: bool
    actual: Any = None
    expected: Any = None
    error: str | None = None
    args: list[Any] | None = None
    kwargs: dict[str, Any] | None = None


def run_tests(meta: ProblemMeta) -> list[TestResult]:
    if not meta.tests:
        return []

    missing = [t.name for t in meta.tests if not t.has_expected]
    if missing:
        return [
            TestResult(
                name="missing expected",
                passed=False,
                error=(
                    "Some tests have no expected value. "
                    f"Run `prep materialize {meta.slug}` first. Missing: {missing}"
                ),
            )
        ]

    try:
        fn = load_solution(meta)
    except Exception as exc:  # noqa: BLE001 - surface any load failure as test failure
        return [
            TestResult(
                name="load solution",
                passed=False,
                error=f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}",
            )
        ]

    results: list[TestResult] = []
    for case in meta.tests:
        try:
            actual = fn(*case.args, **case.kwargs)
            passed = _values_equal(actual, case.expected, case.unordered)
            results.append(
                TestResult(
                    name=case.name or "case",
                    passed=passed,
                    actual=actual,
                    expected=case.expected,
                    args=case.args,
                    kwargs=case.kwargs,
                )
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                TestResult(
                    name=case.name or "case",
                    passed=False,
                    expected=case.expected,
                    args=case.args,
                    kwargs=case.kwargs,
                    error=f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}",
                )
            )
    return results
