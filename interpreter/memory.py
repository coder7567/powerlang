"""
Memory management for PowerLang interpreter.
Tracks allocated runtime values and supports simple retain/release.
"""

from typing import Dict, Iterator, Optional

from .values import RuntimeValue


class MemoryManager:
    """Tracks allocated values and reference counts."""

    def __init__(self) -> None:
        self._allocations: Dict[int, RuntimeValue] = {}
        self._refcounts: Dict[int, int] = {}
        self._next_id = 1

    def allocate(self, value: RuntimeValue) -> int:
        """Register a value and return its id. Initial refcount is 1."""
        uid = self._next_id
        self._next_id += 1
        self._allocations[uid] = value
        self._refcounts[uid] = 1
        return uid

    def retain(self, uid: int) -> None:
        """Increment reference count for an allocation."""
        if uid in self._refcounts:
            self._refcounts[uid] += 1

    def release(self, uid: int) -> bool:
        """Decrement reference count. Free if 0. Return True if freed."""
        if uid not in self._refcounts:
            return False
        self._refcounts[uid] -= 1
        if self._refcounts[uid] <= 0:
            del self._refcounts[uid]
            del self._allocations[uid]
            return True
        return False

    def get(self, uid: int) -> Optional[RuntimeValue]:
        """Return the value for an id, or None if freed."""
        return self._allocations.get(uid)

    def free(self, uid: int) -> bool:
        """Force-free an allocation. Return True if it existed."""
        if uid not in self._allocations:
            return False
        del self._allocations[uid]
        self._refcounts.pop(uid, None)
        return True

    def count(self) -> int:
        """Number of currently allocated values."""
        return len(self._allocations)

    def __iter__(self) -> Iterator[tuple[int, RuntimeValue]]:
        """Iterate (id, value) over all allocations."""
        yield from self._allocations.items()
