"""
ID Registry.

Provides monotonically increasing identifiers scoped by prefix so that
every FAIRFluids object receives a unique, deterministic ID within a
single conversion run.
"""

from __future__ import annotations


class IDRegistry:
    """Thread-unsafe but deterministic ID generator."""

    def __init__(self) -> None:
        self._counters: dict[str, int] = {}

    def new_id(self, prefix: str) -> str:
        count = self._counters.get(prefix, 0) + 1
        self._counters[prefix] = count
        return f"{prefix}_{count}"

    def reset(self) -> None:
        self._counters.clear()
