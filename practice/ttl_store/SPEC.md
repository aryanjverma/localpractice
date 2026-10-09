# TTL store

Implement a key-value store with per-entry time-to-live.

## API

```python
set(key, value, ttl)
get(key)
delete(key)
```

## Requirements

- `set(key, value, ttl)` — store `value` under `key` with a TTL in seconds (relative to the injected clock).
- `get(key)` — return the value if present and not expired; otherwise return `None`.
- `delete(key)` — remove a key; deleting a missing key is a no-op (or raise — pick one and document it).
- Expired keys must behave as missing (`get` returns `None`).
- The clock is an **injected `now()` function** (do not call wall-clock time or `sleep` inside the store).
- Include **cleanup of expired entries** (lazy on access, periodic/active sweep, or both — document your choice).

## Suggested shape

```python
class TtlStore:
    def __init__(self, now: Callable[[], float]): ...
    def set(self, key: str, value: Any, ttl: float) -> None: ...
    def get(self, key: str) -> Any | None: ...
    def delete(self, key: str) -> None: ...
    def cleanup(self) -> int: ...  # optional but useful: remove expired, return count
```

You may adjust names and types as long as the behaviors above hold.

## Design follow-up questions

Read these **after** you finish implementing and testing.

1. Lazy vs. active expiry — when is each preferable, and can you combine them?
2. How do you bound memory if keys are written faster than they expire?
3. What eviction policy would you add on top of TTL (LRU, LFU, size-based)?
4. Is your store safe under concurrent readers/writers? What would you change?
5. How would you persist TTLs correctly across restarts (absolute deadlines vs. remaining TTL)?
