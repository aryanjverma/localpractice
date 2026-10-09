# Backend interview drills

Timed practice for common backend design problems. **Write the implementations yourself** — stubs are intentionally empty.

## Rules

1. **Timed.** Start with `make timer MIN=45` (or your preferred length) before you open the stub.
2. **No lookups mid-build.** Spec only. Docs, Stack Overflow, and AI stay closed until the timer ends.
3. **Injected clock.** Never call `time.sleep` or wall-clock `time.time` inside the drill. Accept a `now()` (or equivalent) callable so tests can advance time deterministically.
4. **Write 5–8 tests.** Cover happy path, edges, and at least one failure / expiry / ordering case. Prefer small, focused tests.
5. **Self-review.** When the timer rings (or you finish), re-read your code and the SPEC follow-up questions before looking anything up.

## Setup

```bash
cd practice
python3.11 -m venv .venv   # or python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Drills

| Drill | Spec | Stub |
|---|---|---|
| Scheduler | `scheduler/SPEC.md` | `scheduler/scheduler.py` |
| Rate limiter | `rate_limiter/SPEC.md` | `rate_limiter/rate_limiter.py` |
| TTL store | `ttl_store/SPEC.md` | `ttl_store/ttl_store.py` |

## Commands

```bash
make test DRILL=scheduler      # pytest for one drill
make test DRILL=rate_limiter
make test DRILL=ttl_store
make lint                      # ruff check .
make timer MIN=45              # countdown (minutes)
```

Or directly:

```bash
pytest scheduler/test_scheduler.py -v
python timer.py 45
```

## Suggested session

1. Pick a drill and skim its `SPEC.md` (skip the follow-up section until later).
2. Start the timer.
3. Implement the stub and write 5–8 tests against an injected clock.
4. Run `make test DRILL=<name>` until green (or until time is up).
5. Read the design follow-up questions and self-review.
