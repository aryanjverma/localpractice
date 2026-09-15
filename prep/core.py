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


@dataclass
class TestCase:
    args: list[Any]
    expected: Any
    kwargs: dict[str, Any]
    unordered: bool
    name: str | None

    @classmethod
    def from_dict(cls, data: dict[str, Any], index: int) -> TestCase:
        if "args" not in data and "input" in data:
            args = data["input"]
            if not isinstance(args, list):
                args = [args]
        else:
            args = data.get("args", [])
        return cls(
            args=list(args),
            expected=data["expected"],
            kwargs=dict(data.get("kwargs", {})),
            unordered=bool(data.get("unordered", False)),
            name=data.get("name") or f"case {index + 1}",
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


def list_problems() -> list[Path]:
    ensure_problems_dir()
    return sorted(
        p for p in PROBLEMS_DIR.iterdir() if p.is_dir() and (p / "tests.json").exists()
    )


def load_problem(slug: str) -> ProblemMeta:
    root = PROBLEMS_DIR / slug
    tests_path = root / "tests.json"
    if not tests_path.exists():
        raise FileNotFoundError(f"No problem found at {root}")

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
                "expected": t.expected,
                **({"unordered": True} if t.unordered else {}),
            }
            for t in meta.tests
        ],
    }
    meta.tests_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def create_problem(
    title: str,
    entry: str,
    description: str,
    tests: list[dict[str, Any]] | None = None,
    slug: str | None = None,
) -> ProblemMeta:
    ensure_problems_dir()
    slug = slugify(slug or title)
    root = PROBLEMS_DIR / slug
    if root.exists():
        raise FileExistsError(f"Problem already exists: {slug}")

    root.mkdir(parents=True)
    method = entry.split(".")[-1]
    class_based = "." in entry

    if class_based:
        class_name, method_name = entry.split(".", 1)
        stub = f'''"""Solution for: {title}"""


class {class_name}:
    def {method_name}(self, *args, **kwargs):
        # TODO: implement
        raise NotImplementedError
'''
    else:
        stub = f'''"""Solution for: {title}"""


def {method}(*args, **kwargs):
    # TODO: implement
    raise NotImplementedError
'''

    (root / "problem.md").write_text(
        f"# {title}\n\n{description.strip()}\n", encoding="utf-8"
    )
    (root / "solution.py").write_text(stub, encoding="utf-8")

    meta = ProblemMeta(
        slug=slug,
        title=title,
        entry=entry,
        tests=[TestCase.from_dict(t, i) for i, t in enumerate(tests or [])],
        root=root,
    )
    save_tests(meta)
    return meta


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
