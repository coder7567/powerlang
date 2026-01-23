"""
Operator definitions for PowerLang
"""

from .tokens import TokenType

# Single character operators
SINGLE_CHAR_OPERATORS = {
    '+': TokenType.PLUS,
    '-': TokenType.MINUS,
    '*': TokenType.STAR,
    '/': TokenType.SLASH,
    '%': TokenType.PERCENT,
    '^': TokenType.CARET,
    '&': TokenType.AMPERSAND,
    '|': TokenType.PIPE,
    '~': TokenType.TILDE,
    '=': TokenType.EQUAL,
    '(': TokenType.LPAREN,
    ')': TokenType.RPAREN,
    '[': TokenType.LBRACKET,
    ']': TokenType.RBRACKET,
    '{': TokenType.LBRACE,
    '}': TokenType.RBRACE,
    '.': TokenType.DOT,
    ',': TokenType.COMMA,
    ':': TokenType.COLON,
    ';': TokenType.SEMICOLON,
    '@': TokenType.AT,
    '#': TokenType.HASH,
    '?': TokenType.QUESTION,
    '<': TokenType.LT,
    '>': TokenType.GT,
}

# Multi-character operators
MULTI_CHAR_OPERATORS = {
    # Comparison operators
    '-eq': TokenType.EQ,
    '-ne': TokenType.NE,
    '-gt': TokenType.GT,
    '-lt': TokenType.LT,
    '-ge': TokenType.GE,
    '-le': TokenType.LE,
    '-like': TokenType.LIKE,
    '-match': TokenType.MATCH,
    '-contains': TokenType.CONTAINS,
    '-notcontains': TokenType.NOTCONTAINS,
    '-in': TokenType.IN_OP,
    '-notin': TokenType.NOTIN,
    '-is': TokenType.IS_OP,
    '-isnot': TokenType.ISNOT,
    '-replace': TokenType.REPLACE,
    
    # Logical operators
    '-and': TokenType.AND,
    '-or': TokenType.OR,
    '-not': TokenType.NOT,
    
    # Assignment operators
    '+=': TokenType.PLUS_EQUAL,
    '-=': TokenType.MINUS_EQUAL,
    '*=': TokenType.STAR_EQUAL,
    '/=': TokenType.SLASH_EQUAL,
    '%=': TokenType.PERCENT_EQUAL,
    '^=': TokenType.CARET_EQUAL,
    '&=': TokenType.AMPERSAND_EQUAL,
    '|=': TokenType.PIPE_EQUAL,
    
    # Increment/Decrement
    '++': TokenType.PLUS_PLUS,
    '--': TokenType.MINUS_MINUS,
    
    # Bitwise
    '&&': TokenType.AMPERSAND_AMPERSAND,
    '||': TokenType.PIPE_PIPE,
    '^^': TokenType.CARET_CARET,
    
    # Shift
    '<<': TokenType.LESS_LESS,
    '>>': TokenType.GREATER_GREATER,
    
    # Null operators
    '??': TokenType.QUESTION_QUESTION,
    '?.': TokenType.QUESTION_DOT,
    
    # Special
    '::': TokenType.DOUBLE_COLON,
    '=>': TokenType.ARROW,
    '...': TokenType.ELLIPSIS,
    '${': TokenType.DOLLAR_LBRACE,
    
    # Comment markers
    '<#': TokenType.BLOCK_COMMENT_START,
    '#>': TokenType.BLOCK_COMMENT_END,
}

# Combined operators dictionary
OPERATORS = {**SINGLE_CHAR_OPERATORS, **MULTI_CHAR_OPERATORS}

# Reverse mapping from TokenType to operator string
OPERATOR_MAP = {v: k for k, v in OPERATORS.items()}

# Operator precedence table
OPERATOR_PRECEDENCE = {
    TokenType.QUESTION_DOT: 1,
    TokenType.DOT: 1,
    TokenType.DOUBLE_COLON: 1,
    
    TokenType.PLUS_PLUS: 2,
    TokenType.MINUS_MINUS: 2,
    
    TokenType.CARET: 3,  # Power
    
    TokenType.TILDE: 4,  # Bitwise NOT
    TokenType.NOT: 4,    # Logical NOT
    
    TokenType.STAR: 5,
    TokenType.SLASH: 5,
    TokenType.PERCENT: 5,
    
    TokenType.PLUS: 6,
    TokenType.MINUS: 6,
    
    TokenType.LESS_LESS: 7,
    TokenType.GREATER_GREATER: 7,
    
    TokenType.LT: 8,
    TokenType.GT: 8,
    TokenType.LE: 8,
    TokenType.GE: 8,
    
    TokenType.EQ: 9,
    TokenType.NE: 9,
    TokenType.LIKE: 9,
    TokenType.MATCH: 9,
    TokenType.CONTAINS: 9,
    TokenType.NOTCONTAINS: 9,
    TokenType.IN_OP: 9,
    TokenType.NOTIN: 9,
    TokenType.IS_OP: 9,
    TokenType.ISNOT: 9,
    TokenType.REPLACE: 9,
    
    TokenType.AMPERSAND: 10,
    
    TokenType.CARET: 11,  # XOR
    
    TokenType.PIPE: 12,
    
    TokenType.AND: 13,
    
    TokenType.OR: 14,
    
    TokenType.QUESTION_QUESTION: 15,
    
    TokenType.QUESTION: 16,  # Ternary
    
    TokenType.EQUAL: 17,
    TokenType.PLUS_EQUAL: 17,
    TokenType.MINUS_EQUAL: 17,
    TokenType.STAR_EQUAL: 17,
    TokenType.SLASH_EQUAL: 17,
    TokenType.PERCENT_EQUAL: 17,
    TokenType.CARET_EQUAL: 17,
    TokenType.AMPERSAND_EQUAL: 17,
    TokenType.PIPE_EQUAL: 17,
    
    TokenType.COMMA: 18,
}

def is_operator_char(char: str) -> bool:
    """Check if character can be part of an operator"""
    return char in '+-*/%=^&|~<>!?:.$#@'

def is_operator_start(char: str) -> bool:
    """Check if character can start an operator"""
    return char in '+-*/%=^&|~<>!?:.$#@'

def get_operator_token_type(op: str) -> TokenType:
    """Get TokenType for an operator string"""
    return OPERATORS.get(op, TokenType.IDENTIFIER)

def get_operator_precedence(token_type: TokenType) -> int:
    """Get precedence level for an operator token type"""
    return OPERATOR_PRECEDENCE.get(token_type, 0)

def is_comparison_operator(token_type: TokenType) -> bool:
    """Check if token type is a comparison operator"""
    comparison_ops = {
        TokenType.EQ, TokenType.NE, TokenType.GT, TokenType.LT,
        TokenType.GE, TokenType.LE, TokenType.LIKE, TokenType.MATCH,
        TokenType.CONTAINS, TokenType.NOTCONTAINS, TokenType.IN_OP,
        TokenType.NOTIN, TokenType.IS_OP, TokenType.ISNOT, TokenType.REPLACE
    }
    return token_type in comparison_ops

def is_logical_operator(token_type: TokenType) -> bool:
    """Check if token type is a logical operator"""
    logical_ops = {TokenType.AND, TokenType.OR, TokenType.NOT}
    return token_type in logical_ops

def is_assignment_operator(token_type: TokenType) -> bool:
    """Check if token type is an assignment operator"""
    assignment_ops = {
        TokenType.EQUAL, TokenType.PLUS_EQUAL, TokenType.MINUS_EQUAL,
        TokenType.STAR_EQUAL, TokenType.SLASH_EQUAL, TokenType.PERCENT_EQUAL,
        TokenType.CARET_EQUAL, TokenType.AMPERSAND_EQUAL, TokenType.PIPE_EQUAL
    }
    return token_type in assignment_ops

def is_arithmetic_operator(token_type: TokenType) -> bool:
    """Check if token type is an arithmetic operator"""
    arithmetic_ops = {
        TokenType.PLUS, TokenType.MINUS, TokenType.STAR,
        TokenType.SLASH, TokenType.PERCENT, TokenType.CARET
    }
    return token_type in arithmetic_ops
