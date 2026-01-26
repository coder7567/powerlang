"""
Tests for the PowerLang interpreter.

Run with: python -m pytest powerlang/test_interpreter.py -v
Or:       python powerlang/test_interpreter.py
"""

import sys

# Ensure powerlang is on path when run as script
if __name__ == "__main__":
    sys.path.insert(0, ".")

from powerlang.lexer import Lexer
from powerlang.parser import Parser
from powerlang.parser.ast import (
    ArrayLiteral,
    Assignment,
    BinaryOperation,
    Block,
    CallExpression,
    ExpressionStatement,
    FunctionDeclaration,
    HashLiteral,
    HashPair,
    IndexAccess,
    Literal,
    Parameter,
    Program,
    ReturnStatement,
    TernaryExpression,
    Variable,
)
from powerlang.lexer.tokens import Token, TokenType
from powerlang.interpreter import Runtime, value_to_python
from powerlang.interpreter.values import NULL


def run_source(source: str):
    """Lex, parse, and run PowerLang source. Returns last expression value."""
    ast = Parser(Lexer(source)).parse()
    return Runtime().run(ast)


def run_ast(program: Program):
    """Run a Program AST directly."""
    return Runtime().run(program)


def tok(tt: TokenType, lexeme: str, literal=None, line=1, col=1):
    return Token(tt, lexeme, literal, line, col, 0)


def lit(v, line=1, col=1):
    """Create a Literal for common types."""
    if isinstance(v, bool):
        t = tok(TokenType.BOOL, "true" if v else "false", v, line, col)
    elif isinstance(v, int):
        t = tok(TokenType.INTEGER, str(v), v, line, col)
    elif isinstance(v, float):
        t = tok(TokenType.FLOAT, str(v), v, line, col)
    elif isinstance(v, str):
        t = tok(TokenType.STRING, repr(v), v, line, col)
    else:
        t = tok(TokenType.NULL, "null", None, line, col)
    return Literal(token=t, value=v, line=line, column=col)


def var(name: str, line=1, col=1):
    """Create a Variable. Name can be 'x' or '$x'."""
    if not name.startswith("$"):
        name = "$" + name
    t = tok(TokenType.VARIABLE, name, name[1:].lower(), line, col)
    return Variable(name_token=t, line=line, column=col)


# ---------------------------------------------------------------------------
# Tests using parsed source (parser-friendly syntax)
# ---------------------------------------------------------------------------


def test_literals():
    """Literals (parser-accepted syntax)."""
    assert value_to_python(run_source("1;")) == 1
    assert value_to_python(run_source("0;")) == 0


def test_arithmetic():
    """Arithmetic via parsed source."""
    assert value_to_python(run_source("1 + 2;")) == 3
    assert value_to_python(run_source("10 - 3;")) == 7
    assert value_to_python(run_source("2 * 5;")) == 10
    assert value_to_python(run_source("12 / 4;")) == 3.0
    assert value_to_python(run_source("17 % 5;")) == 2
    assert value_to_python(run_source("1 + 2 * 3;")) == 7


def test_comparison_and_logic():
    """Comparison and logic (parser-accepted)."""
    assert value_to_python(run_source("1 -eq 1;")) is True
    assert value_to_python(run_source("1 -eq 2;")) is False
    assert value_to_python(run_source("1 -ne 2;")) is True
    assert value_to_python(run_source("3 -gt 2;")) is True
    assert value_to_python(run_source("1 -lt 2;")) is True


def test_blocks():
    assert value_to_python(run_source("{ 1; 2; 3; }")) == 3
    assert value_to_python(run_source("{ { 10; } }")) == 10


def test_if_else():
    """If/else via parsed source (condition in parens, no trailing ';' after else block)."""
    assert value_to_python(run_source("if (1) { 1; } else { 2; }")) == 1
    assert value_to_python(run_source("if (0) { 1; } else { 2; }")) == 2


def test_while():
    assert value_to_python(run_source("while (0) { 1; }")) is None


def test_ternary():
    """Ternary via AST (parser may not accept ? : in all setups)."""
    t = TernaryExpression(condition=lit(1), then_expr=lit(1), else_expr=lit(2), line=L, column=C)
    prog = Program(statements=[_stmt(t)], line=L, column=C)
    assert value_to_python(run_ast(prog)) == 1
    t2 = TernaryExpression(condition=lit(0), then_expr=lit(1), else_expr=lit(2), line=L, column=C)
    prog2 = Program(statements=[_stmt(t2)], line=L, column=C)
    assert value_to_python(run_ast(prog2)) == 2


# ---------------------------------------------------------------------------
# Tests using direct AST (full interpreter coverage)
# ---------------------------------------------------------------------------


L, C = 1, 1


def _stmt(expr, line=L, col=C):
    return ExpressionStatement(expression=expr, line=line, column=col)


def test_variables_and_assignment():
    var_a, var_b = var("a"), var("b")
    one, two = lit(1), lit(2)
    eq = tok(TokenType.EQUAL, "=")
    plus = tok(TokenType.PLUS, "+")
    assign_a = _stmt(Assignment(target=var_a, operator=eq, value=one, line=L, column=C))
    assign_b = _stmt(Assignment(target=var_b, operator=eq, value=two, line=L, column=C))
    add = BinaryOperation(left=var_a, operator=plus, right=var_b, line=L, column=C)
    prog = Program(statements=[assign_a, assign_b, _stmt(add)], line=L, column=C)
    assert value_to_python(run_ast(prog)) == 3


def test_builtin_print():
    printed = []

    def capture(args):
        printed[:] = [value_to_python(a) for a in args]
        return NULL

    from powerlang.builtins import get_builtins
    from powerlang.interpreter.values import BuiltinFunctionValue
    bu = get_builtins()
    saved = bu["print"]
    try:
        bu["print"] = BuiltinFunctionValue("print", capture, None)
        call = CallExpression(callee=var("print"), arguments=[lit(3)], line=L, column=C)
        prog = Program(statements=[_stmt(call)], line=L, column=C)
        run_ast(prog)
        assert printed == [3]
    finally:
        bu["print"] = saved


def test_builtin_len():
    call = CallExpression(callee=var("len"), arguments=[lit("abc")], line=L, column=C)
    prog = Program(statements=[_stmt(call)], line=L, column=C)
    assert value_to_python(run_ast(prog)) == 3

    arr = ArrayLiteral(elements=[lit(1), lit(2), lit(3)], line=L, column=C)
    call2 = CallExpression(callee=var("len"), arguments=[arr], line=L, column=C)
    prog2 = Program(statements=[_stmt(call2)], line=L, column=C)
    assert value_to_python(run_ast(prog2)) == 3


def test_function_call():
    t_f = tok(TokenType.IDENTIFIER, "f")
    body = Block(statements=[ReturnStatement(value=lit(42), line=L, column=C)], line=L, column=C)
    decl = FunctionDeclaration(name_token=t_f, parameters=[], body=body, line=L, column=C)
    call = CallExpression(callee=Variable(t_f, L, C), arguments=[], line=L, column=C)
    prog = Program(statements=[_stmt(call)], functions=[decl], line=L, column=C)
    assert value_to_python(run_ast(prog)) == 42


def test_function_with_params():
    t_add = tok(TokenType.IDENTIFIER, "add")
    t_a, t_b = tok(TokenType.VARIABLE, "$a", "a"), tok(TokenType.VARIABLE, "$b", "b")
    var_a = Variable(name_token=t_a, line=L, column=C)
    var_b = Variable(name_token=t_b, line=L, column=C)
    add_expr = BinaryOperation(left=var_a, operator=tok(TokenType.PLUS, "+"), right=var_b, line=L, column=C)
    body = Block(statements=[ReturnStatement(value=add_expr, line=L, column=C)], line=L, column=C)
    params = [Parameter(name_token=t_a, line=L, column=C), Parameter(name_token=t_b, line=L, column=C)]
    decl = FunctionDeclaration(name_token=t_add, parameters=params, body=body, line=L, column=C)
    call = CallExpression(callee=Variable(t_add, L, C), arguments=[lit(1), lit(2)], line=L, column=C)
    prog = Program(statements=[_stmt(call)], functions=[decl], line=L, column=C)
    assert value_to_python(run_ast(prog)) == 3


def test_array_literal_and_index():
    arr = ArrayLiteral(elements=[lit(10), lit(20), lit(30)], line=L, column=C)
    idx = IndexAccess(object=arr, index=lit(1), line=L, column=C)
    prog = Program(statements=[_stmt(idx)], line=L, column=C)
    assert value_to_python(run_ast(prog)) == 20


def test_hash_literal_and_index():
    kx, ky = lit("x"), lit("y")
    v1, v2 = lit(1), lit(2)
    pairs = [
        HashPair(key=kx, value=v1, line=L, column=C),
        HashPair(key=ky, value=v2, line=L, column=C),
    ]
    h = HashLiteral(pairs=pairs, line=L, column=C)
    idx = IndexAccess(object=h, index=kx, line=L, column=C)
    prog = Program(statements=[_stmt(idx)], line=L, column=C)
    assert value_to_python(run_ast(prog)) == 1


def test_unary():
    assert value_to_python(run_source("-5;")) == -5


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def _run_all():
    tests = [
        test_literals,
        test_arithmetic,
        test_comparison_and_logic,
        test_blocks,
        test_if_else,
        test_while,
        test_ternary,
        test_unary,
        test_variables_and_assignment,
        test_builtin_print,
        test_builtin_len,
        test_function_call,
        test_function_with_params,
        test_array_literal_and_index,
        test_hash_literal_and_index,
    ]
    failed = []
    for t in tests:
        try:
            t()
            print(f"  OK  {t.__name__}")
        except Exception as e:
            print(f"  FAIL {t.__name__}: {e}")
            failed.append((t.__name__, e))
    if failed:
        print(f"\n{len(failed)} failed")
        sys.exit(1)
    print(f"\n{len(tests)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run_all() or 0)
