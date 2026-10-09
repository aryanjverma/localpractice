# Scheduler

Implement a small in-process task scheduler.

## API

```python
schedule(task_id, run_at, fn)
cancel(task_id)
run_due()
```

## Requirements

- `schedule(task_id, run_at, fn)` — register a callable to run at `run_at` (a timestamp comparable to the injected clock).
- `cancel(task_id)` — remove a pending task; cancelling an unknown id is a no-op (or raise — pick one and document it).
- `run_due()` — execute every task whose `run_at` is `<= now()`, then remove those that completed successfully.
- Tasks run in **time order**. Ties at the same `run_at` are broken by **insertion order**.
- A failing task must **not** crash the scheduler. Retry a failed task up to **N** times (N is a constructor / config parameter). Decide whether failed attempts still count toward “due” ordering and document it.
- The clock is an **injected `now()` function** (do not call wall-clock time or `sleep` inside the scheduler).

## Suggested shape

```python
class Scheduler:
    def __init__(self, now: Callable[[], float], max_retries: int = 3): ...
    def schedule(self, task_id: str, run_at: float, fn: Callable[[], None]) -> None: ...
    def cancel(self, task_id: str) -> None: ...
    def run_due(self) -> None: ...
```

You may adjust names and types as long as the behaviors above hold.

## Design follow-up questions

Read these **after** you finish implementing and testing.

1. How would you persist pending tasks across process restarts?
2. What breaks if `schedule` / `cancel` / `run_due` are called concurrently from multiple threads?
3. How would you scale this to multiple workers without double-running a task?
4. Where does this design stop scaling (heap size, lock contention, clock skew)?
5. How should poison / permanently failing tasks be handled (dead-letter, backoff, alerting)?
