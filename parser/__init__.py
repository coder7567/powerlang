"""
PowerLang Parser Module
"""

from .ast import (
    # Base classes
    ASTNode, Statement, Expression,
    
    # Statements
    Program, Block, ExpressionStatement, VariableDeclaration,
    FunctionDeclaration, ClassDeclaration, NamespaceDeclaration,
    IfStatement, ForStatement, WhileStatement, DoWhileStatement,
    ForeachStatement, SwitchStatement, CaseClause, DefaultClause,
    ReturnStatement, BreakStatement, ContinueStatement,
    TryCatchStatement, CatchClause, FinallyClause, ThrowStatement,
    ImportStatement, ExportStatement, UsingStatement,
    
    # Expressions
    Literal, Variable, BinaryOperation, UnaryOperation,
    Assignment, CallExpression, MemberAccess, IndexAccess,
    NewExpression, CastExpression, TypeExpression,
    ArrayLiteral, HashLiteral, HashPair,
    LambdaExpression, TernaryExpression, RangeExpression,
    
    # Other
    Parameter, TypeAnnotation, Comment
)

from .parser import Parser
from .grammar import Grammar, GrammarRule
from .precedence import Precedence, Associativity, get_precedence, get_associativity
from .validation import SyntaxValidator

__all__ = [
    # AST Nodes
    'ASTNode', 'Statement', 'Expression',
    'Program', 'Block', 'ExpressionStatement', 'VariableDeclaration',
    'FunctionDeclaration', 'ClassDeclaration', 'NamespaceDeclaration',
    'IfStatement', 'ForStatement', 'WhileStatement', 'DoWhileStatement',
    'ForeachStatement', 'SwitchStatement', 'CaseClause', 'DefaultClause',
    'ReturnStatement', 'BreakStatement', 'ContinueStatement',
    'TryCatchStatement', 'CatchClause', 'FinallyClause', 'ThrowStatement',
    'ImportStatement', 'ExportStatement', 'UsingStatement',
    'Literal', 'Variable', 'BinaryOperation', 'UnaryOperation',
    'Assignment', 'CallExpression', 'MemberAccess', 'IndexAccess',
    'NewExpression', 'CastExpression', 'TypeExpression',
    'ArrayLiteral', 'HashLiteral', 'HashPair',
    'LambdaExpression', 'TernaryExpression', 'RangeExpression',
    'Parameter', 'TypeAnnotation', 'Comment',
    
    # Parser
    'Parser',
    
    # Grammar
    'Grammar', 'GrammarRule',
    
    # Precedence
    'Precedence', 'Associativity', 'get_precedence', 'get_associativity',
    
    # Validation
    'SyntaxValidator',
]
