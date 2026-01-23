"""
Main lexer implementation for PowerLang
"""

import re
from typing import List, Optional, Iterator
from .tokens import Token, TokenType
from .scanner import Scanner
from .keywords import is_keyword, get_keyword_token_type, is_type_keyword
from .operators import (
    SINGLE_CHAR_OPERATORS, MULTI_CHAR_OPERATORS, 
    get_operator_token_type, is_operator_char, is_operator_start
)

class Lexer:
    """PowerLang lexical analyzer"""
    
    # Regular expressions for pattern matching
    HEX_PATTERN = re.compile(r'^0[xX][0-9a-fA-F]+$')
    BINARY_PATTERN = re.compile(r'^0[bB][01]+$')
    INTEGER_PATTERN = re.compile(r'^\d+$')
    FLOAT_PATTERN = re.compile(r'^\d+\.\d+([eE][+-]?\d+)?$')
    IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
    
    def __init__(self, source: str, filename: str = "<input>"):
        self.scanner = Scanner(source, filename)
        self.tokens: List[Token] = []
        self.had_error = False
        self.errors: List[dict] = []
        
        # State flags
        self._in_type_context = False  # True when parsing [type] annotations
    
    def tokenize(self) -> List[Token]:
        """Tokenize the entire source code"""
        self.tokens.clear()
        self.had_error = False
        self.errors.clear()
        
        while not self.scanner.is_at_end:
            self.scanner.start_lexeme()
            token = self._scan_token()
            if token is not None:
                self.tokens.append(token)
        
        # Add EOF token
        self.tokens.append(Token(
            type=TokenType.EOF,
            lexeme="",
            literal=None,
            line=self.scanner.position.line,
            column=self.scanner.position.column,
            position=self.scanner.position.absolute
        ))
        
        return self.tokens
    
    def _scan_token(self) -> Optional[Token]:
        """Scan a single token"""
        # Skip whitespace and comments
        self._skip_whitespace_and_comments()
        if self.scanner.is_at_end:
            return None
        
        # Handle different token types based on first character
        char = self.scanner.current_char
        
        if char == '$':
            return self._scan_variable()
        elif char == '"' or char == "'":
            return self._scan_string()
        elif char == '`':
            return self._scan_escape_string()
        elif char == '#' and self.scanner.peek() == '#':
            return self._scan_comment()
        elif char == '<' and self.scanner.peek() == '#':
            return self._scan_block_comment_start()
        elif char == '#':
            return self._scan_single_line_comment()
        elif char.isdigit():
            return self._scan_number()
        elif self._is_identifier_start(char):
            return self._scan_identifier_or_keyword()
        elif is_operator_start(char):
            return self._scan_operator()
        elif char == '[':
            # Enter type context for [type] annotations
            token = self._scan_single_char_token()
            if token.type == TokenType.LBRACKET:
                self._in_type_context = True
            return token
        elif char == ']':
            # Exit type context
            token = self._scan_single_char_token()
            if token.type == TokenType.RBRACKET:
                self._in_type_context = False
            return token
        else:
            return self._scan_single_char_token()
    
    def _skip_whitespace_and_comments(self) -> None:
        """Skip whitespace and comments"""
        while not self.scanner.is_at_end:
            if self.scanner.is_whitespace():
                self.scanner.advance()
            elif self.scanner.current_char == '#' and self.scanner.peek() == '#':
                # Single line comment: ## comment
                self.scanner.advance()  # Skip #
                self.scanner.advance()  # Skip #
                self.scanner.skip_line_comment()
            elif self.scanner.current_char == '<' and self.scanner.peek() == '#':
                # Start of block comment, handled in _scan_token
                break
            elif self.scanner.is_in_comment() or self.scanner.is_in_block_comment():
                # We're already in a comment, skip appropriately
                if self.scanner.is_in_comment():
                    self.scanner.skip_line_comment()
                else:
                    # In block comment, need to look for #>
                    while not self.scanner.is_at_end:
                        if (self.scanner.current_char == '#' and 
                            self.scanner.peek() == '>'):
                            self.scanner.advance()  # Skip #
                            self.scanner.advance()  # Skip >
                            self.scanner.exit_block_comment()
                            break
                        self.scanner.advance()
            else:
                break
    
    def _scan_variable(self) -> Token:
        """Scan a variable starting with $"""
        # Skip $
        self.scanner.advance()
        
        # Check for special variable forms
        if self.scanner.current_char == '{':
            # ${variable} form
            self.scanner.advance()
            lexeme = self.scanner.get_lexeme()
            return self._create_token(TokenType.DOLLAR_LBRACE, lexeme, None)
        
        # Regular variable: $name or $name123
        while (not self.scanner.is_at_end and 
               self.scanner.is_letter_or_digit()):
            self.scanner.advance()
        
        lexeme = self.scanner.get_lexeme()
        return self._create_token(TokenType.DOLLAR, lexeme, lexeme)
    
    def _scan_string(self) -> Token:
        """Scan a string literal"""
        delimiter = self.scanner.current_char
        self.scanner.enter_string(delimiter)
        self.scanner.advance()  # Skip opening quote
        
        value_chars = []
        while (not self.scanner.is_at_end and 
               not (self.scanner.current_char == delimiter and 
                    not self.scanner.is_escaped())):
            
            if self.scanner.current_char == '\\':
                # Handle escape sequences
                self.scanner.advance()
                if self.scanner.is_at_end:
                    break
                
                escaped = self._escape_char(self.scanner.current_char)
                if escaped is not None:
                    value_chars.append(escaped)
                else:
                    value_chars.append('\\' + self.scanner.current_char)
            elif (self.scanner.current_char == '$' and 
                  self.scanner.peek() == '{'):
                # String interpolation: ${expression}
                value_chars.append(self.scanner.current_char)
                value_chars.append(self.scanner.peek())
            else:
                value_chars.append(self.scanner.current_char)
            
            self.scanner.advance()
        
        if self.scanner.is_at_end:
            self._error("Unterminated string")
            self.scanner.exit_string()
            lexeme = self.scanner.get_lexeme()
            return self._create_token(TokenType.STRING, lexeme, ''.join(value_chars))
        
        # Skip closing quote
        self.scanner.advance()
        self.scanner.exit_string()
        
        lexeme = self.scanner.get_lexeme()
        value = ''.join(value_chars)
        return self._create_token(TokenType.STRING, lexeme, value)
    
    def _scan_escape_string(self) -> Token:
        """Scan an escape string (backtick quoted)"""
        # Skip opening backtick
        self.scanner.advance()
        
        value_chars = []
        while not self.scanner.is_at_end and self.scanner.current_char != '`':
            value_chars.append(self.scanner.current_char)
            self.scanner.advance()
        
        if self.scanner.is_at_end:
            self._error("Unterminated escape string")
            lexeme = self.scanner.get_lexeme()
            return self._create_token(TokenType.STRING, lexeme, ''.join(value_chars))
        
        # Skip closing backtick
        self.scanner.advance()
        
        lexeme = self.scanner.get_lexeme()
        value = ''.join(value_chars)
        return self._create_token(TokenType.STRING, lexeme, value)
    
    def _scan_comment(self) -> Token:
        """Scan a single line comment starting with ##"""
        # Skip both # characters
        self.scanner.advance()
        self.scanner.advance()
        
        # Save start for lexeme
        self.scanner.start_lexeme()
        
        # Skip to end of line
        while not self.scanner.is_at_end and self.scanner.current_char != '\n':
            self.scanner.advance()
        
        lexeme = self.scanner.get_lexeme()
        return self._create_token(TokenType.COMMENT, lexeme, lexeme.strip())
    
    def _scan_single_line_comment(self) -> Token:
        """Scan PowerShell-style single line comment starting with #"""
        # Skip #
        self.scanner.advance()
        
        # Save start for lexeme
        self.scanner.start_lexeme()
        
        # Skip to end of line
        while not self.scanner.is_at_end and self.scanner.current_char != '\n':
            self.scanner.advance()
        
        lexeme = self.scanner.get_lexeme()
        return self._create_token(TokenType.COMMENT, lexeme, lexeme.strip())
    
    def _scan_block_comment_start(self) -> Token:
        """Scan start of block comment <#"""
        # Skip < and #
        self.scanner.advance()
        self.scanner.advance()
        
        lexeme = self.scanner.get_lexeme()
        token = self._create_token(TokenType.BLOCK_COMMENT_START, lexeme, None)
        
        # Enter block comment mode
        self.scanner.enter_block_comment()
        
        # Skip to end of block comment
        while not self.scanner.is_at_end:
            if self.scanner.current_char == '#' and self.scanner.peek() == '>':
                self.scanner.advance()  # Skip #
                self.scanner.advance()  # Skip >
                self.scanner.exit_block_comment()
                # Create block comment end token
                self.scanner.start_lexeme()
                lexeme = self.scanner.get_lexeme()
                self.tokens.append(
                    self._create_token(TokenType.BLOCK_COMMENT_END, lexeme, None)
                )
                break
            self.scanner.advance()
        
        return token
    
    def _scan_number(self) -> Token:
        """Scan a numeric literal"""
        # Check for hex or binary prefix
        if (self.scanner.current_char == '0' and 
            not self.scanner.is_at_end and
            self.scanner.peek() in 'xXbB'):
            prefix = self.scanner.peek()
            self.scanner.advance()  # Skip 0
            self.scanner.advance()  # Skip x/X/b/B
            
            if prefix.lower() == 'x':
                return self._scan_hex_number()
            else:
                return self._scan_binary_number()
        
        # Decimal number (integer or float)
        while self.scanner.is_digit():
            self.scanner.advance()
        
        # Check for decimal point
        if (self.scanner.current_char == '.' and 
            self.scanner.peek() is not None and 
            self.scanner.peek().isdigit()):
            self.scanner.advance()  # Skip .
            
            while self.scanner.is_digit():
                self.scanner.advance()
            
            # Check for exponent
            if self.scanner.current_char.lower() == 'e':
                self.scanner.advance()  # Skip e/E
                
                # Optional + or -
                if self.scanner.current_char in '+-':
                    self.scanner.advance()
                
                # Must have at least one digit
                if not self.scanner.is_digit():
                    self._error("Invalid floating point exponent")
                
                while self.scanner.is_digit():
                    self.scanner.advance()
            
            lexeme = self.scanner.get_lexeme()
            try:
                value = float(lexeme)
                return self._create_token(TokenType.DOUBLE, lexeme, value)
            except ValueError:
                self._error(f"Invalid floating point number: {lexeme}")
                return self._create_token(TokenType.DOUBLE, lexeme, 0.0)
        else:
            # Integer
            lexeme = self.scanner.get_lexeme()
            try:
                value = int(lexeme)
                return self._create_token(TokenType.INTEGER, lexeme, value)
            except ValueError:
                self._error(f"Invalid integer: {lexeme}")
                return self._create_token(TokenType.INTEGER, lexeme, 0)
    
    def _scan_hex_number(self) -> Token:
        """Scan a hexadecimal number"""
        while self.scanner.is_hex_digit():
            self.scanner.advance()
        
        lexeme = self.scanner.get_lexeme()
        # Remove 0x prefix from lexeme for parsing
        hex_str = lexeme[2:] if lexeme.lower().startswith('0x') else lexeme
        
        if not hex_str:
            self._error("Invalid hexadecimal number")
            return self._create_token(TokenType.INTEGER, lexeme, 0)
        
        try:
            value = int(hex_str, 16)
            return self._create_token(TokenType.INTEGER, lexeme, value)
        except ValueError:
            self._error(f"Invalid hexadecimal number: {lexeme}")
            return self._create_token(TokenType.INTEGER, lexeme, 0)
    
    def _scan_binary_number(self) -> Token:
        """Scan a binary number"""
        while self.scanner.is_binary_digit():
            self.scanner.advance()
        
        lexeme = self.scanner.get_lexeme()
        # Remove 0b prefix from lexeme for parsing
        bin_str = lexeme[2:] if lexeme.lower().startswith('0b') else lexeme
        
        if not bin_str:
            self._error("Invalid binary number")
            return self._create_token(TokenType.INTEGER, lexeme, 0)
        
        try:
            value = int(bin_str, 2)
            return self._create_token(TokenType.INTEGER, lexeme, value)
        except ValueError:
            self._error(f"Invalid binary number: {lexeme}")
            return self._create_token(TokenType.INTEGER, lexeme, 0)
    
    def _scan_identifier_or_keyword(self) -> Token:
        """Scan an identifier or keyword"""
        while self.scanner.is_identifier_part():
            self.scanner.advance()
        
        lexeme = self.scanner.get_lexeme()
        
        # Check if it's a keyword
        if is_keyword(lexeme):
            token_type = get_keyword_token_type(lexeme)
            
            # Special handling for true/false
            if token_type == TokenType.TRUE:
                return self._create_token(token_type, lexeme, True)
            elif token_type == TokenType.FALSE:
                return self._create_token(token_type, lexeme, False)
            elif token_type == TokenType.NULL:
                return self._create_token(token_type, lexeme, None)
            else:
                return self._create_token(token_type, lexeme, None)
        
        # Check if we're in type context (inside [ ])
        if self._in_type_context and is_type_keyword(lexeme):
            token_type = get_keyword_token_type(lexeme)
            return self._create_token(token_type, lexeme, None)
        
        # Regular identifier
        return self._create_token(TokenType.IDENTIFIER, lexeme, lexeme)
    
    def _scan_operator(self) -> Token:
        """Scan an operator"""
        # Try to match multi-character operators first
        for length in range(4, 0, -1):  # Try 4, 3, 2, 1 char operators
            if length == 1:
                # Single character operator
                char = self.scanner.current_char
                if char in SINGLE_CHAR_OPERATORS:
                    self.scanner.advance()
                    token_type = SINGLE_CHAR_OPERATORS[char]
                    lexeme = self.scanner.get_lexeme()
                    return self._create_token(token_type, lexeme, None)
            else:
                # Multi-character operator
                op_str = self.scanner.peek_string(length)
                if op_str in MULTI_CHAR_OPERATORS:
                    for _ in range(length):
                        self.scanner.advance()
                    token_type = MULTI_CHAR_OPERATORS[op_str]
                    lexeme = self.scanner.get_lexeme()
                    return self._create_token(token_type, lexeme, None)
        
        # No operator matched, scan as single character
        char = self.scanner.current_char
        self.scanner.advance()
        lexeme = self.scanner.get_lexeme()
        self._error(f"Unexpected character: {char}")
        return self._create_token(TokenType.IDENTIFIER, lexeme, lexeme)
    
    def _scan_single_char_token(self) -> Token:
        """Scan a single character token"""
        char = self.scanner.current_char
        
        # Map character to token type
        token_type = SINGLE_CHAR_OPERATORS.get(char, TokenType.IDENTIFIER)
        
        self.scanner.advance()
        lexeme = self.scanner.get_lexeme()
        
        # Update nesting depths
        if token_type == TokenType.LBRACE:
            self.scanner.enter_brace()
        elif token_type == TokenType.RBRACE:
            self.scanner.exit_brace()
        elif token_type == TokenType.LPAREN:
            self.scanner.enter_paren()
        elif token_type == TokenType.RPAREN:
            self.scanner.exit_paren()
        elif token_type == TokenType.LBRACKET:
            self.scanner.enter_bracket()
        elif token_type == TokenType.RBRACKET:
            self.scanner.exit_bracket()
        
        return self._create_token(token_type, lexeme, None)
    
    def _escape_char(self, char: str) -> Optional[str]:
        """Convert escape sequence to character"""
        escape_map = {
            'n': '\n',
            'r': '\r',
            't': '\t',
            'b': '\b',
            'f': '\f',
            'v': '\v',
            '\\': '\\',
            '"': '"',
            "'": "'",
            '`': '`',
            '$': '$',
            '0': '\0',
        }
        return escape_map.get(char)
    
    def _is_identifier_start(self, char: str) -> bool:
        """Check if character can start an identifier"""
        return char.isalpha() or char == '_'
    
    def _create_token(self, token_type: TokenType, lexeme: str, literal) -> Token:
        """Create a token with current scanner positions"""
        return Token(
            type=token_type,
            lexeme=lexeme,
            literal=literal,
            line=self.scanner.start_position.line,
            column=self.scanner.start_position.column,
            position=self.scanner.start_position.absolute
        )
    
    def _error(self, message: str) -> None:
        """Record a lexer error"""
        self.had_error = True
        context = self.scanner.create_error_context()
        
        error_info = {
            'type': 'lexer',
            'message': message,
            **context
        }
        
        self.errors.append(error_info)
        
        # Print error for debugging
        print(f"Lexer error at {context['filename']}:{context['line']}:{context['column']}: {message}")
        print(f"  {context['context_lines'][0][1] if context['context_lines'] else ''}")
        print(f"  {context['pointer']}")
    
    def get_tokens(self) -> List[Token]:
        """Get all tokens"""
        return self.tokens.copy()
    
    def get_errors(self) -> List[dict]:
        """Get all lexer errors"""
        return self.errors.copy()
    
    def token_iter(self) -> Iterator[Token]:
        """Iterate over tokens"""
        return iter(self.tokens)
