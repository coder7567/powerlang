"""
Variable environment (scopes) for PowerLang interpreter.
"""

from typing import Dict, Optional

from .values import RuntimeValue
from ..errors import NameError as PplNameError, RuntimeError as PplRuntimeError


def _normalize_name(name: str) -> str:
    """Strip leading $ and normalize for storage/lookup."""
    s = name.strip()
    if s.startswith("$"):
        s = s[1:]
    return s.lower()


class Environment:
    """Variable environment with parent scope chain."""

    def __init__(self, parent: Optional["Environment"] = None):
        self._parent = parent
        self._values: Dict[str, RuntimeValue] = {}
        self._consts: Dict[str, bool] = {}  # names that are readonly

    def define(self, name: str, value: RuntimeValue, *, constant: bool = False) -> None:
        """Define a variable in this scope."""
        key = _normalize_name(name)
        # If the name already exists in an ancestor scope, update it there
        env: Optional[Environment] = self
        while env is not None:
            if key in env._values:
                # If the existing name is constant/readonly, respect it
                if env._consts.get(key):
                    if constant:
                        # already defined as const; nothing to do
                        return
                    # trying to overwrite a constant
                    raise PplRuntimeError(f"Cannot assign to constant '{name}'")
                # update the existing binding in the ancestor scope
                env._values[key] = value
                if constant:
                    env._consts[key] = True
                return
            env = env._parent

        # Not found in any ancestor: define in current scope
        self._values[key] = value
        if constant:
            self._consts[key] = True

    def assign(self, name: str, value: RuntimeValue) -> None:
        """Assign to a variable. Raises if not found or readonly."""
        key = _normalize_name(name)
        if key in self._values:
            if self._consts.get(key):
                raise PplRuntimeError(f"Cannot assign to constant '{name}'")
            self._values[key] = value
            return
        if self._parent is not None:
            self._parent.assign(name, value)
            return
        raise PplNameError(f"Undefined variable '{name}'")

    def get(self, name: str) -> RuntimeValue:
        """Resolve a variable. Raises NameError if not found."""
        key = _normalize_name(name)
        if key in self._values:
            return self._values[key]
        if self._parent is not None:
            return self._parent.get(name)
        raise PplNameError(f"Undefined variable '{name}'")

    def get_optional(self, name: str) -> Optional[RuntimeValue]:
        """Resolve a variable. Returns None if not found."""
        key = _normalize_name(name)
        if key in self._values:
            return self._values[key]
        if self._parent is not None:
            return self._parent.get_optional(name)
        return None

    def assign_at(self, distance: int, name: str, value: RuntimeValue) -> None:
        """Assign at a specific scope depth (for closures)."""
        env = self._ancestor(distance)
        key = _normalize_name(name)
        if env is not None and key in env._values:
            if env._consts.get(key):
                raise PplRuntimeError(f"Cannot assign to constant '{name}'")
            env._values[key] = value
            return
        self.assign(name, value)

    def get_at(self, distance: int, name: str) -> RuntimeValue:
        """Resolve at a specific scope depth (for closures)."""
        env = self._ancestor(distance)
        if env is None:
            return self.get(name)
        key = _normalize_name(name)
        if key in env._values:
            return env._values[key]
        return self.get(name)

    def _ancestor(self, distance: int) -> Optional["Environment"]:
        """Get ancestor environment at given depth."""
        env: Optional[Environment] = self
        for _ in range(distance):
            if env is None:
                break
            env = env._parent
        return env

    def child(self) -> "Environment":
        """Create a child scope."""
        return Environment(parent=self)
