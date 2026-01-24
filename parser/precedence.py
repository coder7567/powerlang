"""
Operator precedence and associativity handling for PowerLang parser
"""

from enum import Enum, auto
from typing import Dict, Optional, List
from ..lexer.tokens import TokenType

class Precedence(Enum):
    """Precedence levels for operators"""
    NONE = 0
    ASSIGNMENT = 1          # = += -= etc.
    TERNARY = 2             # ? :
    NULL_COALESCE = 3       # ??
    LOGICAL_OR = 4          # -or
    LOGICAL_AND = 5         # -and
    BITWISE_OR = 6          # |
    BITWISE_XOR = 7         # ^
    BITWISE_AND = 8         # &
    EQUALITY = 9            # -eq -ne -like -match etc.
    RELATIONAL = 10         # -gt -lt -ge -le
    SHIFT = 11              # << >>
    ADDITIVE = 12           # + -
    MULTIPLICATIVE = 13     # * / %
    POWER = 14              # **
    UNARY = 15              # - + -not !
    POSTFIX = 16            # ++ -- after operand
    CALL = 17               # () [] . :: ?.
    PRIMARY = 18            # literals, variables, groups

class Associativity(Enum):
    """Associativity of operators"""
    LEFT = auto()
    RIGHT = auto()
    NONE = auto()

# Operator precedence mapping
OPERATOR_PRECEDENCE: Dict[TokenType, Precedence] = {
    # Assignment operators
    TokenType.EQUAL: Precedence.ASSIGNMENT,
    TokenType.PLUS_EQUAL: Precedence.ASSIGNMENT,
    TokenType.MINUS_EQUAL: Precedence.ASSIGNMENT,
    TokenType.STAR_EQUAL: Precedence.ASSIGNMENT,
    TokenType.SLASH_EQUAL: Precedence.ASSIGNMENT,
    TokenType.PERCENT_EQUAL: Precedence.ASSIGNMENT,
    TokenType.CARET_EQUAL: Precedence.ASSIGNMENT,
    TokenType.AMPERSAND_EQUAL: Precedence.ASSIGNMENT,
    TokenType.PIPE_EQUAL: Precedence.ASSIGNMENT,
    
    # Ternary
    TokenType.QUESTION: Precedence.TERNARY,
    
    # Null coalescing
    TokenType.QUESTION_QUESTION: Precedence.NULL_COALESCE,
    
    # Logical operators
    TokenType.OR: Precedence.LOGICAL_OR,
    TokenType.AND: Precedence.LOGICAL_AND,
    
    # Bitwise operators
    TokenType.PIPE: Precedence.BITWISE_OR,
    TokenType.CARET: Precedence.BITWISE_XOR,
    TokenType.AMPERSAND: Precedence.BITWISE_AND,
    
    # Equality operators
    TokenType.EQ: Precedence.EQUALITY,
    TokenType.NE: Precedence.EQUALITY,
    TokenType.LIKE: Precedence.EQUALITY,
    TokenType.MATCH: Precedence.EQUALITY,
    TokenType.CONTAINS: Precedence.EQUALITY,
    TokenType.NOTCONTAINS: Precedence.EQUALITY,
    TokenType.IN_OP: Precedence.EQUALITY,
    TokenType.NOTIN: Precedence.EQUALITY,
    TokenType.IS_OP: Precedence.EQUALITY,
    TokenType.ISNOT: Precedence.EQUALITY,
    TokenType.REPLACE: Precedence.EQUALITY,
    
    # Relational operators
    TokenType.GT: Precedence.RELATIONAL,
    TokenType.LT: Precedence.RELATIONAL,
    TokenType.GE: Precedence.RELATIONAL,
    TokenType.LE: Precedence.RELATIONAL,
    
    # Shift operators
    TokenType.LESS_LESS: Precedence.SHIFT,
    TokenType.GREATER_GREATER: Precedence.SHIFT,
    
    # Additive operators
    TokenType.PLUS: Precedence.ADDITIVE,
    TokenType.MINUS: Precedence.ADDITIVE,
    
    # Multiplicative operators
    TokenType.STAR: Precedence.MULTIPLICATIVE,
    TokenType.SLASH: Precedence.MULTIPLICATIVE,
    TokenType.PERCENT: Precedence.MULTIPLICATIVE,
    
    # Power operator
    TokenType.STAR_STAR: Precedence.POWER,
    
    # Unary operators
    # Removed to avoid conflict with def get_unary_operator_precedence(...)
    # TokenType.PLUS: Precedence.UNARY,
    # TokenType.MINUS: Precedence.UNARY,
    # TokenType.NOT: Precedence.UNARY,
    
    # Postfix operators
    TokenType.PLUS_PLUS: Precedence.POSTFIX,
    TokenType.MINUS_MINUS: Precedence.POSTFIX,
    
    # Call/access operators
    TokenType.LPAREN: Precedence.CALL,
    TokenType.LBRACKET: Precedence.CALL,
    TokenType.DOT: Precedence.CALL,
    TokenType.QUESTION_DOT: Precedence.CALL,
    TokenType.DOUBLE_COLON: Precedence.CALL,
}

# Operator associativity mapping
OPERATOR_ASSOCIATIVITY: Dict[TokenType, Associativity] = {
    # Right-associative
    TokenType.EQUAL: Associativity.RIGHT,
    TokenType.PLUS_EQUAL: Associativity.RIGHT,
    TokenType.MINUS_EQUAL: Associativity.RIGHT,
    TokenType.STAR_EQUAL: Associativity.RIGHT,
    TokenType.SLASH_EQUAL: Associativity.RIGHT,
    TokenType.PERCENT_EQUAL: Associativity.RIGHT,
    TokenType.CARET_EQUAL: Associativity.RIGHT,
    TokenType.AMPERSAND_EQUAL: Associativity.RIGHT,
    TokenType.PIPE_EQUAL: Associativity.RIGHT,
    TokenType.QUESTION: Associativity.RIGHT,  # Ternary
    
    # Left-associative
    TokenType.QUESTION_QUESTION: Associativity.LEFT,
    TokenType.OR: Associativity.LEFT,
    TokenType.AND: Associativity.LEFT,
    TokenType.PIPE: Associativity.LEFT,
    TokenType.CARET: Associativity.LEFT,
    TokenType.AMPERSAND: Associativity.LEFT,
    TokenType.EQ: Associativity.LEFT,
    TokenType.NE: Associativity.LEFT,
    TokenType.LIKE: Associativity.LEFT,
    TokenType.MATCH: Associativity.LEFT,
    TokenType.CONTAINS: Associativity.LEFT,
    TokenType.NOTCONTAINS: Associativity.LEFT,
    TokenType.IN_OP: Associativity.LEFT,
    TokenType.NOTIN: Associativity.LEFT,
    TokenType.IS_OP: Associativity.LEFT,
    TokenType.ISNOT: Associativity.LEFT,
    TokenType.REPLACE: Associativity.LEFT,
    TokenType.GT: Associativity.LEFT,
    TokenType.LT: Associativity.LEFT,
    TokenType.GE: Associativity.LEFT,
    TokenType.LE: Associativity.LEFT,
    TokenType.LESS_LESS: Associativity.LEFT,
    TokenType.GREATER_GREATER: Associativity.LEFT,
    TokenType.PLUS: Associativity.LEFT,
    TokenType.MINUS: Associativity.LEFT,
    TokenType.STAR: Associativity.LEFT,
    TokenType.SLASH: Associativity.LEFT,
    TokenType.PERCENT: Associativity.LEFT,
    TokenType.CARET: Associativity.LEFT,  # Power is left-associative in PowerLang
    
    # Non-associative (unary operators)
    TokenType.PLUS: Associativity.NONE,
    TokenType.MINUS: Associativity.NONE,
    TokenType.NOT: Associativity.NONE,
    
    # Postfix operators are non-associative
    TokenType.PLUS_PLUS: Associativity.NONE,
    TokenType.MINUS_MINUS: Associativity.NONE,
    
    # Call/access operators are left-associative
    TokenType.LPAREN: Associativity.LEFT,
    TokenType.LBRACKET: Associativity.LEFT,
    TokenType.DOT: Associativity.LEFT,
    TokenType.QUESTION_DOT: Associativity.LEFT,
    TokenType.DOUBLE_COLON: Associativity.LEFT,
}

def get_precedence(token_type: TokenType) -> Precedence:
    """Get precedence level for a token type"""
    return OPERATOR_PRECEDENCE.get(token_type, Precedence.NONE)

def get_associativity(token_type: TokenType) -> Associativity:
    """Get associativity for a token type"""
    return OPERATOR_ASSOCIATIVITY.get(token_type, Associativity.LEFT)

def compare_precedence(left: TokenType, right: TokenType) -> int:
    """
    Compare precedence of two operators.
    Returns: -1 if left < right, 0 if equal, 1 if left > right
    """
    left_prec = get_precedence(left)
    right_prec = get_precedence(right)
    
    if left_prec.value < right_prec.value:
        return -1
    elif left_prec.value > right_prec.value:
        return 1
    else:
        return 0

def can_be_binary_operator(token_type: TokenType) -> bool:
    """Check if token type can be a binary operator"""
    binary_operators = {
        TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH,
        TokenType.PERCENT, TokenType.CARET, TokenType.EQ, TokenType.NE,
        TokenType.GT, TokenType.LT, TokenType.GE, TokenType.LE,
        TokenType.LIKE, TokenType.MATCH, TokenType.CONTAINS, TokenType.NOTCONTAINS,
        TokenType.IN_OP, TokenType.NOTIN, TokenType.IS_OP, TokenType.ISNOT,
        TokenType.REPLACE, TokenType.AND, TokenType.OR,
        TokenType.AMPERSAND, TokenType.PIPE, TokenType.CARET,
        TokenType.LESS_LESS, TokenType.GREATER_GREATER,
        TokenType.QUESTION_QUESTION
    }
    return token_type in binary_operators

def can_be_unary_operator(token_type: TokenType) -> bool:
    """Check if token type can be a unary operator"""
    unary_operators = {
        TokenType.PLUS, TokenType.MINUS, TokenType.NOT,
        TokenType.PLUS_PLUS, TokenType.MINUS_MINUS
    }
    return token_type in unary_operators

def can_be_assignment_operator(token_type: TokenType) -> bool:
    """Check if token type can be an assignment operator"""
    assignment_operators = {
        TokenType.EQUAL, TokenType.PLUS_EQUAL, TokenType.MINUS_EQUAL,
        TokenType.STAR_EQUAL, TokenType.SLASH_EQUAL, TokenType.PERCENT_EQUAL,
        TokenType.CARET_EQUAL, TokenType.AMPERSAND_EQUAL, TokenType.PIPE_EQUAL
    }
    return token_type in assignment_operators

def is_right_associative(token_type: TokenType) -> bool:
    """Check if operator is right-associative"""
    return get_associativity(token_type) == Associativity.RIGHT

def is_left_associative(token_type: TokenType) -> bool:
    """Check if operator is left-associative"""
    return get_associativity(token_type) == Associativity.LEFT

def get_binary_operator_precedence(token_type: TokenType) -> Optional[Precedence]:
    """Get precedence for binary operator usage of a token"""
    if can_be_binary_operator(token_type):
        return get_precedence(token_type)
    return None

def get_unary_operator_precedence(token_type: TokenType) -> Optional[Precedence]:
    """Get precedence for unary operator usage of a token"""
    if can_be_unary_operator(token_type):
        return Precedence.UNARY
    return None

def get_postfix_operator_precedence(token_type: TokenType) -> Optional[Precedence]:
    """Get precedence for postfix operator usage of a token"""
    if token_type in (TokenType.PLUS_PLUS, TokenType.MINUS_MINUS):
        return Precedence.POSTFIX
    return None

class PrecedenceHandler:
    """Handles operator precedence for Pratt parser"""
    
    def __init__(self):
        self.precedence_stack: List[Precedence] = []
    
    def push_precedence(self, precedence: Precedence) -> None:
        """Push precedence level onto stack"""
        self.precedence_stack.append(precedence)
    
    def pop_precedence(self) -> Optional[Precedence]:
        """Pop precedence level from stack"""
        if self.precedence_stack:
            return self.precedence_stack.pop()
        return None
    
    def current_precedence(self) -> Precedence:
        """Get current precedence level"""
        if self.precedence_stack:
            return self.precedence_stack[-1]
        return Precedence.NONE
    
    def should_apply_operator(self, current: TokenType, next_op: TokenType) -> bool:
        """
        Determine if current operator should be applied before next operator.
        Based on precedence and associativity rules.
        """
        current_prec = get_precedence(current)
        next_prec = get_precedence(next_op)
        
        if current_prec.value > next_prec.value:
            return True
        elif current_prec.value < next_prec.value:
            return False
        else:
            # Same precedence - check associativity
            if is_left_associative(current):
                return True
            elif is_right_associative(current):
                return False
            else:
                # Non-associative operators cannot be chained
                raise ValueError(
                    f"Non-associative operator {current} cannot be chained "
                    f"with {next_op} at same precedence level"
                )
    
    def get_expression_precedence(self, token_type: TokenType, 
                                  is_unary: bool = False,
                                  is_postfix: bool = False) -> Precedence:
        """Get appropriate precedence for expression parsing"""
        if is_unary:
            prec = get_unary_operator_precedence(token_type)
            return prec or Precedence.NONE
        elif is_postfix:
            prec = get_postfix_operator_precedence(token_type)
            return prec or Precedence.NONE
        else:
            return get_precedence(token_type)
