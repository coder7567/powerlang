from powerlang.lexer.lexer import Lexer

source = """
class Test {
    function Method() {
        [int]$x = 42; # This is a comment
        if ($x -gt 10) {
            return $x + 1;
        }
    }
}
"""

lexer = Lexer(source)
tokens = lexer.tokenize()

for t in tokens:
    print(f"Type: {t.type.name}, Lexeme: '{t.lexeme}', Literal: {t.literal}")
