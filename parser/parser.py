"""
Main parser implementation for PowerLang using Pratt parsing
"""

from typing import List, Optional, Any
from ..lexer import Lexer, Token, TokenType
from ..errors import ParseError, ErrorHandler, ErrorReporter
from .ast import *
from .precedence import (
    Precedence, get_precedence, get_associativity,
    can_be_binary_operator, can_be_unary_operator,
    can_be_assignment_operator, compare_precedence
)

class Parser:
    """PowerLang parser using Pratt parsing algorithm"""
    
    def __init__(self, lexer: Lexer, error_handler: Optional[ErrorHandler] = None):
        self.lexer = lexer
        self.tokens = lexer.tokenize()
        self.current = 0
        self.error_handler = error_handler or ErrorHandler()
        
        # Track nesting levels
        self.brace_depth = 0
        self.paren_depth = 0
        self.bracket_depth = 0
        
        # Type context for [type] annotations
        self.in_type_context = False
    
    def parse(self) -> Program:
        """Parse tokens into an AST"""
        try:
            program = self._parse_program()
            
            # Check for unmatched braces/parens/brackets
            if self.brace_depth > 0:
                self._error("Unmatched '{'")
            if self.paren_depth > 0:
                self._error("Unmatched '('")
            if self.bracket_depth > 0:
                self._error("Unmatched '['")
            
            return program
            
        except ParseError as e:
            self.error_handler.error(e)
            # Return empty program on error
            return Program(statements=[], namespaces=[], classes=[], functions=[], line=1, column=1)
    
    # ============================================================================
    # Program-level parsing
    # ============================================================================
    
    def _parse_program(self) -> Program:
        """Parse a complete program"""
        start_token = self._peek()
        statements: List[Statement] = []
        namespaces: List[NamespaceDeclaration] = []
        classes: List[ClassDeclaration] = []
        functions: List[FunctionDeclaration] = []
        
        while not self._is_at_end():
            try:
                # Skip comments
                if self._match(TokenType.COMMENT) or self._match(TokenType.BLOCK_COMMENT_START):
                    self._advance()
                    continue
                
                # Check for different top-level constructs
                if self._check(TokenType.USING):
                    statements.append(self._parse_using_statement())
                elif self._check(TokenType.NAMESPACE):
                    namespaces.append(self._parse_namespace_declaration())
                elif self._check(TokenType.CLASS):
                    classes.append(self._parse_class_declaration())
                elif self._check(TokenType.FUNCTION):
                    functions.append(self._parse_function_declaration())
                else:
                    stmt = self._parse_statement()
                    if stmt:
                        statements.append(stmt)
                        
            except ParseError as e:
                self.error_handler.error(e)
                self._synchronize()
        
        return Program(
            statements=statements,
            namespaces=namespaces,
            classes=classes,
            functions=functions,
            line=(start_token.line if start_token else 1),
            column=(start_token.column if start_token else 1)
        )
    
    def _parse_using_statement(self) -> UsingStatement:
        """Parse a using statement"""
        using_token = self._consume(TokenType.USING, "Expected 'using'")
        
        # Parse namespace path
        namespace_parts = self._parse_identifier_path()
        
        self._consume(TokenType.SEMICOLON, "Expected ';' after using statement")
        
        return UsingStatement(
            namespace_parts=namespace_parts,
            line=using_token.line,
            column=using_token.column
        )
    
    def _parse_namespace_declaration(self) -> NamespaceDeclaration:
        """Parse a namespace declaration"""
        namespace_token = self._consume(TokenType.NAMESPACE, "Expected 'namespace'")
        
        # Parse namespace name (can be dotted)
        name_parts = self._parse_identifier_path()
        
        self._consume(TokenType.LBRACE, "Expected '{' after namespace name")
        self.brace_depth += 1
        
        # Parse namespace body
        body = self._parse_program()
        
        self._consume(TokenType.RBRACE, "Expected '}' after namespace body")
        self.brace_depth -= 1
        
        return NamespaceDeclaration(
            name_parts=name_parts,
            body=body,
            line=namespace_token.line,
            column=namespace_token.column
        )
    
    # ============================================================================
    # Statement parsing
    # ============================================================================
    
    def _parse_statement(self) -> Optional[Statement]:
        """Parse a statement"""
        if self._is_at_end():
            return None
        
        # Check for statement-starting tokens
        if self._check(TokenType.IF):
            return self._parse_if_statement()
        elif self._check(TokenType.FOR):
            return self._parse_for_statement()
        elif self._check(TokenType.WHILE):
            return self._parse_while_statement()
        elif self._check(TokenType.DO):
            return self._parse_do_while_statement()
        elif self._check(TokenType.FOREACH):
            return self._parse_foreach_statement()
        elif self._check(TokenType.SWITCH):
            return self._parse_switch_statement()
        elif self._check(TokenType.RETURN):
            return self._parse_return_statement()
        elif self._check(TokenType.BREAK):
            return self._parse_break_statement()
        elif self._check(TokenType.CONTINUE):
            return self._parse_continue_statement()
        elif self._check(TokenType.TRY):
            return self._parse_try_catch_statement()
        elif self._check(TokenType.THROW):
            return self._parse_throw_statement()
        elif self._check(TokenType.LBRACE):
            return self._parse_block()
        elif self._check(TokenType.VARIABLE):
            # Distinguish variable declaration (e.g. `$x;` or `$x = ...`) from
            # an expression starting with a variable (e.g. `$this.value = ...`).
            next_token = self._peek_next()
            if next_token and next_token.type in (
                TokenType.DOT, TokenType.QUESTION_DOT, TokenType.DOUBLE_COLON,
                TokenType.LPAREN, TokenType.LBRACKET
            ):
                return self._parse_expression_statement()
            return self._parse_variable_declaration()
        else:
            # Expression statement
            return self._parse_expression_statement()
    
    def _parse_block(self) -> Block:
        """Parse a block statement"""
        lbrace_token = self._consume(TokenType.LBRACE, "Expected '{'")
        self.brace_depth += 1
        
        statements: List[Statement] = []
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            stmt = self._parse_statement()
            if stmt:
                statements.append(stmt)
        
        self._consume(TokenType.RBRACE, "Expected '}' after block")
        self.brace_depth -= 1
        
        return Block(
            statements=statements,
            line=lbrace_token.line,
            column=lbrace_token.column
        )
    
    def _parse_variable_declaration(self) -> VariableDeclaration:
        """Parse a variable declaration"""
        start_token = self._peek()
        
        # Check for modifiers (not supported in lexer keywords yet)
        is_global = False
        is_local = False
        is_private = False
        is_readonly = False
        
        # Check for const
        is_constant = self._match(TokenType.CONST)
        
        # Parse type annotation if present
        type_annotation = None
        if self._check(TokenType.LBRACKET):
            type_annotation = self._parse_type_annotation()
        
        # Variable name must start with $
        name_token = self._consume(TokenType.VARIABLE, "Expected variable name starting with '$'")
        
        # Parse initializer if present
        initializer = None
        if self._match(TokenType.EQUAL):
            initializer = self._parse_expression()
        
        self._consume(TokenType.SEMICOLON, "Expected ';' after variable declaration")
        
        return VariableDeclaration(
            name_token=name_token,
            type_annotation=type_annotation,
            initializer=initializer,
            is_constant=is_constant,
            is_global=is_global,
            is_private=is_private,
            is_readonly=is_readonly,
            line=start_token.line,
            column=start_token.column
        )
    
    def _parse_expression_statement(self) -> ExpressionStatement:
        """Parse an expression statement"""
        expr = self._parse_expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after expression")
        
        return ExpressionStatement(
            expression=expr,
            line=expr.line,
            column=expr.column
        )
    
    def _parse_if_statement(self) -> IfStatement:
        """Parse an if statement"""
        if_token = self._consume(TokenType.IF, "Expected 'if'")
        
        self._consume(TokenType.LPAREN, "Expected '(' after 'if'")
        self.paren_depth += 1
        condition = self._parse_expression()
        self._consume(TokenType.RPAREN, "Expected ')' after if condition")
        self.paren_depth -= 1
        
        then_branch = self._parse_statement()
        
        # Parse elseif branches
        elseif_branches: List[ElseIfBranch] = []
        while self._match(TokenType.ELSEIF):
            elseif_token = self._previous()
            
            self._consume(TokenType.LPAREN, "Expected '(' after 'elseif'")
            self.paren_depth += 1
            elseif_condition = self._parse_expression()
            self._consume(TokenType.RPAREN, "Expected ')' after elseif condition")
            self.paren_depth -= 1
            
            elseif_branch = self._parse_statement()
            elseif_branches.append(ElseIfBranch(
                condition=elseif_condition,
                branch=elseif_branch,
                line=elseif_token.line,
                column=elseif_token.column
            ))
        
        # Parse else branch
        else_branch = None
        if self._match(TokenType.ELSE):
            else_branch = self._parse_statement()
        
        return IfStatement(
            condition=condition,
            then_branch=then_branch,
            elseif_branches=elseif_branches,
            else_branch=else_branch,
            line=if_token.line,
            column=if_token.column
        )
    
    def _parse_for_statement(self) -> ForStatement:
        """Parse a for statement"""
        for_token = self._consume(TokenType.FOR, "Expected 'for'")
        
        self._consume(TokenType.LPAREN, "Expected '(' after 'for'")
        self.paren_depth += 1
        
        # Parse initializer (optional)
        initializer = None
        if not self._check(TokenType.SEMICOLON):
            if self._check(TokenType.VARIABLE):
                initializer = self._parse_variable_declaration()
            else:
                initializer = self._parse_expression_statement()
        
        self._consume(TokenType.SEMICOLON, "Expected ';' after for initializer")
        
        # Parse condition (optional)
        condition = None
        if not self._check(TokenType.SEMICOLON):
            condition = self._parse_expression()
        
        self._consume(TokenType.SEMICOLON, "Expected ';' after for condition")
        
        # Parse increment (optional)
        increment = None
        if not self._check(TokenType.RPAREN):
            increment = self._parse_expression()
        
        self._consume(TokenType.RPAREN, "Expected ')' after for clauses")
        self.paren_depth -= 1
        
        body = self._parse_statement()
        
        return ForStatement(
            initializer=initializer,
            condition=condition,
            increment=increment,
            body=body,
            line=for_token.line,
            column=for_token.column
        )
    
    def _parse_while_statement(self) -> WhileStatement:
        """Parse a while statement"""
        while_token = self._consume(TokenType.WHILE, "Expected 'while'")
        
        self._consume(TokenType.LPAREN, "Expected '(' after 'while'")
        self.paren_depth += 1
        condition = self._parse_expression()
        self._consume(TokenType.RPAREN, "Expected ')' after while condition")
        self.paren_depth -= 1
        
        body = self._parse_statement()
        
        return WhileStatement(
            condition=condition,
            body=body,
            is_do_while=False,
            line=while_token.line,
            column=while_token.column
        )
    
    def _parse_do_while_statement(self) -> DoWhileStatement:
        """Parse a do-while statement"""
        do_token = self._consume(TokenType.DO, "Expected 'do'")
        
        body = self._parse_statement()
        
        self._consume(TokenType.WHILE, "Expected 'while' after do statement")
        
        self._consume(TokenType.LPAREN, "Expected '(' after 'while'")
        self.paren_depth += 1
        condition = self._parse_expression()
        self._consume(TokenType.RPAREN, "Expected ')' after while condition")
        self.paren_depth -= 1
        
        self._consume(TokenType.SEMICOLON, "Expected ';' after do-while statement")
        
        return DoWhileStatement(
            body=body,
            condition=condition,
            line=do_token.line,
            column=do_token.column
        )
    
    def _parse_foreach_statement(self) -> ForeachStatement:
        """Parse a foreach statement"""
        foreach_token = self._consume(TokenType.FOREACH, "Expected 'foreach'")
        
        self._consume(TokenType.LPAREN, "Expected '(' after 'foreach'")
        self.paren_depth += 1
        
        # Parse variable type annotation if present
        variable_type = None
        if self._check(TokenType.LBRACKET):
            variable_type = self._parse_type_annotation()
        
        # Parse variable name
        variable_token = self._consume(TokenType.VARIABLE, "Expected variable name in foreach")
        
        self._consume(TokenType.IN, "Expected 'in' after foreach variable")
        
        collection = self._parse_expression()
        
        self._consume(TokenType.RPAREN, "Expected ')' after foreach collection")
        self.paren_depth -= 1
        
        body = self._parse_statement()
        
        return ForeachStatement(
            variable_token=variable_token,
            variable_type=variable_type,
            collection=collection,
            body=body,
            line=foreach_token.line,
            column=foreach_token.column
        )
    
    def _parse_switch_statement(self) -> SwitchStatement:
        """Parse a switch statement"""
        switch_token = self._consume(TokenType.SWITCH, "Expected 'switch'")
        
        self._consume(TokenType.LPAREN, "Expected '(' after 'switch'")
        self.paren_depth += 1
        expression = self._parse_expression()
        self._consume(TokenType.RPAREN, "Expected ')' after switch expression")
        self.paren_depth -= 1
        
        self._consume(TokenType.LBRACE, "Expected '{' after switch expression")
        self.brace_depth += 1
        
        # Parse cases
        cases: List[CaseClause] = []
        default_case = None
        
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            if self._match(TokenType.CASE):
                case_token = self._previous()
                
                # Parse case values (can have multiple)
                values: List[Expression] = []
                values.append(self._parse_expression())
                
                while self._match(TokenType.COMMA):
                    values.append(self._parse_expression())
                
                # Accept either ':' or '{' after case values. Some source uses
                # brace-enclosed bodies (case 1 { ... }), while others use
                # colon followed by statements until the next case/default.
                case_statements: List[Statement] = []
                if self._match(TokenType.COLON):
                    while (not self._check(TokenType.CASE) and 
                           not self._check(TokenType.DEFAULT) and 
                           not self._check(TokenType.RBRACE)):
                        stmt = self._parse_statement()
                        if stmt:
                            case_statements.append(stmt)
                elif self._match(TokenType.LBRACE):
                    self.brace_depth += 1
                    while not self._check(TokenType.RBRACE) and not self._is_at_end():
                        stmt = self._parse_statement()
                        if stmt:
                            case_statements.append(stmt)
                    self._consume(TokenType.RBRACE, "Expected '}' after case body")
                    self.brace_depth -= 1
                else:
                    self._consume(TokenType.COLON, "Expected ':' after case values")

                case_body = Block(statements=case_statements, line=case_token.line, column=case_token.column)
                cases.append(CaseClause(values=values, body=case_body, line=case_token.line, column=case_token.column))
                
            elif self._match(TokenType.DEFAULT):
                if default_case is not None:
                    self._error("Multiple default clauses in switch statement")
                default_token = self._previous()
                default_statements: List[Statement] = []
                if self._match(TokenType.COLON):
                    while not self._check(TokenType.RBRACE) and not self._is_at_end():
                        stmt = self._parse_statement()
                        if stmt:
                            default_statements.append(stmt)
                elif self._match(TokenType.LBRACE):
                    self.brace_depth += 1
                    while not self._check(TokenType.RBRACE) and not self._is_at_end():
                        stmt = self._parse_statement()
                        if stmt:
                            default_statements.append(stmt)
                    self._consume(TokenType.RBRACE, "Expected '}' after default body")
                    self.brace_depth -= 1
                else:
                    self._consume(TokenType.COLON, "Expected ':' after 'default'")

                default_body = Block(statements=default_statements, line=default_token.line, column=default_token.column)
                default_case = DefaultClause(body=default_body, line=default_token.line, column=default_token.column)
                
            else:
                self._error(f"Expected 'case' or 'default', found {self._peek().lexeme}")
                self._advance()
        
        self._consume(TokenType.RBRACE, "Expected '}' after switch statement")
        self.brace_depth -= 1
        
        return SwitchStatement(
            expression=expression,
            cases=cases,
            default_case=default_case,
            line=switch_token.line,
            column=switch_token.column
        )
    
    def _parse_return_statement(self) -> ReturnStatement:
        """Parse a return statement"""
        return_token = self._consume(TokenType.RETURN, "Expected 'return'")
        
        value = None
        if not self._check(TokenType.SEMICOLON):
            value = self._parse_expression()
        
        self._consume(TokenType.SEMICOLON, "Expected ';' after return value")
        
        return ReturnStatement(
            value=value,
            line=return_token.line,
            column=return_token.column
        )
    
    def _parse_break_statement(self) -> BreakStatement:
        """Parse a break statement"""
        break_token = self._consume(TokenType.BREAK, "Expected 'break'")
        
        label = None
        if self._check(TokenType.IDENTIFIER):
            label_token = self._consume(TokenType.IDENTIFIER, "Expected label name")
            label = label_token.lexeme
        
        self._consume(TokenType.SEMICOLON, "Expected ';' after break statement")
        
        return BreakStatement(
            label=label,
            line=break_token.line,
            column=break_token.column
        )
    
    def _parse_continue_statement(self) -> ContinueStatement:
        """Parse a continue statement"""
        continue_token = self._consume(TokenType.CONTINUE, "Expected 'continue'")
        
        label = None
        if self._check(TokenType.IDENTIFIER):
            label_token = self._consume(TokenType.IDENTIFIER, "Expected label name")
            label = label_token.lexeme
        
        self._consume(TokenType.SEMICOLON, "Expected ';' after continue statement")
        
        return ContinueStatement(
            label=label,
            line=continue_token.line,
            column=continue_token.column
        )
    
    def _parse_try_catch_statement(self) -> TryCatchStatement:
        """Parse a try-catch-finally statement"""
        try_token = self._consume(TokenType.TRY, "Expected 'try'")
        
        try_block = self._parse_block()
        
        # Parse catch clauses
        catch_clauses: List[CatchClause] = []
        while self._match(TokenType.CATCH):
            catch_token = self._previous()
            
            exception_type = None
            exception_variable = None
            
            if self._match(TokenType.LPAREN):
                self.paren_depth += 1
                
                if self._check(TokenType.IDENTIFIER) or self._check(TokenType.LBRACKET):
                    # Parse exception type
                    exception_type = self._parse_type_expression()
                
                if self._check(TokenType.IDENTIFIER):
                    exception_variable = self._consume(TokenType.IDENTIFIER, "Expected exception variable name")
                
                self._consume(TokenType.RPAREN, "Expected ')' after catch clause")
                self.paren_depth -= 1
            
            catch_block = self._parse_block()
            catch_clauses.append(CatchClause(
                exception_type=exception_type,
                exception_variable=exception_variable,
                block=catch_block,
                line=catch_token.line,
                column=catch_token.column
            ))
        
        # Parse finally clause
        finally_block = None
        if self._match(TokenType.FINALLY):
            finally_block = self._parse_block()
        
        if not catch_clauses and finally_block is None:
            self._error("try statement must have at least one catch or finally clause")
        
        return TryCatchStatement(
            try_block=try_block,
            catch_clauses=catch_clauses,
            finally_block=finally_block,
            line=try_token.line,
            column=try_token.column
        )
    
    def _parse_throw_statement(self) -> ThrowStatement:
        """Parse a throw statement"""
        throw_token = self._consume(TokenType.THROW, "Expected 'throw'")
        
        expression = self._parse_expression()
        
        self._consume(TokenType.SEMICOLON, "Expected ';' after throw expression")
        
        return ThrowStatement(
            expression=expression,
            line=throw_token.line,
            column=throw_token.column
        )
    
    # ============================================================================
    # Function and class parsing
    # ============================================================================
    
    def _parse_function_declaration(self) -> FunctionDeclaration:
        """Parse a function declaration"""
        start_token = self._peek()
        
        # Check for async modifier
        is_async = self._match(TokenType.ASYNC)
        
        func_token = self._consume(TokenType.FUNCTION, "Expected 'function'")
        
        name_token = self._consume(TokenType.IDENTIFIER, "Expected function name")
        
        self._consume(TokenType.LPAREN, "Expected '(' after function name")
        self.paren_depth += 1
        
        # Parse parameters
        parameters: List[Parameter] = []
        if not self._check(TokenType.RPAREN):
            parameters = self._parse_parameter_list()
        
        self._consume(TokenType.RPAREN, "Expected ')' after parameter list")
        self.paren_depth -= 1
        
        # Parse return type if present
        return_type = None
        if self._check(TokenType.LBRACKET):
            return_type = self._parse_type_annotation()
        
        # Parse function body
        body = self._parse_block()
        
        return FunctionDeclaration(
            name_token=name_token,
            parameters=parameters,
            return_type=return_type,
            body=body,
            is_async=is_async,
            line=start_token.line,
            column=start_token.column
        )
    
    def _parse_class_declaration(self) -> ClassDeclaration:
        """Parse a class declaration"""
        start_token = self._peek()
        
        # Check for modifiers
        is_abstract = self._match(TokenType.ABSTRACT)
        is_sealed = self._match(TokenType.SEALED)
        
        class_token = self._consume(TokenType.CLASS, "Expected 'class'")
        
        name_token = self._consume(TokenType.IDENTIFIER, "Expected class name")
        
        # Parse base class if present
        base_class = None
        if self._match(TokenType.EXTENDS):
            base_class = self._parse_type_expression()
        
        # Parse interfaces if present
        interfaces: List[Expression] = []
        if self._match(TokenType.IMPLEMENTS):
            interfaces.append(self._parse_type_expression())
            while self._match(TokenType.COMMA):
                interfaces.append(self._parse_type_expression())
        
        self._consume(TokenType.LBRACE, "Expected '{' after class header")
        self.brace_depth += 1
        
        # Parse class members
        members: List[Statement] = []
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            member = self._parse_class_member()
            if member:
                members.append(member)
        
        self._consume(TokenType.RBRACE, "Expected '}' after class body")
        self.brace_depth -= 1
        
        return ClassDeclaration(
            name_token=name_token,
            base_class=base_class,
            interfaces=interfaces,
            members=members,
            is_abstract=is_abstract,
            is_sealed=is_sealed,
            line=start_token.line,
            column=start_token.column
        )
    
    def _parse_class_member(self) -> Optional[Statement]:
        """Parse a class member (field, method, property, etc.)"""
        # Simplified - will be expanded in later phases
        if self._check(TokenType.FUNCTION):
            return self._parse_function_declaration()
        elif self._check(TokenType.VARIABLE):
            return self._parse_variable_declaration()
        else:
            # For now, skip unknown members
            self._error(f"Unexpected token in class body: {self._peek().lexeme}")
            self._advance()
            return None
    
    def _parse_parameter_list(self) -> List[Parameter]:
        """Parse a parameter list"""
        parameters: List[Parameter] = []
        
        while True:
            param = self._parse_parameter()
            parameters.append(param)
            
            if not self._match(TokenType.COMMA):
                break
        
        return parameters
    
    def _parse_parameter(self) -> Parameter:
        """Parse a function parameter"""
        start_token = self._peek()
        
        # Parse type annotation if present
        type_annotation = None
        if self._check(TokenType.LBRACKET):
            type_annotation = self._parse_type_annotation()
        
        # Check for ref/out modifiers
        # is_ref = self._match(TokenType.REF) # Currently not implemented
        # is_out = self._match(TokenType.OUT) # Currently not implemented
        
        name = self._consume(
            TokenType.VARIABLE,
            "Expected parameter name"
        )

        
        # Parse default value if present
        default_value = None
        if self._match(TokenType.EQUAL):
            default_value = self._parse_expression()
        
        return Parameter(
            name_token=name,
            type_annotation=type_annotation,
            default_value=default_value,
            # is_ref=is_ref or is_out, # Currently not implemented
            line=start_token.line,
            column=start_token.column
        )
    
    # ============================================================================
    # Expression parsing (Pratt parser)
    # ============================================================================
    
    def _parse_expression(self) -> Expression:
        """Parse an expression using Pratt parsing"""
        return self._parse_precedence(Precedence.ASSIGNMENT)
    
    def _parse_precedence(self, precedence: Precedence) -> Expression:
        """Parse expression with given minimum precedence"""
        # Parse prefix expression
        token = self._advance()
        left = self._parse_prefix(token)

        # (debug prints removed)

        # Parse infix expressions while precedence allows
        while (
            precedence.value <= self._get_current_precedence().value and
            not self._is_at_end() and
            (
                can_be_binary_operator(self._peek().type) or
                can_be_assignment_operator(self._peek().type) or
                self._peek().type in (
                    TokenType.LPAREN, TokenType.LBRACKET,
                    TokenType.DOT, TokenType.QUESTION_DOT, TokenType.DOUBLE_COLON,
                    TokenType.PLUS_PLUS, TokenType.MINUS_MINUS, TokenType.QUESTION
                )
            )
        ):
            token = self._advance()
            left = self._parse_infix(left, token)
        
        return left
    
    def _parse_prefix(self, token: Token) -> Expression:
        """Parse a prefix expression"""
        if token.type == TokenType.IDENTIFIER:
            return self._parse_identifier(token)
        elif token.type == TokenType.VARIABLE:
            return Variable(name_token=token, line=token.line, column=token.column)
        elif token.type in (TokenType.INTEGER, TokenType.FLOAT, 
                           TokenType.STRING, TokenType.BOOL, TokenType.NULL):
            return self._parse_literal(token)
        elif token.type == TokenType.LPAREN:
            return self._parse_grouping()
        elif token.type == TokenType.LBRACKET:
            return self._parse_type_expression_or_cast()
        elif token.type == TokenType.AT:
            return self._parse_array_or_hash_literal()
        elif token.type == TokenType.LBRACE:
            return self._parse_hash_literal_brace()
        elif token.type in (TokenType.PLUS, TokenType.MINUS, TokenType.NOT):
            return self._parse_unary_operation(token)
        elif token.type == TokenType.NEW:
            return self._parse_new_expression(token)
        elif token.type == TokenType.ASYNC:
            return self._parse_async_expression(token)
        else:
            self._error(f"Unexpected token: {token.lexeme}")
            # Create a dummy expression to continue parsing
            return Literal(token=token, value=None, line=token.line, column=token.column)
            
    def _parse_infix(self, left: Expression, token: Token) -> Expression:
        """Parse an infix expression including assignments and binary ops."""
        
        # 1. Handle Assignments (Right-Associative)
        if can_be_assignment_operator(token.type):
            if not isinstance(left, (Variable, MemberAccess, IndexAccess)):
                self._error("Invalid assignment target")
                return left
            
            # Use precedence value - 1 to ensure subsequent assignments are nested correctly
            # Convert back to Precedence enum (avoid passing raw int)
            right_prec_value = Precedence.ASSIGNMENT.value - 1
            right_prec = Precedence(right_prec_value)
            right = self._parse_precedence(right_prec)
            return Assignment(
                target=left,
                operator=token,
                value=right,
                line=token.line,
                column=token.column
            )
        
        # 2. Handle All Other Infix Operators
        if can_be_binary_operator(token.type):
            return self._parse_binary_operation(left, token)
        elif token.type == TokenType.LPAREN:
            return self._parse_call(left)
        elif token.type in (TokenType.DOT, TokenType.QUESTION_DOT):
            return self._parse_member_access(left, token)
        elif token.type == TokenType.DOUBLE_COLON:
            return self._parse_static_access(left, token)
        elif token.type == TokenType.LBRACKET:
            return self._parse_index_access(left, token)
        elif token.type in (TokenType.PLUS_PLUS, TokenType.MINUS_MINUS):
            return self._parse_postfix_operation(left, token)
        elif token.type == TokenType.QUESTION:
            return self._parse_ternary_expression(left, token)
        else:
            self._error(f"Unexpected infix token: {token.lexeme}")
            return left

    def _parse_identifier(self, token: Token) -> Expression:
        """Parse an identifier expression"""
        # Check if it's actually a type in type context
        if self.in_type_context and token.type == TokenType.IDENTIFIER:
            # Might be a user-defined type
            return TypeExpression(type_token=token, is_nullable=False, is_array=False, array_rank=1, line=token.line, column=token.column)
        
        # Regular identifier
        return Variable(token, token.line, token.column)
    
    # def _parse_variable_expression(self, token: Token) -> Expression: # Not used
        """Parse a variable expression starting with $"""
        # The $ was already consumed, need the identifier
        if self._check(TokenType.IDENTIFIER):
            name_token = self._consume(TokenType.IDENTIFIER, "Expected variable name after '$'")
            return Variable(name_token=name_token, line=token.line, column=token.column)
        elif self._check(TokenType.LBRACE):
            # ${expression} interpolation
            self._advance()  # Skip {
            self.brace_depth += 1
            expr = self._parse_expression()
            self._consume(TokenType.RBRACE, "Expected '}' after interpolated expression")
            self.brace_depth -= 1
            return expr
        else:
            self._error("Expected variable name or '{' after '$'")
            return Variable(name_token=token, line=token.line, column=token.column)
    
    def _parse_literal(self, token: Token) -> Literal:
        """Parse a literal expression"""
        return Literal(token=token, value=token.literal, line=token.line, column=token.column)
    
    def _parse_grouping(self) -> Expression:
        """Parse a parenthesized expression"""
        self.paren_depth += 1
        expr = self._parse_expression()
        self._consume(TokenType.RPAREN, "Expected ')' after expression")
        self.paren_depth -= 1
        return expr
    
    def _parse_type_expression_or_cast(self) -> Expression:
        """Parse a type expression or cast expression"""
        # Enter type context
        was_in_type_context = self.in_type_context
        self.in_type_context = True
        self.bracket_depth += 1
        
        # Parse type expression
        type_expr = self._parse_type_expression()
        
        self._consume(TokenType.RBRACKET, "Expected ']' after type expression")
        self.bracket_depth -= 1
        self.in_type_context = was_in_type_context
        
        # Check if this is a cast or just a type expression
        if self._check_next_is_expression():
            # It's a cast: [type] expression
            expr = self._parse_expression()
            return CastExpression(
                type_expression=type_expr,
                expression=expr,
                is_safe_cast=False,
                line=type_expr.line,
                column=type_expr.column
            )
        else:
            # Just a type expression
            return type_expr
    
    def _parse_type_expression(self) -> TypeExpression:
        """Parse a type expression"""
        start_token = self._peek()
        
        # Parse type name
        if not self._check(
            TokenType.IDENTIFIER,
            TokenType.INT_TYPE,
            TokenType.FLOAT_TYPE,
            TokenType.STRING_TYPE,
            TokenType.BOOL_TYPE
        ):
            self._error("Expected type name in type expression")
        
        # Consume the type token
        type_token = self._advance()
        
        # Check for nullable ?
        is_nullable = self._match(TokenType.QUESTION)
        
        # Check for array brackets
        is_array = False
        array_rank = 0
        while self._match(TokenType.LBRACKET):
            self.bracket_depth += 1
            self._consume(TokenType.RBRACKET, "Expected ']' after array bracket")
            self.bracket_depth -= 1
            is_array = True
            array_rank += 1
        
        if array_rank == 0:
            array_rank = 1
        
        return TypeExpression(
            type_token=type_token,
            is_nullable=is_nullable,
            is_array=is_array,
            array_rank=array_rank,
            line=start_token.line,
            column=start_token.column
        )
    
    def _parse_type_annotation(self) -> TypeAnnotation:
        """Parse a type annotation"""
        start_token = self._peek()
        self._consume(TokenType.LBRACKET, "Expected '[' for type annotation")
        self.bracket_depth += 1
        
        type_expr = self._parse_type_expression()
        
        self._consume(TokenType.RBRACKET, "Expected ']' after type expression")
        self.bracket_depth -= 1
        
        return TypeAnnotation(
            type_expression=type_expr,
            line=start_token.line,
            column=start_token.column
        )
    
    def _parse_array_or_hash_literal(self) -> Expression:
        """Parse an array or hash literal starting with @"""
        at_token = self._previous()
        
        if self._match(TokenType.LPAREN):
            # Array literal: @(...)
            self.paren_depth += 1
            elements: List[Expression] = []
            
            if not self._check(TokenType.RPAREN):
                elements = self._parse_expression_list()
            
            self._consume(TokenType.RPAREN, "Expected ')' after array literal")
            self.paren_depth -= 1
            
            return ArrayLiteral(
                elements=elements,
                line=at_token.line,
                column=at_token.column
            )
        elif self._match(TokenType.LBRACE):
            # Hash literal: @{...}
            self.brace_depth += 1
            pairs: List[HashPair] = []
            
            if not self._check(TokenType.RBRACE):
                pairs = self._parse_hash_pair_list()
            
            self._consume(TokenType.RBRACE, "Expected '}' after hash literal")
            self.brace_depth -= 1
            
            return HashLiteral(
                pairs=pairs,
                line=at_token.line,
                column=at_token.column
            )
        else:
            self._error("Expected '(' or '{' after '@'")
            # Return empty array literal as fallback
            return ArrayLiteral([], at_token.line, at_token.column)
    
    def _parse_hash_literal_brace(self) -> Expression:
        """Parse a hash literal starting with { (without @)"""
        lbrace_token = self._previous()
        self.brace_depth += 1
        
        pairs: List[HashPair] = []
        if not self._check(TokenType.RBRACE):
            pairs = self._parse_hash_pair_list()
        
        self._consume(TokenType.RBRACE, "Expected '}' after hash literal")
        self.brace_depth -= 1
        
        return HashLiteral(
            pairs=pairs,
            line=lbrace_token.line,
            column=lbrace_token.column
        )
    
    def _parse_expression_list(self) -> List[Expression]:
        """Parse a list of expressions separated by commas"""
        expressions: List[Expression] = []
        
        while True:
            expressions.append(self._parse_expression())
            
            if not self._match(TokenType.COMMA):
                break
        
        return expressions
    
    def _parse_hash_pair_list(self) -> List[HashPair]:
        """Parse a list of hash pairs"""
        pairs: List[HashPair] = []
        
        while True:
            key = self._parse_expression()
            self._consume(TokenType.EQUAL, "Expected '=' after hash key")
            value = self._parse_expression()
            
            pairs.append(HashPair(key, value, key.line, key.column))
            
            if not self._match(TokenType.COMMA):
                break
        
        return pairs
    
    def _parse_unary_operation(self, operator: Token) -> UnaryOperation:
        """Parse a unary operation"""
        operand = self._parse_expression()
        
        return UnaryOperation(
            operator=operator,
            operand=operand,
            is_postfix=False,
            line=operator.line,
            column=operator.column
        )
    
    def _parse_postfix_operation(self, left: Expression, operator: Token) -> UnaryOperation:
        """Parse a postfix operation (++ or --)"""
        return UnaryOperation(
            operator=operator,
            operand=left,
            is_postfix=True,
            line=operator.line,
            column=operator.column
        )
    
    def _parse_new_expression(self, new_token: Token) -> NewExpression:
        """Parse a new expression"""
        type_expr = self._parse_type_expression()
        
        self._consume(TokenType.LPAREN, "Expected '(' after type in new expression")
        self.paren_depth += 1
        
        arguments: List[Expression] = []
        if not self._check(TokenType.RPAREN):
            arguments = self._parse_expression_list()
        
        self._consume(TokenType.RPAREN, "Expected ')' after new expression arguments")
        self.paren_depth -= 1
        
        return NewExpression(
            type_expression=type_expr,
            arguments=arguments,
            line=new_token.line,
            column=new_token.column
        )
    
    def _parse_async_expression(self, async_token: Token) -> Expression:
        """Parse an async expression"""
        # For now, treat async as a modifier for lambda expressions
        # This will be expanded in later phases
        if self._check(TokenType.LPAREN):
            # Async lambda
            self._advance()  # Skip (
            self.paren_depth += 1
            
            parameters: List[Parameter] = []
            if not self._check(TokenType.RPAREN):
                parameters = self._parse_parameter_list()
            
            self._consume(TokenType.RPAREN, "Expected ')' after async lambda parameters")
            self.paren_depth -= 1
            
            self._consume(TokenType.ARROW, "Expected '=>' after async lambda parameters")
            
            body: Union[Expression, Block]
            if self._check(TokenType.LBRACE):
                body = self._parse_block()
            else:
                body = self._parse_expression()
            
            return LambdaExpression(
                parameters=parameters,
                body=body,
                is_async=True,
                line=async_token.line,
                column=async_token.column
            )
        else:
            self._error("Expected '(' after 'async'")
            # Return dummy expression
            return Literal(async_token, None, async_token.line, async_token.column)
    
    def _parse_binary_operation(self, left: Expression, operator: Token) -> BinaryOperation:
        """Parse a binary operation"""
        # Get precedence of current operator
        current_precedence = get_precedence(operator.type)
        
        # Parse right operand with appropriate precedence
        right = self._parse_precedence(current_precedence)
        
        return BinaryOperation(
            left=left,
            operator=operator,
            right=right,
            line=operator.line,
            column=operator.column
        )
    
    def _parse_call(self, callee: Expression) -> CallExpression:
        """Parse a function call"""
        lparen_token = self._previous()
        self.paren_depth += 1
        
        arguments: List[Expression] = []
        if not self._check(TokenType.RPAREN):
            arguments = self._parse_expression_list()
        
        self._consume(TokenType.RPAREN, "Expected ')' after arguments")
        self.paren_depth -= 1
        
        return CallExpression(
            callee=callee,
            arguments=arguments,
            line=lparen_token.line,
            column=lparen_token.column
        )
    
    def _parse_member_access(self, obj: Expression, dot_token: Token) -> MemberAccess:
        """Parse a member access (object.member)"""
        is_null_conditional = (dot_token.type == TokenType.QUESTION_DOT)
        
        member_token = self._consume(TokenType.IDENTIFIER, "Expected member name after '.'")
        
        return MemberAccess(
            object=obj,
            member_token=member_token,
            is_null_conditional=is_null_conditional,
            line=dot_token.line,
            column=dot_token.column
        )
    
    def _parse_static_access(self, obj: Expression, double_colon_token: Token) -> MemberAccess:
        """Parse a static member access (Type::Member)"""
        member_token = self._consume(TokenType.IDENTIFIER, "Expected member name after '::'")
        
        return MemberAccess(
            object=obj,
            member_token=member_token,
            is_null_conditional=False,
            line=double_colon_token.line,
            column=double_colon_token.column
        )
    
    def _parse_index_access(self, obj: Expression, lbracket_token: Token) -> IndexAccess:
        """Parse an index access (array[index])"""
        is_null_conditional = False
        if lbracket_token.lexeme == '?[':
            is_null_conditional = True
        
        self.bracket_depth += 1
        index = self._parse_expression()
        self._consume(TokenType.RBRACKET, "Expected ']' after index")
        self.bracket_depth -= 1
        
        return IndexAccess(
            object=obj,
            index=index,
            is_null_conditional=is_null_conditional,
            line=lbracket_token.line,
            column=lbracket_token.column
        )
    
    def _parse_ternary_expression(self, condition: Expression, question_token: Token) -> TernaryExpression:
        """Parse a ternary expression (condition ? then : else)"""
        then_expr = self._parse_expression()
        self._consume(TokenType.COLON, "Expected ':' in ternary expression")
        else_expr = self._parse_expression()
        
        return TernaryExpression(
            condition=condition,
            then_expr=then_expr,
            else_expr=else_expr,
            line=question_token.line,
            column=question_token.column
        )
    
    # ============================================================================
    # Helper methods
    # ============================================================================
    
    def _parse_identifier_path(self) -> List[Token]:
        """Parse a dotted identifier path"""
        parts: List[Token] = []
        
        parts.append(self._consume(TokenType.IDENTIFIER, "Expected identifier"))
        
        while self._match(TokenType.DOUBLE_COLON):
            parts.append(self._consume(TokenType.IDENTIFIER, "Expected identifier after '::'"))
        
        return parts
    
    def _check_next_is_expression(self) -> bool:
        """Check if the next token could start an expression"""
        if self._is_at_end():
            return False
        
        token_type = self._peek().type
        return (token_type in (TokenType.IDENTIFIER, TokenType.VARIABLE,
                               TokenType.INTEGER, TokenType.FLOAT,
                               TokenType.STRING, TokenType.BOOL, TokenType.NULL,
                               TokenType.LPAREN, TokenType.LBRACKET,
                               TokenType.AT, TokenType.LBRACE,
                               TokenType.PLUS, TokenType.MINUS, TokenType.NOT,
                               TokenType.NEW, TokenType.ASYNC))
    
    def _get_current_precedence(self) -> Precedence:
        """Get precedence of current token if it's a binary operator"""
        if self._is_at_end():
            return Precedence.NONE
        
        token_type = self._peek().type
        # Use the precedence table for any token that has a defined precedence
        prec = get_precedence(token_type)
        if prec != Precedence.NONE:
            return prec

        # Fallback: if it's a known binary operator, return its precedence
        if can_be_binary_operator(token_type):
            return get_precedence(token_type)

        return Precedence.NONE

    def _peek_next(self) -> Optional[Token]:
        """Get the next token (lookahead) without consuming it"""
        idx = self.current + 1
        if idx >= len(self.tokens):
            last_token = self.tokens[-1] if self.tokens else None
            return Token(
                TokenType.EOF, "", None,
                last_token.line if last_token else 1,
                last_token.column if last_token else 1,
                last_token.position if last_token else 0
            )
        return self.tokens[idx]
    
    def _match(self, *token_types: TokenType) -> bool:
        """Check if current token matches any given type, consume if true"""
        if self._check(*token_types):
            self._advance()
            return True
        return False

    
    def _check(self, *token_types: TokenType) -> bool:
        """Check if current token matches any of the given types"""
        if self._is_at_end():
            return False
        return self._peek().type in token_types

    
    def _advance(self) -> Token:
        """Advance to next token and return the previous one"""
        if not self._is_at_end():
            self.current += 1
        return self._previous()
    
    def _is_at_end(self) -> bool:
        """Check if at end of tokens"""
        return self.current >= len(self.tokens) or self._peek().type == TokenType.EOF
    
    def _peek(self) -> Token:
        """Get current token without consuming it"""
        if self.current >= len(self.tokens):
            # Return EOF token if out of bounds
            last_token = self.tokens[-1] if self.tokens else None
            return Token(
                TokenType.EOF, "", None,
                last_token.line if last_token else 1,
                last_token.column if last_token else 1,
                last_token.position if last_token else 0
            )
        return self.tokens[self.current]
    
    def _previous(self) -> Token:
        """Get previous token"""
        if self.current == 0:
            # Return first token if at beginning
            return self.tokens[0] if self.tokens else Token(
                TokenType.EOF, "", None, 1, 1, 0
            )
        return self.tokens[self.current - 1]
    
    def _consume(self, token_type: TokenType, message: str) -> Token:
        """Consume token of expected type, or raise error"""
        if self._check(token_type):
            return self._advance()
        
        token = self._peek()
        self._error(f"{message}, found '{token.lexeme}'")
        
        # Return a dummy token to continue parsing
        return Token(
            token_type, "", None,
            token.line, token.column, token.position
        )
    
    def _error(self, message: str) -> None:
        """Report a parse error"""
        token = self._peek()
        error = ParseError(
            message,
            ErrorReporter.create_error_context_from_token(token)
        )
        self.error_handler.error(error)
    
    def _synchronize(self) -> None:
        """Synchronize parser after error by skipping to next statement"""
        self._advance()
        
        while not self._is_at_end():
            if self._previous().type == TokenType.SEMICOLON:
                return
            
            # Check for statement-starting tokens
            token_type = self._peek().type
            if token_type in (TokenType.IF, TokenType.FOR, TokenType.WHILE,
                             TokenType.DO, TokenType.FOREACH, TokenType.SWITCH,
                             TokenType.RETURN, TokenType.BREAK, TokenType.CONTINUE,
                             TokenType.TRY, TokenType.THROW, TokenType.LBRACE,
                             TokenType.FUNCTION, TokenType.CLASS, TokenType.NAMESPACE):
                return
            
            self._advance()
