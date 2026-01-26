"""
Runtime value types for PowerLang interpreter.
"""

from abc import ABC
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .environment import Environment


@dataclass
class RuntimeValue(ABC):
    """Base class for all runtime values."""

    def is_truthy(self) -> bool:
        """Whether this value is truthy in boolean context."""
        return True

    def __str__(self) -> str:
        return repr(self)


@dataclass
class NullValue(RuntimeValue):
    """Represents null/nil."""

    def is_truthy(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "null"


@dataclass
class BoolValue(RuntimeValue):
    """Boolean value."""

    value: bool

    def is_truthy(self) -> bool:
        return self.value

    def __repr__(self) -> str:
        return "true" if self.value else "false"


@dataclass
class IntValue(RuntimeValue):
    """Integer value."""

    value: int

    def is_truthy(self) -> bool:
        return self.value != 0

    def __repr__(self) -> str:
        return str(self.value)


@dataclass
class FloatValue(RuntimeValue):
    """Floating-point value."""

    value: float

    def is_truthy(self) -> bool:
        return self.value != 0.0

    def __repr__(self) -> str:
        s = str(self.value)
        if "e" not in s and "." not in s:
            s += ".0"
        return s


@dataclass
class StringValue(RuntimeValue):
    """String value."""

    value: str

    def is_truthy(self) -> bool:
        return len(self.value) > 0

    def __repr__(self) -> str:
        return repr(self.value)


@dataclass
class ArrayValue(RuntimeValue):
    """Array (list) value."""

    elements: List[RuntimeValue] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.elements)

    def __repr__(self) -> str:
        inner = ", ".join(repr(e) for e in self.elements)
        return f"@{inner}"


@dataclass
class HashValue(RuntimeValue):
    """Hash (dictionary) value. Keys must be usable as dict keys."""

    pairs: Dict[Any, RuntimeValue] = field(default_factory=dict)

    def __repr__(self) -> str:
        parts = []
        for k, v in self.pairs.items():
            sk = repr(k) if isinstance(k, str) else str(k)
            parts.append(f"{sk}: {v!r}")
        return "{" + ", ".join(parts) + "}"


@dataclass
class FunctionValue(RuntimeValue):
    """User-defined function."""

    name: Optional[str]
    params: List["ParameterInfo"]
    body: Any  # Block AST node
    closure: "Environment"
    is_async: bool = False

    def __repr__(self) -> str:
        n = self.name or "<lambda>"
        return f"<function {n}>"


@dataclass
class ParameterInfo:
    """Parameter metadata for user functions."""

    name: str
    has_default: bool = False
    default_value: Optional[RuntimeValue] = None


@dataclass
class BuiltinFunctionValue(RuntimeValue):
    """Built-in function."""

    name: str
    fn: Callable[..., RuntimeValue]
    arity: Optional[int] = None  # None = variadic

    def __repr__(self) -> str:
        return f"<builtin {self.name}>"


@dataclass
class ClassValue(RuntimeValue):
    """Runtime class (type)."""

    name: str
    methods: Dict[str, FunctionValue] = field(default_factory=dict)
    base: Optional["ClassValue"] = None

    def __repr__(self) -> str:
        return f"<class {self.name}>"


@dataclass
class InstanceValue(RuntimeValue):
    """Object instance."""

    klass: ClassValue
    fields: Dict[str, RuntimeValue] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"<{self.klass.name} instance>"


# Convenience constants
NULL = NullValue()


def value_to_python(v: RuntimeValue) -> Any:
    """Convert a RuntimeValue to a Python value (for builtins, etc.)."""
    if isinstance(v, NullValue):
        return None
    if isinstance(v, BoolValue):
        return v.value
    if isinstance(v, IntValue):
        return v.value
    if isinstance(v, FloatValue):
        return v.value
    if isinstance(v, StringValue):
        return v.value
    if isinstance(v, ArrayValue):
        return [value_to_python(e) for e in v.elements]
    if isinstance(v, HashValue):
        return {k: value_to_python(val) for k, val in v.pairs.items()}
    return v


def python_to_value(x: Any) -> RuntimeValue:
    """Convert a Python value to RuntimeValue."""
    if x is None:
        return NULL
    if isinstance(x, bool):
        return BoolValue(x)
    if isinstance(x, int):
        return IntValue(x)
    if isinstance(x, float):
        return FloatValue(x)
    if isinstance(x, str):
        return StringValue(x)
    if isinstance(x, list):
        return ArrayValue([python_to_value(e) for e in x])
    if isinstance(x, dict):
        out: Dict[Any, RuntimeValue] = {}
        for k, val in x.items():
            key = k if isinstance(k, (str, int, float, bool)) else str(k)
            out[key] = python_to_value(val)
        return HashValue(out)
    return NULL
