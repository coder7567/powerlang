"""
Token definitions for PowerLang lexer
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Any

class TokenType(Enum):
    """All token types in PowerLang"""
    
    # Identifiers and literals
    IDENTIFIER = auto()
    VARIABLE = auto() 
    STRING = auto()
    INTEGER = auto()
    DOUBLE = auto()
    BOOL = auto()
    
    # Variables
    DOLLAR = auto()
    
    # Keywords
    CLASS = auto()
    FUNCTION = auto()
    RETURN = auto()
    IF = auto()
    ELSE = auto()
    ELSEIF = auto()
    FOR = auto()
    WHILE = auto()
    DO = auto()
    FOREACH = auto()
    IN = auto()
    SWITCH = auto()
    CASE = auto()
    DEFAULT = auto()
    BREAK = auto()
    CONTINUE = auto()
    NAMESPACE = auto()
    USING = auto()
    EVENT = auto()
    CONST = auto()
    NEW = auto()
    THIS = auto()
    NULL = auto()
    TRUE = auto()
    FALSE = auto()
    TRY = auto()
    CATCH = auto()
    FINALLY = auto()
    THROW = auto()
    IMPORT = auto()
    EXPORT = auto()
    FROM = auto()
    AS = auto()
    IS = auto()
    INSTANCEOF = auto()
    TYPEOF = auto()
    ASYNC = auto()
    AWAIT = auto()
    
    # Types
    INT_TYPE = auto()
    DOUBLE_TYPE = auto()
    STRING_TYPE = auto()
    BOOL_TYPE = auto()
    ARRAY_TYPE = auto()
    VOID_TYPE = auto()
    OBJECT_TYPE = auto()
    DATETIME_TYPE = auto()
    HASHTABLE_TYPE = auto()
    LIST_TYPE = auto()
    DICTIONARY_TYPE = auto()
    
    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    CARET = auto()
    AMPERSAND = auto()
    PIPE = auto()
    TILDE = auto()
    
    # Comparison operators
    EQ = auto()
    NE = auto()
    GT = auto()
    LT = auto()
    GE = auto()
    LE = auto()
    LIKE = auto()
    MATCH = auto()
    CONTAINS = auto()
    NOTCONTAINS = auto()
    IN_OP = auto()
    NOTIN = auto()
    IS_OP = auto()
    ISNOT = auto()
    REPLACE = auto()
    
    # Logical operators
    AND = auto()
    OR = auto()
    NOT = auto()
    
    # Assignment
    EQUAL = auto()
    PLUS_EQUAL = auto()
    MINUS_EQUAL = auto()
    STAR_EQUAL = auto()
    SLASH_EQUAL = auto()
    PERCENT_EQUAL = auto()
    CARET_EQUAL = auto()
    AMPERSAND_EQUAL = auto()
    PIPE_EQUAL = auto()
    
    # Increment/Decrement
    PLUS_PLUS = auto()
    MINUS_MINUS = auto()
    
    # Bitwise operators
    AMPERSAND_AMPERSAND = auto()
    PIPE_PIPE = auto()
    CARET_CARET = auto()
    
    # Shift operators
    LESS_LESS = auto()
    GREATER_GREATER = auto()
    
    # Null operators
    QUESTION = auto()
    QUESTION_QUESTION = auto()
    QUESTION_DOT = auto()
    
    # Brackets and punctuation
    LBRACKET = auto()
    RBRACKET = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    DOT = auto()
    COMMA = auto()
    COLON = auto()
    SEMICOLON = auto()
    AT = auto()
    HASH = auto()
    
    # Comments
    COMMENT = auto()
    BLOCK_COMMENT_START = auto()
    BLOCK_COMMENT_END = auto()
    
    # Special
    DOUBLE_COLON = auto()
    ARROW = auto()
    ELLIPSIS = auto()
    DOLLAR_LBRACE = auto()
    
    # End of file
    EOF = auto()

@dataclass
class Token:
    """Token class representing a lexeme with its metadata"""
    type: TokenType
    lexeme: str
    literal: Optional[Any]
    line: int
    column: int
    position: int
    
    def __str__(self) -> str:
        return f"Token({self.type}, '{self.lexeme}', {self.literal}, line={self.line}, col={self.column})"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    @property
    def length(self) -> int:
        """Length of the lexeme"""
        return len(self.lexeme)
    
    def clone(self, new_type: Optional[TokenType] = None, 
              new_lexeme: Optional[str] = None,
              new_literal: Optional[Any] = None) -> 'Token':
        """Create a copy of the token with optional modifications"""
        return Token(
            type=new_type or self.type,
            lexeme=new_lexeme or self.lexeme,
            literal=new_literal or self.literal,
            line=self.line,
            column=self.column,
            position=self.position
        )
