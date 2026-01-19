from powerlang.lexer.tokens import Token, TokenType, KEYWORDS


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.length = len(source)
        self.position = 0
        self.line = 1
        self.column = 1

    # =========================
    # Core helpers
    # =========================

    def current_char(self):
        if self.position >= self.length:
            return None
        return self.source[self.position]

    def peek(self, offset=1):
        pos = self.position + offset
        if pos >= self.length:
            return None
        return self.source[pos]

    def advance(self):
        char = self.current_char()
        self.position += 1

        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        return char

    def make_token(self, token_type, value=None, line=None, column=None):
        return Token(
            token_type,
            value,
            line if line is not None else self.line,
            column if column is not None else self.column,
        )

    # =========================
    # Main entry
    # =========================

    def tokenize(self):
        tokens = []

        while self.current_char() is not None:
            char = self.current_char()

            # -------- Whitespace --------
            if char in " \t\r":
                self.advance()
                continue

            if char == "\n":
                tokens.append(self.make_token(TokenType.NEWLINE, "\n"))
                self.advance()
                continue

            # -------- Comments --------
            if char == "#":
                if self.peek() == ">":  # should never happen alone, defensive
                    self.advance()
                elif self.peek() == "<":  # malformed
                    self.advance()
                else:
                    self.skip_single_line_comment()
                continue

            if char == "<" and self.peek() == "#":
                self.skip_block_comment()
                continue

            # -------- Variables --------
            if char == "$":
                line, col = self.line, self.column
                self.advance()
                tokens.append(Token(TokenType.DOLLAR, "$", line, col))
                continue

            # -------- Identifiers / Keywords --------
            if char.isalpha() or char == "_":
                tokens.append(self.read_identifier())
                continue

            # -------- Numbers --------
            if char.isdigit():
                tokens.append(self.read_number())
                continue

            # -------- Strings --------
            if char == '"':
                tokens.append(self.read_string())
                continue

            # -------- Operators & Symbols --------
            token = self.read_operator_or_symbol()
            if token:
                tokens.append(token)
                continue

            raise SyntaxError(
                f"Unexpected character '{char}' at {self.line}:{self.column}"
            )

        tokens.append(self.make_token(TokenType.EOF))
        return tokens

    # =========================
    # Readers
    # =========================

    def read_identifier(self):
        start_line = self.line
        start_col = self.column
        value = ""

        while self.current_char() and (
            self.current_char().isalnum() or self.current_char() == "_"
        ):
            value += self.advance()

        lower = value.lower()
        if lower in KEYWORDS:
            return Token(KEYWORDS[lower], value, start_line, start_col)

        return Token(TokenType.IDENTIFIER, value, start_line, start_col)

    def read_number(self):
        start_line = self.line
        start_col = self.column
        value = ""
        has_dot = False

        while self.current_char() and (
            self.current_char().isdigit() or self.current_char() == "."
        ):
            if self.current_char() == ".":
                if has_dot:
                    break
                has_dot = True
            value += self.advance()

        if "." in value:
            return Token(TokenType.NUMBER, float(value), start_line, start_col)
        return Token(TokenType.NUMBER, int(value), start_line, start_col)

    def read_string(self):
        start_line = self.line
        start_col = self.column
        self.advance()  # skip opening quote
        value = ""

        while self.current_char() is not None and self.current_char() != '"':
            if self.current_char() == "\\":
                self.advance()
                esc = self.advance()
                value += {
                    "n": "\n",
                    "t": "\t",
                    '"': '"',
                    "\\": "\\",
                }.get(esc, esc)
            else:
                value += self.advance()

        if self.current_char() != '"':
            raise SyntaxError(
                f"Unterminated string at {start_line}:{start_col}"
            )

        self.advance()  # closing quote
        return Token(TokenType.STRING, value, start_line, start_col)

    # =========================
    # Operators & symbols
    # =========================

    def read_operator_or_symbol(self):
        char = self.current_char()
        line, col = self.line, self.column

        # --- Two-character operators ---
        if char == "+" and self.peek() == "+":
            self.advance(); self.advance()
            return Token(TokenType.INCREMENT, "++", line, col)

        if char == "-" and self.peek() == "-":
            self.advance(); self.advance()
            return Token(TokenType.DECREMENT, "--", line, col)

        if char == "+" and self.peek() == "=":
            self.advance(); self.advance()
            return Token(TokenType.PLUS_ASSIGN, "+=", line, col)

        if char == "-" and self.peek() == "=":
            self.advance(); self.advance()
            return Token(TokenType.MINUS_ASSIGN, "-=", line, col)

        if char == "*" and self.peek() == "=":
            self.advance(); self.advance()
            return Token(TokenType.MULT_ASSIGN, "*=", line, col)

        if char == "/" and self.peek() == "=":
            self.advance(); self.advance()
            return Token(TokenType.DIV_ASSIGN, "/=", line, col)

        # --- PowerShell-style operators ---
        if char == "-" and self.peek() and self.peek().isalpha():
            return self.read_ps_operator()

        # --- Single-character symbols ---
        single = {
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.MULTIPLY,
            "/": TokenType.DIVIDE,
            "%": TokenType.MODULO,
            "=": TokenType.ASSIGN,
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            "{": TokenType.LBRACE,
            "}": TokenType.RBRACE,
            "[": TokenType.LBRACKET,
            "]": TokenType.RBRACKET,
            ",": TokenType.COMMA,
            ".": TokenType.DOT,
            ":": TokenType.COLON,
            ";": TokenType.SEMICOLON,
        }

        if char in single:
            self.advance()
            return Token(single[char], char, line, col)

        return None

    def read_ps_operator(self):
        start_line = self.line
        start_col = self.column
        value = self.advance()  # '-'

        while self.current_char() and self.current_char().isalpha():
            value += self.advance()

        mapping = {
            "-eq": TokenType.EQ,
            "-ne": TokenType.NE,
            "-gt": TokenType.GT,
            "-lt": TokenType.LT,
            "-ge": TokenType.GE,
            "-le": TokenType.LE,
            "-and": TokenType.AND,
            "-or": TokenType.OR,
            "-not": TokenType.NOT,
        }

        if value.lower() in mapping:
            return Token(mapping[value.lower()], value, start_line, start_col)

        raise SyntaxError(
            f"Unknown operator '{value}' at {start_line}:{start_col}"
        )

    # =========================
    # Comment skipping
    # =========================

    def skip_single_line_comment(self):
        while self.current_char() and self.current_char() != "\n":
            self.advance()

    def skip_block_comment(self):
        self.advance()  # <
        self.advance()  # #

        while self.current_char() is not None:
            if self.current_char() == "#" and self.peek() == ">":
                self.advance()
                self.advance()
                return
            self.advance()

        raise SyntaxError("Unterminated block comment")
