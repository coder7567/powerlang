from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    # ===== Special =====
    EOF = auto()
    NEWLINE = auto()

    # ===== Identifiers & Literals =====
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    BOOLEAN = auto()
    NULL = auto()

    # ===== Variable Prefix =====
    DOLLAR = auto()          # $

    # ===== Type Brackets =====
    LBRACKET = auto()        # [
    RBRACKET = auto()        # ]

    # ===== Grouping =====
    LPAREN = auto()          # (
    RPAREN = auto()          # )
    LBRACE = auto()          # {
    RBRACE = auto()          # }

    # ===== Separators =====
    COMMA = auto()
    DOT = auto()
    COLON = auto()
    SEMICOLON = auto()

    # ===== Assignment =====
    ASSIGN = auto()          # =
    PLUS_ASSIGN = auto()     # +=
    MINUS_ASSIGN = auto()    # -=
    MULT_ASSIGN = auto()     # *=
    DIV_ASSIGN = auto()      # /=

    # ===== Arithmetic Operators =====
    PLUS = auto()            # +
    MINUS = auto()           # -
    MULTIPLY = auto()        # *
    DIVIDE = auto()          # /
    MODULO = auto()          # %

    INCREMENT = auto()       # ++
    DECREMENT = auto()       # --

    # ===== Comparison Operators (PowerShell-style) =====
    EQ = auto()              # -eq
    NE = auto()              # -ne
    GT = auto()              # -gt
    LT = auto()              # -lt
    GE = auto()              # -ge
    LE = auto()              # -le

    # ===== Logical Operators =====
    AND = auto()             # -and
    OR = auto()              # -or
    NOT = auto()             # -not

    # ===== Keywords =====
    CLASS = auto()
    NAMESPACE = auto()
    INTERFACE = auto()
    EVENT = auto()
    DELEGATE = auto()
    STATIC = auto()
    CONST = auto()
    RETURN = auto()
    NEW = auto()

    IF = auto()
    ELSEIF = auto()
    ELSE = auto()
    SWITCH = auto()
    DEFAULT = auto()

    FOR = auto()
    WHILE = auto()
    DO = auto()
    FOREACH = auto()
    BREAK = auto()
    CONTINUE = auto()

    TRUE = auto()
    FALSE = auto()


# ===== Keyword Lookup Table =====
KEYWORDS = {
    "class": TokenType.CLASS,
    "namespace": TokenType.NAMESPACE,
    "interface": TokenType.INTERFACE,
    "event": TokenType.EVENT,
    "delegate": TokenType.DELEGATE,
    "static": TokenType.STATIC,
    "const": TokenType.CONST,
    "return": TokenType.RETURN,
    "new": TokenType.NEW,

    "if": TokenType.IF,
    "elseif": TokenType.ELSEIF,
    "else": TokenType.ELSE,
    "switch": TokenType.SWITCH,
    "default": TokenType.DEFAULT,

    "for": TokenType.FOR,
    "while": TokenType.WHILE,
    "do": TokenType.DO,
    "foreach": TokenType.FOREACH,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,

    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "null": TokenType.NULL,
}


@dataclass
class Token:
    type: TokenType
    value: any
    line: int
    column: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value}, {self.line}:{self.column})"
