"""
Character scanner for PowerLang lexer
"""

from typing import Optional, List
from dataclasses import dataclass, field
import re

@dataclass
class SourcePosition:
    """Position in source code"""
    line: int = 1
    column: int = 1
    absolute: int = 0
    
    def clone(self) -> 'SourcePosition':
        """Create a copy of the position"""
        return SourcePosition(
            line=self.line,
            column=self.column,
            absolute=self.absolute
        )
    
    def advance(self, char: str = '\n') -> None:
        """Advance position based on character"""
        self.absolute += 1
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
    
    def __str__(self) -> str:
        return f"line {self.line}, column {self.column}"

@dataclass
class ScannerState:
    """State of the scanner for save/restore"""
    position: SourcePosition
    start_pos: SourcePosition
    in_string: bool = False
    string_delimiter: Optional[str] = None
    in_comment: bool = False
    in_block_comment: bool = False
    block_comment_depth: int = 0
    brace_depth: int = 0
    paren_depth: int = 0
    bracket_depth: int = 0
    
    def clone(self) -> 'ScannerState':
        """Create a deep copy of the scanner state"""
        return ScannerState(
            position=self.position.clone(),
            start_pos=self.start_pos.clone(),
            in_string=self.in_string,
            string_delimiter=self.string_delimiter,
            in_comment=self.in_comment,
            in_block_comment=self.in_block_comment,
            block_comment_depth=self.block_comment_depth,
            brace_depth=self.brace_depth,
            paren_depth=self.paren_depth,
            bracket_depth=self.bracket_depth
        )

class Scanner:
    """Character scanner for PowerLang source code"""
    
    def __init__(self, source: str, filename: str = "<input>"):
        self.source = source
        self.filename = filename
        self.source_length = len(source)
        
        # Current scanner state
        self._state = ScannerState(
            position=SourcePosition(),
            start_pos=SourcePosition()
        )
        
        # Save point for lookahead
        self._saved_state: Optional[ScannerState] = None
    
    @property
    def position(self) -> SourcePosition:
        """Current position in source"""
        return self._state.position.clone()
    
    @property
    def start_position(self) -> SourcePosition:
        """Start position of current lexeme"""
        return self._state.start_pos.clone()
    
    @property
    def is_at_end(self) -> bool:
        """Check if at end of source"""
        return self._state.position.absolute >= self.source_length
    
    @property
    def current_char(self) -> Optional[str]:
        """Get current character"""
        if self.is_at_end:
            return None
        return self.source[self._state.position.absolute]
    
    @property
    def next_char(self) -> Optional[str]:
        """Peek at next character without advancing"""
        pos = self._state.position.absolute + 1
        if pos >= self.source_length:
            return None
        return self.source[pos]
    
    def peek(self, offset: int = 0) -> Optional[str]:
        """Peek ahead by offset characters"""
        pos = self._state.position.absolute + offset
        if pos < 0 or pos >= self.source_length:
            return None
        return self.source[pos]
    
    def peek_string(self, length: int) -> str:
        """Peek ahead a string of specified length"""
        pos = self._state.position.absolute
        end = min(pos + length, self.source_length)
        return self.source[pos:end]
    
    def match(self, expected: str) -> bool:
        """Check if current character matches expected, consume if true"""
        if self.is_at_end:
            return False
        
        if self.current_char == expected:
            self.advance()
            return True
        return False
    
    def match_any(self, chars: str) -> bool:
        """Check if current character matches any in chars, consume if true"""
        if self.is_at_end:
            return False
        
        if self.current_char in chars:
            self.advance()
            return True
        return False
    
    def advance(self) -> Optional[str]:
        """Advance to next character and return the character moved past"""
        if self.is_at_end:
            return None
        
        char = self.current_char
        self._state.position.advance(char)
        return char
    
    def advance_if(self, condition: bool) -> Optional[str]:
        """Advance only if condition is true"""
        if condition and not self.is_at_end:
            return self.advance()
        return None
    
    def skip_whitespace(self) -> None:
        """Skip whitespace characters"""
        while not self.is_at_end and self.current_char.isspace():
            self.advance()
    
    def skip_line_comment(self) -> None:
        """Skip a line comment"""
        while not self.is_at_end and self.current_char != '\n':
            self.advance()
    
    def is_newline(self) -> bool:
        """Check if current character is a newline"""
        if self.is_at_end:
            return False
        return self.current_char == '\n'
    
    def is_whitespace(self) -> bool:
        """Check if current character is whitespace"""
        if self.is_at_end:
            return False
        return self.current_char.isspace()
    
    def is_digit(self) -> bool:
        """Check if current character is a digit"""
        if self.is_at_end:
            return False
        return self.current_char.isdigit()
    
    def is_hex_digit(self) -> bool:
        """Check if current character is a hex digit"""
        if self.is_at_end:
            return False
        char = self.current_char.lower()
        return char.isdigit() or char in 'abcdef'
    
    def is_binary_digit(self) -> bool:
        """Check if current character is a binary digit"""
        if self.is_at_end:
            return False
        return self.current_char in '01'
    
    def is_letter(self) -> bool:
        """Check if current character is a letter"""
        if self.is_at_end:
            return False
        return self.current_char.isalpha() or self.current_char == '_'
    
    def is_letter_or_digit(self) -> bool:
        """Check if current character is a letter or digit"""
        if self.is_at_end:
            return False
        return self.current_char.isalnum() or self.current_char == '_'
    
    def is_identifier_start(self) -> bool:
        """Check if current character can start an identifier"""
        if self.is_at_end:
            return False
        return self.is_letter()
    
    def is_identifier_part(self) -> bool:
        """Check if current character can be part of an identifier"""
        if self.is_at_end:
            return False
        return self.is_letter_or_digit()
    
    def start_lexeme(self) -> None:
        """Mark start of a new lexeme"""
        self._state.start_pos = self._state.position.clone()
    
    def get_lexeme(self) -> str:
        """Get the current lexeme from start to current position"""
        start = self._state.start_pos.absolute
        end = self._state.position.absolute
        return self.source[start:end]
    
    def get_lexeme_length(self) -> int:
        """Get length of current lexeme"""
        return self._state.position.absolute - self._state.start_pos.absolute
    
    def save_state(self) -> None:
        """Save current scanner state for lookahead"""
        self._saved_state = self._state.clone()
    
    def restore_state(self) -> None:
        """Restore scanner state from saved state"""
        if self._saved_state is not None:
            self._state = self._saved_state
        self._saved_state = None
    
    def discard_saved_state(self) -> None:
        """Discard saved state without restoring"""
        self._saved_state = None
    
    def enter_string(self, delimiter: str) -> None:
        """Enter string mode"""
        self._state.in_string = True
        self._state.string_delimiter = delimiter
    
    def exit_string(self) -> None:
        """Exit string mode"""
        self._state.in_string = False
        self._state.string_delimiter = None
    
    def enter_comment(self) -> None:
        """Enter single-line comment mode"""
        self._state.in_comment = True
    
    def exit_comment(self) -> None:
        """Exit comment mode"""
        self._state.in_comment = False
    
    def enter_block_comment(self) -> None:
        """Enter block comment mode"""
        self._state.in_block_comment = True
        self._state.block_comment_depth += 1
    
    def exit_block_comment(self) -> None:
        """Exit block comment mode (one level)"""
        self._state.block_comment_depth -= 1
        if self._state.block_comment_depth == 0:
            self._state.in_block_comment = False
    
    def is_in_block_comment(self) -> bool:
        """Check if inside block comment"""
        return self._state.in_block_comment
    
    def is_in_comment(self) -> bool:
        """Check if inside any comment"""
        return self._state.in_comment or self._state.in_block_comment
    
    def is_in_string(self) -> bool:
        """Check if inside string"""
        return self._state.in_string
    
    def get_string_delimiter(self) -> Optional[str]:
        """Get current string delimiter"""
        return self._state.string_delimiter
    
    def enter_brace(self) -> None:
        """Enter a brace level"""
        self._state.brace_depth += 1
    
    def exit_brace(self) -> None:
        """Exit a brace level"""
        if self._state.brace_depth > 0:
            self._state.brace_depth -= 1
    
    def enter_paren(self) -> None:
        """Enter a parenthesis level"""
        self._state.paren_depth += 1
    
    def exit_paren(self) -> None:
        """Exit a parenthesis level"""
        if self._state.paren_depth > 0:
            self._state.paren_depth -= 1
    
    def enter_bracket(self) -> None:
        """Enter a bracket level"""
        self._state.bracket_depth += 1
    
    def exit_bracket(self) -> None:
        """Exit a bracket level"""
        if self._state.bracket_depth > 0:
            self._state.bracket_depth -= 1
    
    def get_brace_depth(self) -> int:
        """Get current brace nesting depth"""
        return self._state.brace_depth
    
    def get_paren_depth(self) -> int:
        """Get current parenthesis nesting depth"""
        return self._state.paren_depth
    
    def get_bracket_depth(self) -> int:
        """Get current bracket nesting depth"""
        return self._state.bracket_depth
    
    def create_error_context(self, length: int = 20) -> dict:
        """Create error context information"""
        pos = self._state.position.absolute
        line_start = self.source.rfind('\n', 0, pos) + 1
        line_end = self.source.find('\n', pos)
        if line_end == -1:
            line_end = self.source_length
        
        line = self.source[line_start:line_end]
        column = pos - line_start + 1
        
        # Create pointer to error position
        pointer = ' ' * (column - 1) + '^'
        
        # Get surrounding lines for context
        lines = []
        current_line = self._state.position.line
        
        # Get previous line
        prev_line_start = self.source.rfind('\n', 0, line_start - 1)
        if prev_line_start != -1:
            prev_line_end = line_start - 1
            prev_line = self.source[prev_line_start + 1:prev_line_end]
            lines.append((current_line - 1, prev_line))
        
        # Current line
        lines.append((current_line, line))
        
        # Next line
        next_line_end = self.source.find('\n', line_end + 1)
        if next_line_end != -1:
            next_line_start = line_end + 1
            next_line = self.source[next_line_start:next_line_end]
            lines.append((current_line + 1, next_line))
        
        return {
            'filename': self.filename,
            'line': current_line,
            'column': column,
            'context_lines': lines,
            'pointer': pointer,
            'position': self._state.position
         }
