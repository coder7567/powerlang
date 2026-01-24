from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Any
from ..lexer.tokens import TokenType



# =========================
# Grammar Rule Types
# =========================

class GrammarRuleType(Enum):
    STATEMENT = auto()
    EXPRESSION = auto()
    DECLARATION = auto()
    BLOCK = auto()


# =========================
# Grammar Rule Definition
# =========================

@dataclass
class GrammarRule:
    name: str
    rule_type: GrammarRuleType
    productions: List[Any]

# =========================
# Grammar Container
# =========================

class Grammar:
    """
    Grammar container for all grammar rules.
    Provides lookup and validation utilities.
    """

    def __init__(self, rules: List[GrammarRule]):
        self.rules = rules
        self.rule_map = {rule.name: rule for rule in rules}

    def get(self, name: str) -> GrammarRule:
        if name not in self.rule_map:
            raise KeyError(f"Grammar rule '{name}' not found!")
        return self.rule_map[name]

    def has(self, name: str) -> bool:
        return name in self.rule_map

    def __iter__(self):
        return iter(self.rules)

    def __len__(self):
        return len(self.rules)

# =========================
# Grammar Rules
# =========================

GRAMMAR: List[GrammarRule] = [

    # ---------- PROGRAM ----------

    GrammarRule(
        "program",
        GrammarRuleType.BLOCK,
        [
            ["zero_or_more", "declaration"],
            TokenType.EOF
        ]
    ),

    # ---------- DECLARATIONS ----------

    GrammarRule(
        "declaration",
        GrammarRuleType.DECLARATION,
        [
            ["or",
                "class_declaration",
                "function_declaration",
                "variable_declaration",
                "statement"
            ]
        ]
    ),

    GrammarRule(
        "class_declaration",
        GrammarRuleType.DECLARATION,
        [
            TokenType.CLASS,
            "identifier",
            TokenType.LBRACE,
            ["zero_or_more", "function_declaration"],
            TokenType.RBRACE
        ]
    ),

    GrammarRule(
        "function_declaration",
        GrammarRuleType.DECLARATION,
        [
            TokenType.FUNCTION,
            "identifier",
            TokenType.LPAREN,
            ["optional", "parameter_list"],
            TokenType.RPAREN,
            "block"
        ]
    ),

    GrammarRule(
        "variable_declaration",
        GrammarRuleType.DECLARATION,
        [
            ["optional", "type_annotation"],
            TokenType.VARIABLE,
            TokenType.EQUAL,
            "expression",
            TokenType.SEMICOLON
        ]
    ),

    GrammarRule(
        "type_annotation",
        GrammarRuleType.EXPRESSION,
        [
            TokenType.LBRACKET,
            ["or",
                TokenType.INT_TYPE,
                TokenType.FLOAT_TYPE,
                TokenType.STRING_TYPE,
                TokenType.BOOL_TYPE
            ],
            TokenType.RBRACKET
        ]
    ),

    # ---------- PARAMETERS ----------

    GrammarRule(
        "parameter_list",
        GrammarRuleType.EXPRESSION,
        [
            "parameter",
            ["zero_or_more", [TokenType.COMMA, "parameter"]]
        ]
    ),

    GrammarRule(
        "parameter",
        GrammarRuleType.EXPRESSION,
        [
            ["optional", "type_annotation"],
            "identifier",
            ["optional", [TokenType.EQUAL, "expression"]]
        ]
    ),

    # ---------- STATEMENTS ----------

    GrammarRule(
        "statement",
        GrammarRuleType.STATEMENT,
        [
            ["or",
                "if_statement",
                "return_statement",
                "expression_statement",
                "block"
            ]
        ]
    ),

    GrammarRule(
        "block",
        GrammarRuleType.BLOCK,
        [
            TokenType.LBRACE,
            ["zero_or_more", "statement"],
            TokenType.RBRACE
        ]
    ),

    GrammarRule(
        "if_statement",
        GrammarRuleType.STATEMENT,
        [
            TokenType.IF,
            TokenType.LPAREN,
            "expression",
            TokenType.RPAREN,
            "block"
        ]
    ),

    GrammarRule(
        "return_statement",
        GrammarRuleType.STATEMENT,
        [
            TokenType.RETURN,
            ["optional", "expression"],
            TokenType.SEMICOLON
        ]
    ),

    GrammarRule(
        "expression_statement",
        GrammarRuleType.STATEMENT,
        [
            "expression",
            TokenType.SEMICOLON
        ]
    ),

    # ---------- EXPRESSIONS ----------

    GrammarRule(
        "expression",
        GrammarRuleType.EXPRESSION,
        [
            "assignment"
        ]
    ),

    GrammarRule(
        "assignment",
        GrammarRuleType.EXPRESSION,
        [
            ["or",
                ["sequence", TokenType.VARIABLE, TokenType.EQUAL, "assignment"],
                "logical_or"
            ]
        ]
    ),

    GrammarRule(
        "logical_or",
        GrammarRuleType.EXPRESSION,
        [
            "logical_and",
            ["zero_or_more", [TokenType.OR, "logical_and"]]
        ]
    ),

    GrammarRule(
        "logical_and",
        GrammarRuleType.EXPRESSION,
        [
            "equality",
            ["zero_or_more", [TokenType.AND, "equality"]]
        ]
    ),

    GrammarRule(
        "equality",
        GrammarRuleType.EXPRESSION,
        [
            "comparison",
            ["zero_or_more", [["or", TokenType.EQ, TokenType.NE], "comparison"]]
        ]
    ),

    GrammarRule(
        "comparison",
        GrammarRuleType.EXPRESSION,
        [
            "term",
            ["zero_or_more", [["or", TokenType.GT, TokenType.LT, TokenType.GE, TokenType.LE], "term"]]
        ]
    ),

    GrammarRule(
        "term",
        GrammarRuleType.EXPRESSION,
        [
            "factor",
            ["zero_or_more", [["or", TokenType.PLUS, TokenType.MINUS], "factor"]]
        ]
    ),

    GrammarRule(
        "factor",
        GrammarRuleType.EXPRESSION,
        [
            "unary",
            ["zero_or_more", [["or", TokenType.STAR, TokenType.SLASH], "unary"]]
        ]
    ),

    GrammarRule(
        "unary",
        GrammarRuleType.EXPRESSION,
        [
            ["or",
                ["sequence", ["or", TokenType.NOT, TokenType.MINUS], "unary"],
                "primary"
            ]
        ]
    ),

    GrammarRule(
        "primary",
        GrammarRuleType.EXPRESSION,
        [
            ["or",
                TokenType.INTEGER,
                TokenType.FLOAT,
                TokenType.STRING,
                TokenType.TRUE,
                TokenType.FALSE,
                TokenType.VARIABLE,
                ["sequence", TokenType.LPAREN, "expression", TokenType.RPAREN]
            ]
        ]
    ),


    # ---------- IDENTIFIER ----------

    GrammarRule(
        "identifier",
        GrammarRuleType.EXPRESSION,
        [
            TokenType.IDENTIFIER
        ]
    ),
]
GRAMMAR_INSTANCE = Grammar(GRAMMAR)
