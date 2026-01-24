from powerlang.lexer.lexer import Lexer
from powerlang.parser.parser import Parser

source = """
function Add-Numbers([int]$a, [int]$b) {
    return $a + $b
}
"""

lexer = Lexer(source)
ast = Parser(lexer).parse()

print(ast.pretty())
