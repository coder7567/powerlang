import sys
from powerlang.lexer.lexer import Lexer
from powerlang.parser.parser import Parser
from powerlang.interpreter.runtime import Runtime
from powerlang.interpreter.values import value_to_python, NULL

def main():
    if len(sys.argv) != 2:
        print("Usage: python -m powerlang <file.pow>")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        source = f.read()

    ast = Parser(Lexer(source)).parse()
    result = Runtime().run(ast)

    if result is not NULL:
        print(value_to_python(result))

if __name__ == "__main__":
    main()
