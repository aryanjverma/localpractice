# Rate limiter

Implement a per-key rate limiter.

## API

```python
allow(key) -> bool
```

## Requirements

- `allow(key) -> bool` — return `True` if the request is allowed under the limit, else `False`.
- Per-key limit of **N requests per window** (N and window length are constructor / config parameters).
- The clock is an **injected `now()` function** (do not call wall-clock time or `sleep` inside the limiter).
- **Pick one algorithm** and implement it:
  - fixed window
  - sliding window
  - token bucket
- Be ready to explain the tradeoffs of your choice (boundary bursts, fairness, memory, complexity).

## Suggested shape

```python
class RateLimiter:
    def __init__(
        self,
        now: Callable[[], float],
        limit: int,
        window_seconds: float,
    ): ...
    def allow(self, key: str) -> bool: ...
```

You may adjust names and types as long as the behaviors above hold.

## Design follow-up questions

Read these **after** you finish implementing and testing.

1. How would you implement distributed limiting with Redis (or similar)?
2. How does your algorithm handle bursts at window boundaries?
3. What happens to memory as the number of distinct keys grows without bound?
4. How would you support per-tier limits (e.g. free vs. paid) or per-route limits?
5. When would you choose token bucket vs. sliding window in production?
