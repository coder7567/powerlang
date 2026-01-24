"""
Syntax validation for PowerLang AST
"""

from typing import List, Dict, Set, Optional
from ..lexer.tokens import TokenType
from .ast import *
from ..errors import SemanticError, ErrorHandler

class SyntaxValidator:
    """Validates syntax and semantic rules for PowerLang AST"""
    
    def __init__(self, error_handler: Optional[ErrorHandler] = None):
        self.error_handler = error_handler or ErrorHandler()
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
        # Track declared names for duplicate checking
        self.declared_names: Dict[str, List[ASTNode]] = {}
        
        # Track control flow for break/continue validation
        self.in_loop: bool = False
        self.in_switch: bool = False
        self.loop_depth: int = 0
        self.switch_depth: int = 0
        
        # Track function context for return validation
        self.in_function: bool = False
        self.current_function: Optional[FunctionDeclaration] = None
    
    def validate(self, ast: ASTNode) -> bool:
        """Validate an AST node and all its children"""
        self.errors.clear()
        self.warnings.clear()
        self.declared_names.clear()
        self._reset_context()
        
        self._validate_node(ast)
        
        # Report errors and warnings
        for error in self.errors:
            self.error_handler.error(SemanticError(error))
        for warning in self.warnings:
            self.error_handler.warning(warning)
        
        return len(self.errors) == 0
    
    def _reset_context(self) -> None:
        """Reset validation context"""
        self.in_loop = False
        self.in_switch = False
        self.loop_depth = 0
        self.switch_depth = 0
        self.in_function = False
        self.current_function = None
    
    def _validate_node(self, node: ASTNode) -> None:
        """Dispatch to appropriate validation method based on node type"""
        if isinstance(node, Program):
            self._validate_program(node)
        elif isinstance(node, Block):
            self._validate_block(node)
        elif isinstance(node, ExpressionStatement):
            self._validate_expression_statement(node)
        elif isinstance(node, VariableDeclaration):
            self._validate_variable_declaration(node)
        elif isinstance(node, FunctionDeclaration):
            self._validate_function_declaration(node)
        elif isinstance(node, ClassDeclaration):
            self._validate_class_declaration(node)
        elif isinstance(node, NamespaceDeclaration):
            self._validate_namespace_declaration(node)
        elif isinstance(node, IfStatement):
            self._validate_if_statement(node)
        elif isinstance(node, ForStatement):
            self._validate_for_statement(node)
        elif isinstance(node, WhileStatement):
            self._validate_while_statement(node)
        elif isinstance(node, DoWhileStatement):
            self._validate_do_while_statement(node)
        elif isinstance(node, ForeachStatement):
            self._validate_foreach_statement(node)
        elif isinstance(node, SwitchStatement):
            self._validate_switch_statement(node)
        elif isinstance(node, CaseClause):
            self._validate_case_clause(node)
        elif isinstance(node, DefaultClause):
            self._validate_default_clause(node)
        elif isinstance(node, ReturnStatement):
            self._validate_return_statement(node)
        elif isinstance(node, BreakStatement):
            self._validate_break_statement(node)
        elif isinstance(node, ContinueStatement):
            self._validate_continue_statement(node)
        elif isinstance(node, TryCatchStatement):
            self._validate_try_catch_statement(node)
        elif isinstance(node, CatchClause):
            self._validate_catch_clause(node)
        elif isinstance(node, FinallyClause):
            self._validate_finally_clause(node)
        elif isinstance(node, ThrowStatement):
            self._validate_throw_statement(node)
        elif isinstance(node, ImportStatement):
            self._validate_import_statement(node)
        elif isinstance(node, ExportStatement):
            self._validate_export_statement(node)
        elif isinstance(node, UsingStatement):
            self._validate_using_statement(node)
        
        # Expressions
        elif isinstance(node, BinaryOperation):
            self._validate_binary_operation(node)
        elif isinstance(node, UnaryOperation):
            self._validate_unary_operation(node)
        elif isinstance(node, Assignment):
            self._validate_assignment(node)
        elif isinstance(node, CallExpression):
            self._validate_call_expression(node)
        elif isinstance(node, MemberAccess):
            self._validate_member_access(node)
        elif isinstance(node, IndexAccess):
            self._validate_index_access(node)
        elif isinstance(node, NewExpression):
            self._validate_new_expression(node)
        elif isinstance(node, CastExpression):
            self._validate_cast_expression(node)
        elif isinstance(node, TypeExpression):
            self._validate_type_expression(node)
        elif isinstance(node, TypeAnnotation):
            self._validate_type_annotation(node)
        elif isinstance(node, ArrayLiteral):
            self._validate_array_literal(node)
        elif isinstance(node, HashLiteral):
            self._validate_hash_literal(node)
        elif isinstance(node, LambdaExpression):
            self._validate_lambda_expression(node)
        elif isinstance(node, TernaryExpression):
            self._validate_ternary_expression(node)
        elif isinstance(node, RangeExpression):
            self._validate_range_expression(node)
        elif isinstance(node, Literal):
            self._validate_literal(node)
        elif isinstance(node, Variable):
            self._validate_variable(node)
        
        # Parameters
        elif isinstance(node, Parameter):
            self._validate_parameter(node)
    
    # ============================================================================
    # Program and declaration validation
    # ============================================================================
    
    def _validate_program(self, program: Program) -> None:
        """Validate a program"""
        # Validate all statements
        for stmt in program.statements:
            self._validate_node(stmt)
        
        # Validate namespaces
        for ns in program.namespaces:
            self._validate_node(ns)
        
        # Validate classes
        for cls in program.classes:
            self._validate_node(cls)
        
        # Validate functions
        for func in program.functions:
            self._validate_node(func)
    
    def _validate_block(self, block: Block) -> None:
        """Validate a block"""
        for stmt in block.statements:
            self._validate_node(stmt)
    
    def _validate_expression_statement(self, stmt: ExpressionStatement) -> None:
        """Validate an expression statement"""
        self._validate_node(stmt.expression)
    
    def _validate_variable_declaration(self, decl: VariableDeclaration) -> None:
        """Validate a variable declaration"""
        # Check variable name
        name = decl.name
        if not name:
            self.errors.append(f"Variable name cannot be empty at line {decl.line}")
            return
        
        # Check for duplicate declaration in same scope
        if name in self.declared_names:
            # Check if any previous declaration is in the same scope level
            previous = self.declared_names[name][-1]
            if isinstance(previous, VariableDeclaration):
                self.errors.append(
                    f"Duplicate variable declaration: '{name}' "
                    f"previously declared at line {previous.line}"
                )
        
        # Record declaration
        self._record_declaration(name, decl)
        
        # Validate type annotation
        if decl.type_annotation:
            self._validate_node(decl.type_annotation)
        
        # Validate initializer
        if decl.initializer:
            self._validate_node(decl.initializer)
            
            # Check constant initialization
            if decl.is_constant:
                # Constants must have compile-time constant initializers
                # For now, just check it exists
                pass
    
    def _validate_function_declaration(self, func: FunctionDeclaration) -> None:
        """Validate a function declaration"""
        # Save previous context
        previous_in_function = self.in_function
        previous_function = self.current_function
        
        # Set new context
        self.in_function = True
        self.current_function = func
        
        # Check function name
        name = func.name
        if not name:
            self.errors.append(f"Function name cannot be empty at line {func.line}")
            return
        
        # Check for duplicate declaration
        if name in self.declared_names:
            previous = self.declared_names[name][-1]
            if isinstance(previous, FunctionDeclaration):
                self.errors.append(
                    f"Duplicate function declaration: '{name}' "
                    f"previously declared at line {previous.line}"
                )
        
        # Record declaration
        self._record_declaration(name, func)
        
        # Validate parameters
        param_names: Set[str] = set()
        for param in func.parameters:
            self._validate_node(param)
            
            # Check for duplicate parameter names
            if param.name in param_names:
                self.errors.append(
                    f"Duplicate parameter name: '{param.name}' "
                    f"in function '{name}' at line {func.line}"
                )
            param_names.add(param.name)
            
            # Record parameter as local declaration
            self._record_declaration(param.name, param)
        
        # Validate return type
        if func.return_type:
            self._validate_node(func.return_type)
        
        # Validate function body
        self._validate_node(func.body)
        
        # Check for return statement if function has non-void return type
        if func.return_type and func.return_type.type_expression.type_name != "void":
            # TODO: Implement control flow analysis to check all paths return
            pass
        
        # Restore previous context
        self.in_function = previous_in_function
        self.current_function = previous_function
    
    def _validate_class_declaration(self, cls: ClassDeclaration) -> None:
        """Validate a class declaration"""
        # Check class name
        name = cls.name
        if not name:
            self.errors.append(f"Class name cannot be empty at line {cls.line}")
            return
        
        # Check for duplicate declaration
        if name in self.declared_names:
            previous = self.declared_names[name][-1]
            if isinstance(previous, ClassDeclaration):
                self.errors.append(
                    f"Duplicate class declaration: '{name}' "
                    f"previously declared at line {previous.line}"
                )
        
        # Record declaration
        self._record_declaration(name, cls)
        
        # Validate base class
        if cls.base_class:
            self._validate_node(cls.base_class)
        
        # Validate interfaces
        for iface in cls.interfaces:
            self._validate_node(iface)
        
        # Validate members
        member_names: Set[str] = set()
        for member in cls.members:
            self._validate_node(member)
            
            # Check for duplicate member names
            if isinstance(member, FunctionDeclaration):
                member_name = member.name
                if member_name in member_names:
                    self.errors.append(
                        f"Duplicate member '{member_name}' in class '{name}' "
                        f"at line {member.line}"
                    )
                member_names.add(member_name)
    
    # ============================================================================
    # Control flow validation
    # ============================================================================
    
    def _validate_if_statement(self, stmt: IfStatement) -> None:
        """Validate an if statement"""
        self._validate_node(stmt.condition)
        self._validate_node(stmt.then_branch)
        
        for elseif in stmt.elseif_branches:
            self._validate_node(elseif.condition)
            self._validate_node(elseif.branch)
        
        if stmt.else_branch:
            self._validate_node(stmt.else_branch)
    
    def _validate_for_statement(self, stmt: ForStatement) -> None:
        """Validate a for statement"""
        # Save previous loop context
        previous_in_loop = self.in_loop
        previous_loop_depth = self.loop_depth
        
        # Set new context
        self.in_loop = True
        self.loop_depth += 1
        
        # Validate initializer
        if stmt.initializer:
            self._validate_node(stmt.initializer)
        
        # Validate condition
        if stmt.condition:
            self._validate_node(stmt.condition)
        
        # Validate increment
        if stmt.increment:
            self._validate_node(stmt.increment)
        
        # Validate body
        self._validate_node(stmt.body)
        
        # Restore context
        self.in_loop = previous_in_loop
        self.loop_depth = previous_loop_depth
    
    def _validate_while_statement(self, stmt: WhileStatement) -> None:
        """Validate a while statement"""
        # Save previous loop context
        previous_in_loop = self.in_loop
        previous_loop_depth = self.loop_depth
        
        # Set new context
        self.in_loop = True
        self.loop_depth += 1
        
        self._validate_node(stmt.condition)
        self._validate_node(stmt.body)
        
        # Restore context
        self.in_loop = previous_in_loop
        self.loop_depth = previous_loop_depth
    
    def _validate_do_while_statement(self, stmt: DoWhileStatement) -> None:
        """Validate a do-while statement"""
        # Save previous loop context
        previous_in_loop = self.in_loop
        previous_loop_depth = self.loop_depth
        
        # Set new context
        self.in_loop = True
        self.loop_depth += 1
        
        self._validate_node(stmt.body)
        self._validate_node(stmt.condition)
        
        # Restore context
        self.in_loop = previous_in_loop
        self.loop_depth = previous_loop_depth
    
    def _validate_foreach_statement(self, stmt: ForeachStatement) -> None:
        """Validate a foreach statement"""
        # Save previous loop context
        previous_in_loop = self.in_loop
        previous_loop_depth = self.loop_depth
        
        # Set new context
        self.in_loop = True
        self.loop_depth += 1
        
        # Validate variable type
        if stmt.variable_type:
            self._validate_node(stmt.variable_type)
        
        # Validate collection
        self._validate_node(stmt.collection)
        
        # Validate body
        self._validate_node(stmt.body)
        
        # Restore context
        self.in_loop = previous_in_loop
        self.loop_depth = previous_loop_depth
    
    def _validate_switch_statement(self, stmt: SwitchStatement) -> None:
        """Validate a switch statement"""
        # Save previous switch context
        previous_in_switch = self.in_switch
        previous_switch_depth = self.switch_depth
        
        # Set new context
        self.in_switch = True
        self.switch_depth += 1
        
        self._validate_node(stmt.expression)
        
        # Validate cases
        case_values = set()
        for case in stmt.cases:
            self._validate_node(case)
            
            # Check for duplicate case values
            for value_expr in case.values:
                # TODO: Evaluate constant expressions for duplicate checking
                pass
        
        # Validate default case
        if stmt.default_case:
            self._validate_node(stmt.default_case)
        
        # Restore context
        self.in_switch = previous_in_switch
        self.switch_depth = previous_switch_depth
    
    def _validate_return_statement(self, stmt: ReturnStatement) -> None:
        """Validate a return statement"""
        # Check if we're in a function
        if not self.in_function:
            self.errors.append(
                f"Return statement outside function at line {stmt.line}"
            )
        
        # Validate return value
        if stmt.value:
            self._validate_node(stmt.value)
            
            # Check if return type matches function return type
            if self.current_function and self.current_function.return_type:
                # TODO: Type checking
                pass
    
    def _validate_break_statement(self, stmt: BreakStatement) -> None:
        """Validate a break statement"""
        # Check if we're in a loop or switch
        if not (self.in_loop or self.in_switch):
            self.errors.append(
                f"Break statement outside loop or switch at line {stmt.line}"
            )
    
    def _validate_continue_statement(self, stmt: ContinueStatement) -> None:
        """Validate a continue statement"""
        # Check if we're in a loop
        if not self.in_loop:
            self.errors.append(
                f"Continue statement outside loop at line {stmt.line}"
            )
    
    # ============================================================================
    # Expression validation
    # ============================================================================
    
    def _validate_binary_operation(self, op: BinaryOperation) -> None:
        """Validate a binary operation"""
        self._validate_node(op.left)
        self._validate_node(op.right)
        
        # Check for valid operator
        valid_operators = {
            TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH,
            TokenType.PERCENT, TokenType.EQ, TokenType.NE, TokenType.GT,
            TokenType.LT, TokenType.GE, TokenType.LE, TokenType.AND,
            TokenType.OR, TokenType.LIKE, TokenType.MATCH, TokenType.CONTAINS,
            TokenType.IN_OP, TokenType.IS_OP, TokenType.REPLACE
        }
        
        if op.operator.type not in valid_operators:
            self.errors.append(
                f"Invalid binary operator: {op.operator.lexeme} "
                f"at line {op.line}"
            )
    
    def _validate_unary_operation(self, op: UnaryOperation) -> None:
        """Validate a unary operation"""
        self._validate_node(op.operand)
        
        # Check for valid operator
        valid_operators = {
            TokenType.PLUS, TokenType.MINUS, TokenType.NOT,
            TokenType.PLUS_PLUS, TokenType.MINUS_MINUS
        }
        
        if op.operator.type not in valid_operators:
            self.errors.append(
                f"Invalid unary operator: {op.operator.lexeme} "
                f"at line {op.line}"
            )
    
    def _validate_assignment(self, assign: Assignment) -> None:
        """Validate an assignment"""
        # Validate target (must be assignable)
        self._validate_node(assign.target)

    def can_be_assignment_operator(token_type: TokenType) -> bool:
        """
        Returns True if the token type is a valid assignment operator.
        """
        return token_type in {
            TokenType.ASSIGN,          # =
            TokenType.PLUS_ASSIGN,     # +=
            TokenType.MINUS_ASSIGN,    # -=
            TokenType.STAR_ASSIGN,     # *=
            TokenType.SLASH_ASSIGN,    # /=
            TokenType.PERCENT_ASSIGN,  # %=
        }

        # Check for valid assignment operator
        if not can_be_assignment_operator(assign.operator.type):
            self.errors.append(
                f"Invalid assignment operator: {assign.operator.lexeme} "
                f"at line {assign.line}"
            )
        
        # Validate value
        self._validate_node(assign.value)
    
    def _validate_variable(self, var: Variable) -> None:
        """Validate a variable reference"""
        name = var.name
        
        # Check if variable is declared
        if name not in self.declared_names:
            self.errors.append(
                f"Undeclared variable: '{name}' at line {var.line}"
            )
    
    def _validate_call_expression(self, call: CallExpression) -> None:
        """Validate a function call"""
        self._validate_node(call.callee)
        
        for arg in call.arguments:
            self._validate_node(arg)
    
    # ============================================================================
    # Helper methods
    # ============================================================================
    
    def _record_declaration(self, name: str, node: ASTNode) -> None:
        """Record a name declaration"""
        if name not in self.declared_names:
            self.declared_names[name] = []
        self.declared_names[name].append(node)
    
    def _validate_namespace_declaration(self, ns: NamespaceDeclaration) -> None:
        """Validate a namespace declaration"""
        self._validate_node(ns.body)
    
    def _validate_case_clause(self, case: CaseClause) -> None:
        """Validate a case clause"""
        for value in case.values:
            self._validate_node(value)
        self._validate_node(case.body)
    
    def _validate_default_clause(self, default: DefaultClause) -> None:
        """Validate a default clause"""
        self._validate_node(default.body)
    
    def _validate_try_catch_statement(self, stmt: TryCatchStatement) -> None:
        """Validate a try-catch statement"""
        self._validate_node(stmt.try_block)
        
        for catch in stmt.catch_clauses:
            self._validate_node(catch)
        
        if stmt.finally_block:
            self._validate_node(stmt.finally_block)
    
    def _validate_catch_clause(self, catch: CatchClause) -> None:
        """Validate a catch clause"""
        if catch.exception_type:
            self._validate_node(catch.exception_type)
        self._validate_node(catch.block)
    
    def _validate_finally_clause(self, finally_clause: FinallyClause) -> None:
        """Validate a finally clause"""
        self._validate_node(finally_clause.block)
    
    def _validate_throw_statement(self, stmt: ThrowStatement) -> None:
        """Validate a throw statement"""
        self._validate_node(stmt.expression)
    
    def _validate_import_statement(self, stmt: ImportStatement) -> None:
        """Validate an import statement"""
        # Nothing to validate for now
        pass
    
    def _validate_export_statement(self, stmt: ExportStatement) -> None:
        """Validate an export statement"""
        self._validate_node(stmt.declaration)
    
    def _validate_using_statement(self, stmt: UsingStatement) -> None:
        """Validate a using statement"""
        # Nothing to validate for now
        pass
    
    def _validate_member_access(self, access: MemberAccess) -> None:
        """Validate a member access"""
        self._validate_node(access.object)
    
    def _validate_index_access(self, access: IndexAccess) -> None:
        """Validate an index access"""
        self._validate_node(access.object)
        self._validate_node(access.index)
    
    def _validate_new_expression(self, expr: NewExpression) -> None:
        """Validate a new expression"""
        self._validate_node(expr.type_expression)
        for arg in expr.arguments:
            self._validate_node(arg)
    
    def _validate_cast_expression(self, expr: CastExpression) -> None:
        """Validate a cast expression"""
        self._validate_node(expr.type_expression)
        self._validate_node(expr.expression)
    
    def _validate_type_expression(self, expr: TypeExpression) -> None:
        """Validate a type expression"""
        # Check if type name is valid
        type_name = expr.type_name
        valid_type_names = {
            'int', 'double', 'string', 'bool', 'array', 'void',
            'object', 'datetime', 'hashtable', 'list', 'dictionary'
        }
        
        if type_name not in valid_type_names and type_name not in self.declared_names:
            self.warnings.append(
                f"Unknown type name: '{type_name}' at line {expr.line}"
            )
    
    def _validate_type_annotation(self, annot: TypeAnnotation) -> None:
        """Validate a type annotation"""
        self._validate_node(annot.type_expression)
    
    def _validate_array_literal(self, array: ArrayLiteral) -> None:
        """Validate an array literal"""
        for elem in array.elements:
            self._validate_node(elem)
    
    def _validate_hash_literal(self, hash_lit: HashLiteral) -> None:
        """Validate a hash literal"""
        for pair in hash_lit.pairs:
            self._validate_node(pair.key)
            self._validate_node(pair.value)
    
    def _validate_lambda_expression(self, lambda_expr: LambdaExpression) -> None:
        """Validate a lambda expression"""
        # Validate parameters
        param_names: Set[str] = set()
        for param in lambda_expr.parameters:
            self._validate_node(param)
            
            if param.name in param_names:
                self.errors.append(
                    f"Duplicate parameter name: '{param.name}' "
                    f"in lambda at line {lambda_expr.line}"
                )
            param_names.add(param.name)
            
            self._record_declaration(param.name, param)
        
        # Validate body
        if isinstance(lambda_expr.body, Block):
            self._validate_node(lambda_expr.body)
        else:
            self._validate_node(lambda_expr.body)
    
    def _validate_ternary_expression(self, expr: TernaryExpression) -> None:
        """Validate a ternary expression"""
        self._validate_node(expr.condition)
        self._validate_node(expr.then_expr)
        self._validate_node(expr.else_expr)
    
    def _validate_range_expression(self, expr: RangeExpression) -> None:
        """Validate a range expression"""
        self._validate_node(expr.start)
        self._validate_node(expr.end)
    
    def _validate_literal(self, lit: Literal) -> None:
        """Validate a literal expression"""
        # Literals are always valid
        pass
    
    def _validate_parameter(self, param: Parameter) -> None:
        """Validate a parameter"""
        # Validate type annotation
        if param.type_annotation:
            self._validate_node(param.type_annotation)
        
        # Validate default value
        if param.default_value:
            self._validate_node(param.default_value)
