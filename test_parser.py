from powerlang.lexer.lexer import Lexer
from powerlang.parser.parser import Parser


source = """
function AddNumbers([int]$a, [int]$b) {
    return $a + $b;
}
"""

lexer = Lexer(source)
ast = Parser(lexer).parse()

print(ast.pretty())
