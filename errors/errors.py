"""
Error classes and error handling for PowerLang
"""

from typing import Optional, Any, Dict, List
from dataclasses import dataclass, field
import traceback
import sys

@dataclass
class ErrorContext:
    """Context information for an error"""
    filename: str = "<input>"
    line: int = 1
    column: int = 1
    position: int = 0
    source_line: Optional[str] = None
    source_lines: List[str] = field(default_factory=list)
    function_name: Optional[str] = None
    module_name: Optional[str] = None
    stack_trace: List[Dict[str, Any]] = field(default_factory=list)

class PowerLangError(Exception):
    """Base class for all PowerLang errors"""
    
    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        super().__init__(message)
        self.message = message
        self.context = context or ErrorContext()
        self.inner_exception: Optional[Exception] = None
        
        # Capture stack trace
        self._capture_stack_trace()
    
    def _capture_stack_trace(self) -> None:
        """Capture Python stack trace"""
        try:
            tb = traceback.extract_stack()
            # Filter out frames from this file and error handling
            filtered_frames = []
            for frame in tb:
                if not frame.filename.endswith('errors.py'):
                    filtered_frames.append({
                        'filename': frame.filename,
                        'line': frame.lineno,
                        'function': frame.name,
                        'code': frame.line or ''
                    })
            self.context.stack_trace = filtered_frames
        except:
            pass
    
    def with_context(self, **kwargs) -> 'PowerLangError':
        """Add context information to the error"""
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)
        return self
    
    def with_inner_exception(self, exc: Exception) -> 'PowerLangError':
        """Set inner exception"""
        self.inner_exception = exc
        return self
    
    def __str__(self) -> str:
        base = f"{self.__class__.__name__}: {self.message}"
        
        if self.context.filename or self.context.line or self.context.column:
            location = f" at {self.context.filename}:{self.context.line}:{self.context.column}"
            base += location
        
        if self.inner_exception:
            base += f"\nCaused by: {self.inner_exception}"
        
        return base
    
    def detailed_string(self) -> str:
        """Get detailed error string with context"""
        lines = [str(self)]
        
        if self.context.source_line:
            lines.append(f"  {self.context.source_line}")
            if self.context.column > 0:
                lines.append(f"  {' ' * (self.context.column - 1)}^")
        
        if self.context.source_lines:
            lines.append("Context:")
            for i, source_line in enumerate(self.context.source_lines):
                lines.append(f"  {source_line}")
        
        if self.context.stack_trace:
            lines.append("Stack trace:")
            for frame in self.context.stack_trace[:5]:  # Show only first 5 frames
                lines.append(f"  at {frame['function']} in {frame['filename']}:{frame['line']}")
                if frame['code']:
                    lines.append(f"    {frame['code']}")
        
        if self.inner_exception:
            lines.append(f"\nInner exception: {self.inner_exception}")
            if hasattr(self.inner_exception, '__traceback__'):
                tb_lines = traceback.format_exception(
                    type(self.inner_exception),
                    self.inner_exception,
                    self.inner_exception.__traceback__
                )
                lines.extend(tb_lines)
        
        return '\n'.join(lines)

# Lexical analysis errors
class LexerError(PowerLangError):
    """Error during lexical analysis"""
    pass

class SyntaxError(PowerLangError):
    """Syntax error in source code"""
    pass

# Parsing errors
class ParseError(PowerLangError):
    """Error during parsing"""
    pass

# Semantic analysis errors
class SemanticError(PowerLangError):
    """Semantic error in source code"""
    pass

class TypeError(PowerLangError):
    """Type-related error"""
    pass

class NameError(PowerLangError):
    """Undefined name/variable error"""
    pass

class ArgumentError(PowerLangError):
    """Function argument error"""
    pass

# Runtime errors
class RuntimeError(PowerLangError):
    """General runtime error"""
    pass

class DivisionByZeroError(RuntimeError):
    """Division by zero error"""
    pass

class IndexError(RuntimeError):
    """Array index out of bounds error"""
    pass

class KeyError(RuntimeError):
    """Hashtable key not found error"""
    pass

class ImportError(RuntimeError):
    """Module import failed error"""
    pass

class TimeoutError(RuntimeError):
    """Operation timed out error"""
    pass

class ErrorHandler:
    """Handles error reporting and recovery"""
    
    def __init__(self, show_traceback: bool = False, abort_on_error: bool = False):
        self.show_traceback = show_traceback
        self.abort_on_error = abort_on_error
        self.error_count = 0
        self.warning_count = 0
        self.errors: List[PowerLangError] = []
        self.warnings: List[str] = []
        
    def reset(self) -> None:
        """Reset error counts and lists"""
        self.error_count = 0
        self.warning_count = 0
        self.errors.clear()
        self.warnings.clear()
    
    def error(self, error: PowerLangError) -> None:
        """Record an error"""
        self.error_count += 1
        self.errors.append(error)
        
        if self.show_traceback:
            print(error.detailed_string(), file=sys.stderr)
        else:
            print(str(error), file=sys.stderr)
        
        if self.abort_on_error:
            raise error
    
    def warning(self, message: str, context: Optional[ErrorContext] = None) -> None:
        """Record a warning"""
        self.warning_count += 1
        warning_msg = f"Warning: {message}"
        if context and (context.filename or context.line):
            warning_msg += f" at {context.filename}:{context.line}"
        
        self.warnings.append(warning_msg)
        print(warning_msg, file=sys.stderr)
    
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return self.error_count > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings"""
        return self.warning_count > 0
    
    def get_summary(self) -> str:
        """Get error/warning summary"""
        return f"Errors: {self.error_count}, Warnings: {self.warning_count}"
    
    def raise_if_errors(self) -> None:
        """Raise an exception if there are errors"""
        if self.has_errors():
            # Create a compound error if multiple errors
            if len(self.errors) == 1:
                raise self.errors[0]
            else:
                message = f"Multiple errors ({self.error_count})"
                compound_error = PowerLangError(message)
                # Attach all errors as inner exceptions
                for err in self.errors:
                    compound_error.with_inner_exception(err)
                raise compound_error

class ErrorReporter:
    """Reports errors in a formatted way"""
    
    @staticmethod
    def format_error(error: PowerLangError, show_context: bool = True) -> str:
        """Format an error for display"""
        if show_context:
            return error.detailed_string()
        return str(error)
    
    @staticmethod
    def format_lexer_error(error_info: dict) -> str:
        """Format a lexer error"""
        lines = []
        
        filename = error_info.get('filename', '<input>')
        line = error_info.get('line', 1)
        column = error_info.get('column', 1)
        message = error_info.get('message', 'Unknown error')
        
        lines.append(f"Lexer error at {filename}:{line}:{column}: {message}")
        
        context_lines = error_info.get('context_lines', [])
        if context_lines:
            for ctx_line, ctx_text in context_lines:
                lines.append(f"  {ctx_text}")
            
            pointer = error_info.get('pointer', '')
            if pointer:
                lines.append(f"  {pointer}")
        
        return '\n'.join(lines)
    
    @staticmethod
    def create_error_context_from_token(token, source: Optional[str] = None) -> ErrorContext:
        """Create error context from a token"""
        context = ErrorContext(
            filename=token.filename if hasattr(token, 'filename') else '<input>',
            line=token.line,
            column=token.column,
            position=token.position
        )
        
        if source:
            # Extract source line containing the token
            lines = source.split('\n')
            if 0 <= token.line - 1 < len(lines):
                context.source_line = lines[token.line - 1]
                
                # Get surrounding lines for context
                start = max(0, token.line - 3)
                end = min(len(lines), token.line + 2)
                context.source_lines = lines[start:end]
        
        return context
