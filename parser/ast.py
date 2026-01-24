"""Abstract Syntax Tree (AST) node definitions for PowerLang"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, List, Any, Union, Dict
from ..lexer.tokens import Token, TokenType


class NodeType(Enum):
    """Types of AST nodes"""
    # Program structure
    PROGRAM = auto()
    BLOCK = auto()
    
    # Statements
    EXPRESSION_STATEMENT = auto()
    VARIABLE_DECLARATION = auto()
    FUNCTION_DECLARATION = auto()
    CLASS_DECLARATION = auto()
    NAMESPACE_DECLARATION = auto()
    IF_STATEMENT = auto()
    FOR_STATEMENT = auto()
    WHILE_STATEMENT = auto()
    DO_WHILE_STATEMENT = auto()
    FOREACH_STATEMENT = auto()
    SWITCH_STATEMENT = auto()
    CASE_CLAUSE = auto()
    DEFAULT_CLAUSE = auto()
    RETURN_STATEMENT = auto()
    BREAK_STATEMENT = auto()
    CONTINUE_STATEMENT = auto()
    TRY_CATCH_STATEMENT = auto()
    CATCH_CLAUSE = auto()
    FINALLY_CLAUSE = auto()
    THROW_STATEMENT = auto()
    IMPORT_STATEMENT = auto()
    EXPORT_STATEMENT = auto()
    USING_STATEMENT = auto()
    
    # Expressions
    LITERAL = auto()
    VARIABLE = auto()
    BINARY_OPERATION = auto()
    UNARY_OPERATION = auto()
    ASSIGNMENT = auto()
    CALL_EXPRESSION = auto()
    MEMBER_ACCESS = auto()
    INDEX_ACCESS = auto()
    NEW_EXPRESSION = auto()
    CAST_EXPRESSION = auto()
    TYPE_EXPRESSION = auto()
    ARRAY_LITERAL = auto()
    HASH_LITERAL = auto()
    HASH_PAIR = auto()
    LAMBDA_EXPRESSION = auto()
    TERNARY_EXPRESSION = auto()
    RANGE_EXPRESSION = auto()
    
    # Other
    PARAMETER = auto()
    TYPE_ANNOTATION = auto()
    COMMENT = auto()


@dataclass
class ASTNode:
    line: int
    column: int
    node_type: NodeType = field(init=False)
    
    def accept(self, visitor) -> Any:
        method_name = f'visit_{self.node_type.name.lower()}'
        if hasattr(visitor, method_name):
            return getattr(visitor, method_name)(self)
        elif hasattr(visitor, 'visit'):
            return visitor.visit(self)
        else:
            raise NotImplementedError(
                f"Visitor doesn't implement {method_name} or visit()"
            )
    
    def pretty(self, indent: int = 0) -> str:
        visitor = ASTVisitor()
        return visitor.pretty(self, indent)


@dataclass
class Statement(ASTNode):
    """Base class for all statements"""
    pass


@dataclass
class Expression(ASTNode):
    """Base class for all expressions"""
    pass


# ============================================================================
# Program Structure
# ============================================================================

@dataclass
class Program(Statement):
    """Root node representing an entire program"""
    statements: List[Statement]
    namespaces: List['NamespaceDeclaration'] = field(default_factory=list)
    classes: List['ClassDeclaration'] = field(default_factory=list)
    functions: List['FunctionDeclaration'] = field(default_factory=list)
    
    def __post_init__(self):
        self.node_type = NodeType.PROGRAM


@dataclass
class Block(Statement):
    """Block of statements"""
    statements: List[Statement]
    
    def __post_init__(self):
        self.node_type = NodeType.BLOCK


# ============================================================================
# Statements
# ============================================================================

@dataclass
class ExpressionStatement(Statement):
    """Statement consisting of a single expression"""
    expression: Expression
    
    def __post_init__(self):
        self.node_type = NodeType.EXPRESSION_STATEMENT


@dataclass
class VariableDeclaration(Statement):
    """Variable declaration statement"""
    name_token: Token  # $name or name
    initializer: Optional[Expression] = None
    type_annotation: Optional['TypeAnnotation'] = None
    is_constant: bool = False
    is_global: bool = False
    is_private: bool = False
    is_readonly: bool = False
    
    def __post_init__(self):
        self.node_type = NodeType.VARIABLE_DECLARATION
    
    @property
    def name(self) -> str:
        """Get variable name without $ prefix"""
        name = self.name_token.lexeme
        if name.startswith('$'):
            return name[1:]
        return name


@dataclass
class Parameter(ASTNode):
    """Function or method parameter"""
    name_token: Token
    type_annotation: Optional['TypeAnnotation'] = None
    default_value: Optional[Expression] = None
    is_ref: bool = False
    is_params: bool = False  # For params array
    
    def __post_init__(self):
        self.node_type = NodeType.PARAMETER
    
    @property
    def name(self) -> str:
        """Get parameter name"""
        return self.name_token.lexeme


@dataclass
class FunctionDeclaration(Statement):
    """Function declaration"""
    name_token: Token
    parameters: List[Parameter]
    body: Block
    return_type: Optional['TypeAnnotation'] = None
    is_async: bool = False
    is_export: bool = False
    is_private: bool = False
    
    def __post_init__(self):
        self.node_type = NodeType.FUNCTION_DECLARATION
    
    @property
    def name(self) -> str:
        """Get function name"""
        return self.name_token.lexeme


@dataclass
class ClassDeclaration(Statement):
    """Class declaration"""
    name_token: Token
    members: List[Statement]  # Fields, methods, properties
    base_class: Optional[Expression] = None
    interfaces: List[Expression] = field(default_factory=list)
    is_abstract: bool = False
    is_sealed: bool = False
    is_static: bool = False
    is_export: bool = False
    
    def __post_init__(self):
        self.node_type = NodeType.CLASS_DECLARATION
    
    @property
    def name(self) -> str:
        """Get class name"""
        return self.name_token.lexeme


@dataclass
class NamespaceDeclaration(Statement):
    """Namespace declaration"""
    name_parts: List[Token]  # e.g., ['MyCompany', 'MyApp']
    body: Program
    
    def __post_init__(self):
        self.node_type = NodeType.NAMESPACE_DECLARATION
    
    @property
    def full_name(self) -> str:
        """Get full namespace name with dots"""
        return '.'.join(token.lexeme for token in self.name_parts)


@dataclass
class IfStatement(Statement):
    """If statement with optional elseif and else branches"""
    condition: Expression
    then_branch: Statement
    elseif_branches: List['ElseIfBranch'] = field(default_factory=list)
    else_branch: Optional[Statement] = None
    
    def __post_init__(self):
        self.node_type = NodeType.IF_STATEMENT


@dataclass
class ElseIfBranch:
    """Elseif branch in an if statement"""
    condition: Expression
    branch: Statement
    line: int
    column: int


@dataclass
class ForStatement(Statement):
    body: Statement
    initializer: Optional[Statement] = None
    condition: Optional[Expression] = None
    increment: Optional[Expression] = None
    
    def __post_init__(self):
        self.node_type = NodeType.FOR_STATEMENT


@dataclass
class WhileStatement(Statement):
    """While loop statement"""
    condition: Expression
    body: Statement
    is_do_while: bool = False
    
    def __post_init__(self):
        self.node_type = NodeType.WHILE_STATEMENT


@dataclass
class DoWhileStatement(Statement):
    """Do-while loop statement"""
    body: Statement
    condition: Expression
    
    def __post_init__(self):
        self.node_type = NodeType.DO_WHILE_STATEMENT


@dataclass
class ForeachStatement(Statement):
    """Foreach loop statement"""
    variable_token: Token
    collection: Expression
    body: Statement
    variable_type: Optional['TypeAnnotation'] = None
    
    def __post_init__(self):
        self.node_type = NodeType.FOREACH_STATEMENT
    
    @property
    def variable_name(self) -> str:
        """Get variable name"""
        name = self.variable_token.lexeme
        if name.startswith('$'):
            return name[1:]
        return name


@dataclass
class SwitchStatement(Statement):
    """Switch statement"""
    expression: Expression
    cases: List['CaseClause'] = field(default_factory=list)
    default_case: Optional['DefaultClause'] = None
    
    def __post_init__(self):
        self.node_type = NodeType.SWITCH_STATEMENT


@dataclass
class CaseClause(ASTNode):
    """Case clause in a switch statement"""
    values: List[Expression]  # Can have multiple values for one case
    body: Block
    
    def __post_init__(self):
        self.node_type = NodeType.CASE_CLAUSE


@dataclass
class DefaultClause(ASTNode):
    """Default clause in a switch statement"""
    body: Block
    
    def __post_init__(self):
        self.node_type = NodeType.DEFAULT_CLAUSE


@dataclass
class ReturnStatement(Statement):
    """Return statement"""
    value: Optional[Expression] = None
    
    def __post_init__(self):
        self.node_type = NodeType.RETURN_STATEMENT


@dataclass
class BreakStatement(Statement):
    """Break statement"""
    label: Optional[str] = None
    
    def __post_init__(self):
        self.node_type = NodeType.BREAK_STATEMENT


@dataclass
class ContinueStatement(Statement):
    """Continue statement"""
    label: Optional[str] = None
    
    def __post_init__(self):
        self.node_type = NodeType.CONTINUE_STATEMENT


@dataclass
class TryCatchStatement(Statement):
    """Try-catch-finally statement"""
    try_block: Block
    catch_clauses: List['CatchClause'] = field(default_factory=list)
    finally_block: Optional[Block] = None
    
    def __post_init__(self):
        self.node_type = NodeType.TRY_CATCH_STATEMENT


@dataclass
class CatchClause(ASTNode):
    block: Block
    exception_type: Optional[Expression] = None
    exception_variable: Optional[Token] = None
    
    def __post_init__(self):
        self.node_type = NodeType.CATCH_CLAUSE


@dataclass
class FinallyClause(ASTNode):
    """Finally clause in try-catch statement"""
    block: Block
    
    def __post_init__(self):
        self.node_type = NodeType.FINALLY_CLAUSE


@dataclass
class ThrowStatement(Statement):
    """Throw statement"""
    expression: Expression
    
    def __post_init__(self):
        self.node_type = NodeType.THROW_STATEMENT


@dataclass
class ImportStatement(Statement):
    """Import statement"""
    module_path: List[Token]  # Could be simple name or dotted path
    alias: Optional[Token] = None
    import_all: bool = False
    imports: List[Token] = field(default_factory=list)  # Specific imports
    
    def __post_init__(self):
        self.node_type = NodeType.IMPORT_STATEMENT


@dataclass
class ExportStatement(Statement):
    """Export statement"""
    declaration: Statement  # What to export
    
    def __post_init__(self):
        self.node_type = NodeType.EXPORT_STATEMENT


@dataclass
class UsingStatement(Statement):
    """Using/namespace import statement"""
    namespace_parts: List[Token]
    
    def __post_init__(self):
        self.node_type = NodeType.USING_STATEMENT


# ============================================================================
# Expressions
# ============================================================================

@dataclass
class Literal(Expression):
    """Literal value expression"""
    token: Token
    value: Any
    
    def __post_init__(self):
        self.node_type = NodeType.LITERAL


@dataclass
class Variable(Expression):
    """Variable reference expression"""
    name_token: Token  # $name or name
    
    def __post_init__(self):
        self.node_type = NodeType.VARIABLE
    
    @property
    def name(self) -> str:
        """Get variable name"""
        return self.name_token.lexeme


@dataclass
class BinaryOperation(Expression):
    """Binary operation expression"""
    left: Expression
    operator: Token
    right: Expression
    
    def __post_init__(self):
        self.node_type = NodeType.BINARY_OPERATION


@dataclass
class UnaryOperation(Expression):
    """Unary operation expression"""
    operator: Token
    operand: Expression
    is_postfix: bool = False
    
    def __post_init__(self):
        self.node_type = NodeType.UNARY_OPERATION


@dataclass
class Assignment(Expression):
    """Assignment expression"""
    target: Expression  # Variable, member access, index access
    operator: Token  # =, +=, -=, etc.
    value: Expression
    
    def __post_init__(self):
        self.node_type = NodeType.ASSIGNMENT


@dataclass
class CallExpression(Expression):
    """Function/method call expression"""
    callee: Expression
    arguments: List[Expression] = field(default_factory=list)
    is_null_conditional: bool = False  # ?. call
    
    def __post_init__(self):
        self.node_type = NodeType.CALL_EXPRESSION


@dataclass
class MemberAccess(Expression):
    """Member access expression (object.member)"""
    object: Expression
    member_token: Token
    is_null_conditional: bool = False  # ?. access
    
    def __post_init__(self):
        self.node_type = NodeType.MEMBER_ACCESS
    
    @property
    def member_name(self) -> str:
        """Get member name"""
        return self.member_token.lexeme


@dataclass
class IndexAccess(Expression):
    """Index/array access expression"""
    object: Expression
    index: Expression
    is_null_conditional: bool = False  # ?[ index
    
    def __post_init__(self):
        self.node_type = NodeType.INDEX_ACCESS


@dataclass
class NewExpression(Expression):
    """New object creation expression"""
    type_expression: Expression  # Could be TypeExpression or Variable
    arguments: List[Expression] = field(default_factory=list)
    
    def __post_init__(self):
        self.node_type = NodeType.NEW_EXPRESSION


@dataclass
class TypeExpression(Expression):
    """Type expression for casting or type checking"""
    type_token: Token  # int, string, etc. or user-defined type
    is_nullable: bool = False
    is_array: bool = False
    array_rank: int = 1  # For multidimensional arrays
    
    def __post_init__(self):
        self.node_type = NodeType.TYPE_EXPRESSION
    
    @property
    def type_name(self) -> str:
        """Get type name"""
        return self.type_token.lexeme


@dataclass
class CastExpression(Expression):
    """Type cast expression"""
    expression: Expression
    type_expression: TypeExpression
    is_safe_cast: bool = False  # as operator
    
    def __post_init__(self):
        self.node_type = NodeType.CAST_EXPRESSION


@dataclass
class TypeAnnotation(ASTNode):
    """Type annotation for variables, parameters, returns"""
    type_expression: TypeExpression
    
    def __post_init__(self):
        self.node_type = NodeType.TYPE_ANNOTATION


@dataclass
class ArrayLiteral(Expression):
    """Array literal expression @(...)"""
    elements: List[Expression] = field(default_factory=list)
    
    def __post_init__(self):
        self.node_type = NodeType.ARRAY_LITERAL


@dataclass
class HashPair(ASTNode):
    key: Expression
    value: Expression


@dataclass
class HashLiteral(Expression):
    """Hash literal expression @{...}"""
    pairs: List[HashPair] = field(default_factory=list)
    
    def __post_init__(self):
        self.node_type = NodeType.HASH_LITERAL


@dataclass
class LambdaExpression(Expression):
    body: Union[Expression, Block]
    parameters: List[Parameter] = field(default_factory=list)
    is_async: bool = False
    
    def __post_init__(self):
        self.node_type = NodeType.LAMBDA_EXPRESSION


@dataclass
class TernaryExpression(Expression):
    """Ternary conditional expression (condition ? then : else)"""
    condition: Expression
    then_expr: Expression
    else_expr: Expression
    
    def __post_init__(self):
        self.node_type = NodeType.TERNARY_EXPRESSION


@dataclass
class RangeExpression(Expression):
    """Range expression (start..end)"""
    start: Expression
    end: Expression
    inclusive: bool = True  # .. is inclusive, ..< would be exclusive
    
    def __post_init__(self):
        self.node_type = NodeType.RANGE_EXPRESSION


# ============================================================================
# Comments
# ============================================================================

@dataclass
class Comment(ASTNode):
    """Comment node"""
    token: Token
    text: str
    is_block: bool = False
    
    def __post_init__(self):
        self.node_type = NodeType.COMMENT


# Visitor base class for pattern matching
class ASTVisitor:
    """Base visitor class for traversing AST"""
    
    def visit(self, node: ASTNode) -> Any:
        """Visit a node, dispatching to appropriate method"""
        method_name = f'visit_{node.node_type.name.lower()}'
        if hasattr(self, method_name):
            return getattr(self, method_name)(node)
        else:
            return self.generic_visit(node)
    
    def generic_visit(self, node: ASTNode) -> Any:
        """Generic visitor for nodes without specific handler"""
        # Visit children based on node type
        if isinstance(node, Program):
            for stmt in node.statements:
                self.visit(stmt)
            for ns in node.namespaces:
                self.visit(ns)
            for cls in node.classes:
                self.visit(cls)
            for func in node.functions:
                self.visit(func)
        elif isinstance(node, Block):
            for stmt in node.statements:
                self.visit(stmt)
        elif isinstance(node, ExpressionStatement):
            self.visit(node.expression)
        elif isinstance(node, VariableDeclaration):
            if node.type_annotation:
                self.visit(node.type_annotation)
            if node.initializer:
                self.visit(node.initializer)
        elif isinstance(node, FunctionDeclaration):
            for param in node.parameters:
                self.visit(param)
            if node.return_type:
                self.visit(node.return_type)
            self.visit(node.body)
        elif isinstance(node, ClassDeclaration):
            if node.base_class:
                self.visit(node.base_class)
            for iface in node.interfaces:
                self.visit(iface)
            for member in node.members:
                self.visit(member)
        elif isinstance(node, NamespaceDeclaration):
            self.visit(node.body)
        elif isinstance(node, IfStatement):
            self.visit(node.condition)
            self.visit(node.then_branch)
            for elseif in node.elseif_branches:
                self.visit(elseif.condition)
                self.visit(elseif.branch)
            if node.else_branch:
                self.visit(node.else_branch)
        elif isinstance(node, ForStatement):
            if node.initializer:
                self.visit(node.initializer)
            if node.condition:
                self.visit(node.condition)
            if node.increment:
                self.visit(node.increment)
            self.visit(node.body)
        elif isinstance(node, WhileStatement):
            self.visit(node.condition)
            self.visit(node.body)
        elif isinstance(node, DoWhileStatement):
            self.visit(node.body)
            self.visit(node.condition)
        elif isinstance(node, ForeachStatement):
            if node.variable_type:
                self.visit(node.variable_type)
            self.visit(node.collection)
            self.visit(node.body)
        elif isinstance(node, SwitchStatement):
            self.visit(node.expression)
            for case in node.cases:
                self.visit(case)
            if node.default_case:
                self.visit(node.default_case)
        elif isinstance(node, CaseClause):
            for value in node.values:
                self.visit(value)
            self.visit(node.body)
        elif isinstance(node, DefaultClause):
            self.visit(node.body)
        elif isinstance(node, ReturnStatement):
            if node.value:
                self.visit(node.value)
        elif isinstance(node, TryCatchStatement):
            self.visit(node.try_block)
            for catch in node.catch_clauses:
                self.visit(catch)
            if node.finally_block:
                self.visit(node.finally_block)
        elif isinstance(node, CatchClause):
            if node.exception_type:
                self.visit(node.exception_type)
            self.visit(node.block)
        elif isinstance(node, FinallyClause):
            self.visit(node.block)
        elif isinstance(node, ThrowStatement):
            self.visit(node.expression)
        # Expressions
        elif isinstance(node, BinaryOperation):
            self.visit(node.left)
            self.visit(node.right)
        elif isinstance(node, UnaryOperation):
            self.visit(node.operand)
        elif isinstance(node, Assignment):
            self.visit(node.target)
            self.visit(node.value)
        elif isinstance(node, CallExpression):
            self.visit(node.callee)
            for arg in node.arguments:
                self.visit(arg)
        elif isinstance(node, MemberAccess):
            self.visit(node.object)
        elif isinstance(node, IndexAccess):
            self.visit(node.object)
            self.visit(node.index)
        elif isinstance(node, NewExpression):
            self.visit(node.type_expression)
            for arg in node.arguments:
                self.visit(arg)
        elif isinstance(node, CastExpression):
            self.visit(node.expression)
            self.visit(node.type_expression)
        elif isinstance(node, TypeAnnotation):
            self.visit(node.type_expression)
        elif isinstance(node, TypeExpression):
            pass  # Leaf node
        elif isinstance(node, ArrayLiteral):
            for elem in node.elements:
                self.visit(elem)
        elif isinstance(node, HashLiteral):
            for pair in node.pairs:
                self.visit(pair.key)
                self.visit(pair.value)
        elif isinstance(node, LambdaExpression):
            for param in node.parameters:
                self.visit(param)
            if isinstance(node.body, Block):
                self.visit(node.body)
            else:
                self.visit(node.body)
        elif isinstance(node, TernaryExpression):
            self.visit(node.condition)
            self.visit(node.then_expr)
            self.visit(node.else_expr)
        elif isinstance(node, RangeExpression):
            self.visit(node.start)
            self.visit(node.end)
        elif isinstance(node, Literal):
            pass  # Leaf node
        elif isinstance(node, Variable):
            pass  # Leaf node
        elif isinstance(node, Comment):
            pass  # Leaf node
        return None
    
    def pretty(self, node: ASTNode, indent=0):
        pad = " " * indent
        result = f"{pad}{node.__class__.__name__}"
        for k, v in node.__dict__.items():
            if isinstance(v, ASTNode):
                result += f"\n{pad} {k}:\n{self.pretty(v, indent + 2)}"
            elif isinstance(v, list):
                result += f"\n{pad} {k}:"
                for item in v:
                    if isinstance(item, ASTNode):
                        result += f"\n{self.pretty(item, indent + 2)}"
                    else:
                        result += f"\n{pad} {item}"
            else:
                result += f"\n{pad} {k}: {v}"
        return result
