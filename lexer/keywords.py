"""
Keyword definitions for PowerLang
"""

from .tokens import TokenType

# Regular keywords
KEYWORDS = {
    'class': TokenType.CLASS,
    'function': TokenType.FUNCTION,
    'return': TokenType.RETURN,
    'if': TokenType.IF,
    'else': TokenType.ELSE,
    'elseif': TokenType.ELSEIF,
    'for': TokenType.FOR,
    'while': TokenType.WHILE,
    'do': TokenType.DO,
    'foreach': TokenType.FOREACH,
    'in': TokenType.IN,
    'switch': TokenType.SWITCH,
    'case': TokenType.CASE,
    'default': TokenType.DEFAULT,
    'break': TokenType.BREAK,
    'continue': TokenType.CONTINUE,
    'namespace': TokenType.NAMESPACE,
    'using': TokenType.USING,
    'event': TokenType.EVENT,
    'const': TokenType.CONST,
    'new': TokenType.NEW,
    'this': TokenType.THIS,
    'null': TokenType.NULL,
    'true': TokenType.TRUE,
    'false': TokenType.FALSE,
    'try': TokenType.TRY,
    'catch': TokenType.CATCH,
    'finally': TokenType.FINALLY,
    'throw': TokenType.THROW,
    'import': TokenType.IMPORT,
    'export': TokenType.EXPORT,
    'from': TokenType.FROM,
    'as': TokenType.AS,
    'is': TokenType.IS,
    'instanceof': TokenType.INSTANCEOF,
    'typeof': TokenType.TYPEOF,
    'async': TokenType.ASYNC,
    'await': TokenType.AWAIT,
}

# Type keywords (used in [type] annotations)
TYPE_KEYWORDS = {
    'int': TokenType.INT_TYPE,
    'double': TokenType.DOUBLE_TYPE,
    'string': TokenType.STRING_TYPE,
    'bool': TokenType.BOOL_TYPE,
    'array': TokenType.ARRAY_TYPE,
    'void': TokenType.VOID_TYPE,
    'object': TokenType.OBJECT_TYPE,
    'datetime': TokenType.DATETIME_TYPE,
    'hashtable': TokenType.HASHTABLE_TYPE,
    'list': TokenType.LIST_TYPE,
    'dictionary': TokenType.DICTIONARY_TYPE,
}

# Combined lookup for all reserved words
RESERVED_WORDS = {**KEYWORDS, **TYPE_KEYWORDS}

# Reverse mapping from TokenType to string representation
TOKEN_TO_KEYWORD = {v: k for k, v in RESERVED_WORDS.items()}

def is_keyword(word: str) -> bool:
    """Check if a word is a PowerLang keyword"""
    return word in RESERVED_WORDS

def get_keyword_token_type(word: str) -> TokenType:
    """Get the TokenType for a keyword"""
    return RESERVED_WORDS.get(word, TokenType.IDENTIFIER)

def is_type_keyword(word: str) -> bool:
    """Check if a word is a type keyword"""
    return word in TYPE_KEYWORDS

def get_type_keyword_token_type(word: str) -> TokenType:
    """Get the TokenType for a type keyword"""
    return TYPE_KEYWORDS.get(word, TokenType.IDENTIFIER)
