"""
Runtime environment and built-in bindings for PowerLang.
"""

from typing import Any, Optional

from .environment import Environment
from .memory import MemoryManager
from .values import RuntimeValue

# Avoid circular import: builtins imports interpreter.values
def _load_builtins() -> dict:
    from ..builtins import get_builtins
    return get_builtins()


class Runtime:
    """Runtime environment: global scope, memory, and built-ins."""

    def __init__(self) -> None:
        self.memory = MemoryManager()
        self.globals: Environment = Environment(parent=None)
        self._seed_builtins()

    def _seed_builtins(self) -> None:
        for name, value in _load_builtins().items():
            self.globals.define(name, value, constant=True)

    def new_scope(self) -> Environment:
        """Create a new scope chain rooted at globals."""
        return self.globals.child()

    def run(self, program: Any) -> Optional[RuntimeValue]:
        """Run a parsed Program AST. Returns last expression value or exit value."""
        from .interpreter import Interpreter, ReturnSignal

        interp = Interpreter(self)
        try:
            return interp.run(program)
        except ReturnSignal as r:
            # Top-level return = program exit value
            return r.value

