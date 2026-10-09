#!/usr/bin/env python3
"""CLI countdown for timed interview drills.

Usage:
    python timer.py 45          # 45 minutes
    python timer.py --minutes 30
"""

from __future__ import annotations

import argparse
import sys
import time

BELL = "\a"
TICK_SECONDS = 5 * 60
WRAP_UP_SECONDS = 5 * 60


def format_remaining(seconds: int) -> str:
    minutes, secs = divmod(max(0, seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:d}h {minutes:02d}m {secs:02d}s"
    return f"{minutes:d}m {secs:02d}s"


def run_countdown(total_minutes: int) -> None:
    total_seconds = total_minutes * 60
    deadline = time.monotonic() + total_seconds
    next_tick = deadline - total_seconds + TICK_SECONDS
    wrap_up_at = deadline - WRAP_UP_SECONDS
    wrap_up_printed = total_seconds <= WRAP_UP_SECONDS

    print(f"Timer started: {total_minutes} minute(s). Good luck.")
    print(f"Remaining: {format_remaining(total_seconds)}")

    while True:
        remaining = int(round(deadline - time.monotonic()))
        if remaining <= 0:
            break

        now = time.monotonic()

        if not wrap_up_printed and now >= wrap_up_at:
            print(
                f"\nWrap up — {format_remaining(WRAP_UP_SECONDS)} remaining.",
                flush=True,
            )
            wrap_up_printed = True

        if now >= next_tick and remaining > 0:
            print(f"Remaining: {format_remaining(remaining)}", flush=True)
            next_tick += TICK_SECONDS

        time.sleep(min(1.0, max(0.05, deadline - time.monotonic())))

    print(f"\nTime's up!{BELL}", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Timed practice countdown")
    parser.add_argument(
        "minutes",
        nargs="?",
        type=int,
        help="Countdown length in minutes",
    )
    parser.add_argument(
        "--minutes",
        "-m",
        dest="minutes_flag",
        type=int,
        help="Countdown length in minutes (alternative to positional)",
    )
    args = parser.parse_args(argv)

    minutes = args.minutes_flag if args.minutes_flag is not None else args.minutes
    if minutes is None:
        parser.error("provide minutes, e.g. python timer.py 45")
    if minutes <= 0:
        parser.error("minutes must be a positive integer")

    try:
        run_countdown(minutes)
    except KeyboardInterrupt:
        print("\nTimer cancelled.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
