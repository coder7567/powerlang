"""
Main AST interpreter for PowerLang.
"""

from typing import Any, List, Optional

from ..lexer.tokens import TokenType
from ..parser.ast import (
    ArrayLiteral,
    Assignment,
    BinaryOperation,
    Block,
    BreakStatement,
    CallExpression,
    CaseClause,
    ClassDeclaration,
    ContinueStatement,
    DefaultClause,
    DoWhileStatement,
    Expression,
    ExpressionStatement,
    ForeachStatement,
    ForStatement,
    FunctionDeclaration,
    HashLiteral,
    HashPair,
    IfStatement,
    IndexAccess,
    LambdaExpression,
    Literal,
    MemberAccess,
    NewExpression,
    Parameter,
    Program,
    RangeExpression,
    ReturnStatement,
    Statement,
    SwitchStatement,
    TernaryExpression,
    ThrowStatement,
    TryCatchStatement,
    UnaryOperation,
    Variable,
    VariableDeclaration,
    WhileStatement,
)
from ..errors import (
    IndexError as PplIndexError,
    KeyError as PplKeyError,
    RuntimeError as PplRuntimeError,
)

from .environment import Environment
from .runtime import Runtime
from .values import (
    ArrayValue,
    BoolValue,
    BuiltinFunctionValue,
    ClassValue,
    FloatValue,
    FunctionValue,
    HashValue,
    InstanceValue,
    IntValue,
    NullValue,
    ParameterInfo,
    RuntimeValue,
    StringValue,
    NULL,
    python_to_value,
    value_to_python,
)


class ReturnSignal(Exception):
    def __init__(self, value: RuntimeValue):
        self.value = value


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


def _var_name(node: Variable) -> str:
    tok = getattr(node, "name_token", None)
    if tok is not None and hasattr(tok, "lexeme"):
        n = tok.lexeme
    else:
        line = getattr(node, "line", None)
        if line is not None and hasattr(line, "lexeme"):
            n = line.lexeme  # Parser bug: token passed as line
        else:
            n = getattr(node, "name", None) or ""
    if hasattr(n, "lexeme"):
        n = n.lexeme
    if not isinstance(n, str):
        n = str(n) if n is not None else ""
    if n.startswith("$"):
        n = n[1:]
    return n.lower()


def _literal_to_value(lit: Literal) -> RuntimeValue:
    v = lit.value
    if v is None:
        return NULL
    if isinstance(v, bool):
        return BoolValue(v)
    if isinstance(v, int):
        return IntValue(v)
    if isinstance(v, float):
        return FloatValue(v)
    if isinstance(v, str):
        return StringValue(v)
    return python_to_value(v)


class Interpreter:
    def __init__(self, runtime: Runtime) -> None:
        self.runtime = runtime
        self.env: Environment = runtime.new_scope()

    def run(self, program: Program) -> Optional[RuntimeValue]:
        last: Optional[RuntimeValue] = NULL
        for fn in program.functions:
            self._declare_function(fn)
        for cls in program.classes:
            self._declare_class(cls)
        for stmt in program.statements:
            last = self._execute(stmt)
        return last

    def _declare_function(self, node: FunctionDeclaration) -> None:
        name = node.name_token.lexeme
        params: List[ParameterInfo] = []
        for p in node.parameters:
            params.append(ParameterInfo(name=p.name_token.lexeme, has_default=p.default_value is not None))
        fn = FunctionValue(
            name=name,
            params=params,
            body=node.body,
            closure=self.env,
        )
        self.env.define(name, fn, constant=False)

    def _declare_class(self, node: ClassDeclaration) -> None:
        name = node.name_token.lexeme
        klass = ClassValue(name=name, methods={})
        for m in node.members:
            if isinstance(m, FunctionDeclaration):
                method_name = m.name_token.lexeme
                params = [ParameterInfo(name=p.name_token.lexeme, has_default=p.default_value is not None) for p in m.parameters]
                method = FunctionValue(
                    name=method_name,
                    params=params,
                    body=m.body,
                    closure=self.env,
                )
                klass.methods[method_name.lower()] = method
        
        self.env.define(name, klass, constant=False)

    def _execute(self, stmt: Statement) -> Optional[RuntimeValue]:
        if isinstance(stmt, Block):
            return self._execute_block(stmt)
        if isinstance(stmt, ExpressionStatement):
            return self._evaluate(stmt.expression)
        if isinstance(stmt, VariableDeclaration):
            return self._execute_variable_decl(stmt)
        if isinstance(stmt, FunctionDeclaration):
            self._declare_function(stmt)
            return NULL
        if isinstance(stmt, ClassDeclaration):
            self._declare_class(stmt)
            return NULL
        if isinstance(stmt, IfStatement):
            return self._execute_if(stmt)
        if isinstance(stmt, ForStatement):
            return self._execute_for(stmt)
        if isinstance(stmt, WhileStatement):
            return self._execute_while(stmt)
        if isinstance(stmt, DoWhileStatement):
            return self._execute_do_while(stmt)
        if isinstance(stmt, ForeachStatement):
            return self._execute_foreach(stmt)
        if isinstance(stmt, SwitchStatement):
            return self._execute_switch(stmt)
        if isinstance(stmt, ReturnStatement):
            val = self._evaluate(stmt.value) if stmt.value else NULL
            raise ReturnSignal(val)
        if isinstance(stmt, BreakStatement):
            raise BreakSignal()
        if isinstance(stmt, ContinueStatement):
            raise ContinueSignal()
        if isinstance(stmt, TryCatchStatement):
            return self._execute_try_catch(stmt)
        if isinstance(stmt, ThrowStatement):
            exc = self._evaluate(stmt.expression)
            raise PplRuntimeError(str(value_to_python(exc)))
        return NULL

    def _execute_block(self, block: Block) -> Optional[RuntimeValue]:
        prev = self.env
        self.env = prev.child()
        try:
            last: Optional[RuntimeValue] = NULL
            for s in block.statements:
                last = self._execute(s)
            return last
        finally:
            self.env = prev

    def _execute_variable_decl(self, node: VariableDeclaration) -> Optional[RuntimeValue]:
        name = getattr(node, "name", None) or (node.name_token.lexeme if node.name_token.lexeme.startswith("$") else "$" + node.name_token.lexeme)
        if name.startswith("$"):
            name = name[1:].lower()
        else:
            name = name.lower()
        value = self._evaluate(node.initializer) if node.initializer else NULL
        self.env.define(name, value, constant=node.is_constant)
        return value

    def _execute_if(self, node: IfStatement) -> Optional[RuntimeValue]:
        if self._evaluate(node.condition).is_truthy():
            return self._execute(node.then_branch)
        for elseif in node.elseif_branches:
            if self._evaluate(elseif.condition).is_truthy():
                return self._execute(elseif.branch)
        if node.else_branch:
            return self._execute(node.else_branch)
        return NULL

    def _execute_for(self, node: ForStatement) -> Optional[RuntimeValue]:
        if node.initializer:
            self._execute(node.initializer)
        while True:
            if node.condition:
                if not self._evaluate(node.condition).is_truthy():
                    break
            try:
                self._execute(node.body)
            except BreakSignal:
                break
            except ContinueSignal:
                pass
            if node.increment:
                self._evaluate(node.increment)
        return NULL

    def _execute_while(self, node: WhileStatement) -> Optional[RuntimeValue]:
        while self._evaluate(node.condition).is_truthy():
            try:
                self._execute(node.body)
            except BreakSignal:
                break
            except ContinueSignal:
                pass
        return NULL

    def _execute_do_while(self, node: DoWhileStatement) -> Optional[RuntimeValue]:
        while True:
            try:
                self._execute(node.body)
            except BreakSignal:
                break
            except ContinueSignal:
                pass
            if not self._evaluate(node.condition).is_truthy():
                break
        return NULL

    def _execute_foreach(self, node: ForeachStatement) -> Optional[RuntimeValue]:
        col = self._evaluate(node.collection)
        var_name = getattr(node, "variable_name", None) or (node.variable_token.lexeme[1:].lower() if node.variable_token.lexeme.startswith("$") else node.variable_token.lexeme.lower())
        prev = self.env
        self.env = prev.child()
        try:
            if isinstance(col, ArrayValue):
                for elem in col.elements:
                    self.env.define(var_name, elem, constant=False)
                    try:
                        self._execute(node.body)
                    except BreakSignal:
                        break
                    except ContinueSignal:
                        pass
            elif isinstance(col, StringValue):
                for c in col.value:
                    self.env.define(var_name, StringValue(c), constant=False)
                    try:
                        self._execute(node.body)
                    except BreakSignal:
                        break
                    except ContinueSignal:
                        pass
            return NULL
        finally:
            self.env = prev

    def _execute_switch(self, node: SwitchStatement) -> Optional[RuntimeValue]:
        val = self._evaluate(node.expression)
        py = value_to_python(val)

        def eq(a: RuntimeValue, b: RuntimeValue) -> bool:
            pa = value_to_python(a)
            pb = value_to_python(b)
            return pa == pb

        for case in node.cases:
            for cval_expr in case.values:
                if eq(self._evaluate(cval_expr), val):
                    self._execute_block(case.body)
                    return NULL
        if node.default_case:
            self._execute_block(node.default_case.body)
        return NULL

    def _execute_try_catch(self, node: TryCatchStatement) -> Optional[RuntimeValue]:
        try:
            return self._execute_block(node.try_block)
        except PplRuntimeError as e:
            for catch in node.catch_clauses:
                prev = self.env
                self.env = prev.child()
                try:
                    if catch.exception_variable:
                        vname = catch.exception_variable.lexeme
                        if vname.startswith("$"):
                            vname = vname[1:].lower()
                        self.env.define(vname, StringValue(str(e)), constant=False)
                    result = self._execute_block(catch.block)
                    return result
                finally:
                    self.env = prev
            raise
        finally:
            if node.finally_block:
                self._execute_block(node.finally_block)
        return NULL

    def _evaluate(self, expr: Expression) -> RuntimeValue:
        if isinstance(expr, Literal):
            return _literal_to_value(expr)
        if isinstance(expr, Variable):
            name = _var_name(expr)
            return self.env.get(name)
        if isinstance(expr, BinaryOperation):
            return self._eval_binary(expr)
        if isinstance(expr, UnaryOperation):
            return self._eval_unary(expr)
        if isinstance(expr, Assignment):
            return self._eval_assignment(expr)
        if isinstance(expr, CallExpression):
            return self._eval_call(expr)
        if isinstance(expr, MemberAccess):
            return self._eval_member_access(expr)
        if isinstance(expr, IndexAccess):
            return self._eval_index_access(expr)
        if isinstance(expr, TernaryExpression):
            return self._evaluate(expr.then_expr) if self._evaluate(expr.condition).is_truthy() else self._evaluate(expr.else_expr)
        if isinstance(expr, ArrayLiteral):
            return ArrayValue([self._evaluate(e) for e in expr.elements])
        if isinstance(expr, HashLiteral):
            pairs: dict = {}
            for p in expr.pairs:
                k = self._evaluate(p.key)
                v = self._evaluate(p.value)
                key = value_to_python(k)
                if not isinstance(key, (str, int, float, bool)):
                    key = str(key)
                pairs[key] = v
            return HashValue(pairs)
        if isinstance(expr, LambdaExpression):
            params = [ParameterInfo(name=p.name_token.lexeme, has_default=p.default_value is not None) for p in expr.parameters]
            return FunctionValue(name=None, params=params, body=expr.body, closure=self.env, is_async=expr.is_async)
        if isinstance(expr, RangeExpression):
            lo = self._evaluate(expr.start)
            hi = self._evaluate(expr.end)
            a = value_to_python(lo)
            b = value_to_python(hi)
            low = int(a) if isinstance(a, (int, float)) else 0
            high = int(b) if isinstance(b, (int, float)) else 0
            inc = 1 if expr.inclusive else 0
            return ArrayValue([IntValue(i) for i in range(low, high + inc)])
        if isinstance(expr, NewExpression):
            return self._eval_new(expr)
        return NULL

    def _eval_binary(self, node: BinaryOperation) -> RuntimeValue:
        op = node.operator.type
        left = self._evaluate(node.left)
        right = self._evaluate(node.right)
        lp = value_to_python(left)
        rp = value_to_python(right)

        if op == TokenType.EQ:
            return BoolValue(lp == rp)
        if op == TokenType.NE:
            return BoolValue(lp != rp)
        if op == TokenType.GT:
            return BoolValue(lp > rp)
        if op == TokenType.LT:
            return BoolValue(lp < rp)
        if op == TokenType.GE:
            return BoolValue(lp >= rp)
        if op == TokenType.LE:
            return BoolValue(lp <= rp)
        if op == TokenType.AND:
            return BoolValue(left.is_truthy() and right.is_truthy())
        if op == TokenType.OR:
            return BoolValue(left.is_truthy() or right.is_truthy())

        if op == TokenType.PLUS:
            if isinstance(left, StringValue) or isinstance(right, StringValue):
                return StringValue(str(lp) + str(rp))
            if isinstance(left, ArrayValue):
                arr = ArrayValue(left.elements[:])
                if isinstance(right, ArrayValue):
                    arr.elements.extend(right.elements)
                else:
                    arr.elements.append(right)
                return arr
            return python_to_value((lp or 0) + (rp or 0))
        if op == TokenType.MINUS:
            return python_to_value((lp or 0) - (rp or 0))
        if op == TokenType.STAR:
            return python_to_value((lp or 0) * (rp or 0))
        if op == TokenType.SLASH:
            if rp == 0 or (isinstance(right, (IntValue, FloatValue)) and (right.value == 0)):
                raise PplRuntimeError("Division by zero")
            return python_to_value((lp or 0) / (rp or 1))
        if op == TokenType.PERCENT:
            if rp == 0:
                raise PplRuntimeError("Division by zero")
            return IntValue(int(lp or 0) % int(rp or 1))
        if op == TokenType.CARET or op == TokenType.STAR_STAR:
            return python_to_value((lp or 0) ** (rp or 1))

        return NULL

    def _eval_unary(self, node: UnaryOperation) -> RuntimeValue:
        op = node.operator.type
        val = self._evaluate(node.operand)
        if op == TokenType.MINUS:
            p = value_to_python(val)
            return python_to_value(-(p or 0))
        if op == TokenType.PLUS:
            return val
        if op == TokenType.NOT:
            return BoolValue(not val.is_truthy())
        if op == TokenType.PLUS_PLUS:
            p = value_to_python(val)
            n = (p or 0) + 1
            out = python_to_value(n)
            self._assign_target(node.operand, out)
            return out
        if op == TokenType.MINUS_MINUS:
            p = value_to_python(val)
            n = (p or 0) - 1
            out = python_to_value(n)
            self._assign_target(node.operand, out)
            return out
        return val

    def _assign_target(self, target: Expression, value: RuntimeValue) -> None:
        if isinstance(target, Variable):
            name = _var_name(target)
            if self.env.get_optional(name) is None:
                self.env.define(name, value, constant=False)
            else:
                self.env.assign(name, value)
            return
        if isinstance(target, MemberAccess):
            obj = self._evaluate(target.object)
            if isinstance(obj, InstanceValue):
                name = target.member_token.lexeme.lower()
                obj.fields[name] = value
            return
        if isinstance(target, IndexAccess):
            container = self._evaluate(target.object)
            idx = self._evaluate(target.index)
            key = value_to_python(idx)
            if isinstance(container, ArrayValue):
                i = int(key) if isinstance(key, (int, float)) else 0
                if i < 0:
                    i += len(container.elements)
                if 0 <= i < len(container.elements):
                    container.elements[i] = value
            elif isinstance(container, HashValue):
                k = key if isinstance(key, (str, int, float, bool)) else str(key)
                container.pairs[k] = value
            return

    def _eval_assignment(self, node: Assignment) -> RuntimeValue:
        op = node.operator.type
        val = self._evaluate(node.value)
        if op != TokenType.EQUAL:
            target_val = self._evaluate(node.target)
            lp = value_to_python(target_val)
            rp = value_to_python(val)
            if op == TokenType.PLUS_EQUAL:
                val = python_to_value((lp or 0) + (rp or 0))
            elif op == TokenType.MINUS_EQUAL:
                val = python_to_value((lp or 0) - (rp or 0))
            elif op == TokenType.STAR_EQUAL:
                val = python_to_value((lp or 0) * (rp or 0))
            elif op == TokenType.SLASH_EQUAL:
                val = python_to_value((lp or 0) / (rp or 1)) if rp else NULL
            elif op == TokenType.PERCENT_EQUAL:
                val = IntValue(int(lp or 0) % int(rp or 1))
            else:
                val = target_val
        self._assign_target(node.target, val)
        return val

    def _eval_call(self, node: CallExpression) -> RuntimeValue:
        args: List[RuntimeValue] = [self._evaluate(a) for a in node.arguments]
        this_val: Optional[RuntimeValue] = None
        callee: RuntimeValue

        if isinstance(node.callee, MemberAccess):
            this_val = self._evaluate(node.callee.object)
            callee = self._eval_member_access(node.callee)
        else:
            callee = self._evaluate(node.callee)

        if isinstance(callee, BuiltinFunctionValue):
            return callee.fn(args)
        if isinstance(callee, FunctionValue):
            prev = self.env
            self.env = callee.closure.child()
            try:
                if this_val is not None and isinstance(this_val, InstanceValue):
                    self.env.define("this", this_val, constant=False)
                arg_idx = 0
                for p in callee.params:
                    if p.name in ("this", "self") and this_val is not None:
                        continue
                    if arg_idx < len(args):
                        self.env.define(p.name, args[arg_idx], constant=False)
                        arg_idx += 1
                    else:
                        self.env.define(p.name, NULL, constant=False)
                result = NULL
                if hasattr(callee.body, "statements"):
                    for s in callee.body.statements:
                        result = self._execute(s)
                else:
                    result = self._evaluate(callee.body)
                return result
            except ReturnSignal as r:
                return r.value
            finally:
                self.env = prev
        if isinstance(callee, ClassValue):
            inst = InstanceValue(klass=callee)
            init = callee.methods.get("constructor") or callee.methods.get("__init__")
            # Debug: show available methods and lookup
            if init is None:
                # Try class-named constructor (e.g. function Simple(...) inside class Simple)
                init = callee.methods.get(callee.name.lower())
            if init:
                prev = self.env
                self.env = init.closure.child()
                self.env.define("this", inst, constant=False)
                try:
                    for i, p in enumerate(init.params):
                        if p.name in ("this", "self"):
                            continue
                        if i < len(args):
                            self.env.define(p.name, args[i], constant=False)
                    for s in init.body.statements:
                        self._execute(s)
                except ReturnSignal:
                    pass
                finally:
                    pass
                    self.env = prev
            return inst
        raise PplRuntimeError("Can only call functions or classes")

    def _eval_member_access(self, node: MemberAccess) -> RuntimeValue:
        obj = self._evaluate(node.object)
        name = node.member_token.lexeme.lower()
        if isinstance(obj, InstanceValue):
            if name in obj.fields:
                return obj.fields[name]
            if name in obj.klass.methods:
                return obj.klass.methods[name]
        if isinstance(obj, ArrayValue) and name == "length":
            return IntValue(len(obj.elements))
        if isinstance(obj, StringValue) and name == "length":
            return IntValue(len(obj.value))
        raise PplRuntimeError(f"Member '{name}' not found")

    def _eval_index_access(self, node: IndexAccess) -> RuntimeValue:
        obj = self._evaluate(node.object)
        idx = self._evaluate(node.index)
        key = value_to_python(idx)
        if isinstance(obj, ArrayValue):
            i = int(key) if isinstance(key, (int, float)) else 0
            if i < 0:
                i += len(obj.elements)
            if not (0 <= i < len(obj.elements)):
                raise PplIndexError("Index out of range")
            return obj.elements[i]
        if isinstance(obj, HashValue):
            k = key if isinstance(key, (str, int, float, bool)) else str(key)
            if k not in obj.pairs:
                raise PplKeyError(f"Key not found: {k!r}")
            return obj.pairs[k]
        if isinstance(obj, StringValue):
            i = int(key) if isinstance(key, (int, float)) else 0
            if i < 0:
                i += len(obj.value)
            if not (0 <= i < len(obj.value)):
                raise PplIndexError("Index out of range")
            return StringValue(obj.value[i])
        raise PplRuntimeError("Index access only on array, hash, or string")

    def _eval_new(self, node: NewExpression) -> RuntimeValue:
        type_expr = node.type_expression
        name = getattr(type_expr, "type_name", None) or (type_expr.type_token.lexeme if hasattr(type_expr, "type_token") else "")
        args = [self._evaluate(a) for a in node.arguments]
        klass = self.env.get_optional(name)
        if klass is None:
            klass = self.runtime.globals.get_optional(name)
        if isinstance(klass, ClassValue):
            inst = InstanceValue(klass=klass)
            init = klass.methods.get("constructor") or klass.methods.get("__init__")
            # Try class-named constructor if not found
            if init is None:
                init = klass.methods.get(klass.name.lower())
            if init:
                prev = self.env
                self.env = init.closure.child()
                self.env.define("this", inst, constant=False)
                try:
                    arg_idx = 0
                    for p in init.params:
                        if p.name in ("this", "self"):
                            continue
                        if arg_idx < len(args):
                            self.env.define(p.name, args[arg_idx], constant=False)
                            arg_idx += 1
                        else:
                            self.env.define(p.name, NULL, constant=False)
                    for s in init.body.statements:
                        self._execute(s)
                except ReturnSignal:
                    pass
                finally:
                    pass
                    self.env = prev
            return inst
        if name.lower() == "array":
            return ArrayValue(list(args))
        if name.lower() == "object":
            return InstanceValue(klass=ClassValue(name="Object", methods={}))
        raise PplRuntimeError(f"Unknown type: {name}")
