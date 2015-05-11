import sys
import pl0_lexer

class ParseError(Exception):
    pass

class SymbolParser:
    def __init__(self, lex):
        self.lex = lex
        self.sym = None
        self.source = None
    
    def input(self, data):
        self.source = "<input>"
        self.lex.input(data)
        self.sym = self.lex.token()
    
    def get_sym(self, name = None):
        self.sym = self.lex.token()
        return self.sym
    
    def is_sym(self, name):
        return self.sym and self.sym.type == name
    
    # Raises an exception if the current symbol is not the one expected.
    def expect_sym(self, name):
        if self.is_sym(name):
            return self.sym
        elif self.sym:
            args = (self.source, self.sym.lineno, self.sym.lexpos, name, self.sym.type, self.sym.value,)
            raise ParseError("%s[%d:%d]: Expected %s but got %s (%s)" % args)
        else:
            args = (self.source, self.lex.lineno, self.lex.lexpos, name,)
            raise ParseError("%s[%d:%d]: Expected %s but got none" % args)
    
    def required(self, result, name):
        if result:
            return result
        else:
            self.expect_sym("~%s" % name)

class Parser(SymbolParser):
    def __init__(self):
        SymbolParser.__init__(self, pl0_lexer.create())

    def p_program(self):
        block = self.required(self.p_block(), "block")
        self.expect_sym("DOT")
        self.get_sym()
        
        return ("PROGRAM", block,)
    
    def p_block(self):
        const_decl = self.p_const_decl()
        var_decl = self.p_var_decl()
        procedures_decl = self.p_procedures_decl()
        statement = self.p_statement()
        
        return ("BLOCK", const_decl, var_decl, procedures_decl, statement,)
    
    def p_const_decl(self):
        if self.is_sym("CONST"):
            constants = ["CONSTANTS"]
            
            while True:
                self.get_sym()
                
                assignment = self.p_const_assign()
                
                if assignment:
                    constants.append(assignment)
                
                if self.is_sym("EOS"):
                    self.get_sym()
                    return constants
                
                self.expect_sym("COMMA")
        else:
            return None
    
    def p_const_assign(self):
        if self.is_sym("NAME"):
            name = self.sym.value
            
            self.get_sym("const-assign-symbol")
            self.expect_sym("E_ASSIGN")
            
            self.get_sym("const-assign-number")
            self.expect_sym("NUMBER")
            value = self.sym.value
            
            self.get_sym()
            
            return ("DEFINE", name, value,)
        else:
            return None
    
    def p_var_decl(self):
        if self.is_sym("VAR"):
            names = ["VARIABLES"]
            
            while True:
                self.get_sym()
                self.expect_sym("NAME")
                
                names.append(("NAME", self.sym.value,))
                
                self.get_sym()
                
                if self.is_sym("EOS"):
                    self.get_sym()
                    return names
                
                self.expect_sym("COMMA")
        else:
            return None
    
    def p_procedures_decl(self):
        procedures = ["PROCEDURES"]
        
        while self.is_sym("PROCEDURE"):
            self.get_sym()
            self.expect_sym("NAME")
            name = self.sym.value
            
            self.get_sym()
            self.expect_sym("EOS")
            
            self.get_sym()
            block = self.p_block()
            
            self.expect_sym("EOS")
            
            procedures.append(("PROCEDURE", name, block,))
            
            self.get_sym()
        
        if len(procedures) > 1:
            return procedures
        else:
            return None
    
    def p_statement(self):
        if self.is_sym("NAME"):
            return self.p_statement_assign()
        elif self.is_sym("CALL"):
            return self.p_statement_call()
        elif self.is_sym("BEGIN"):
            return self.p_statement_begin()
        elif self.is_sym("IF"):
            return self.p_statement_if()
        elif self.is_sym("WHILE"):
            return self.p_statement_while()
        elif self.is_sym("REPEAT"):
            return self.p_statement_repeat()
        elif self.is_sym("READ"):
            return self.p_statement_read()
        elif self.is_sym("WRITE"):
            return self.p_statement_write()
        else:
            return self.p_statement_empty()
            #self.expect_sym("~statement")
    
    def p_statement_assign(self):
        if self.is_sym("NAME"):
            name = ("NAME", self.sym.value,)
            
            self.get_sym()
            self.expect_sym("UPDATE")
            
            self.get_sym()
            expression = self.p_expression()
            
            return ("SET", name, expression,)
        else:
            return None

    def p_statement_read(self):
        if self.is_sym("READ"):
            self.get_sym("read-1")
            self.expect_sym("LPAREN")

            names = ["NAMES"]
            while True:
                self.get_sym()
                self.expect_sym("NAME")

                names.append(("NAME", self.sym.value,))

                self.get_sym()

                if self.is_sym("RPAREN"):
                    self.get_sym()
                    return ("READ", names,)

                self.expect_sym("COMMA")

        else:
            return None

    def p_statement_write(self):
        if self.is_sym("WRITE"):
            self.get_sym("print-1")
            self.expect_sym("LPAREN")
            
            names = ["NAMES"]
            while True:
                self.get_sym()
                self.expect_sym("NAME")

                names.append(("NAME", self.sym.value,))

                self.get_sym()

                if self.is_sym("RPAREN"):
                    self.get_sym()
                    return ("WRITE", names,)

                self.expect_sym("COMMA")

            return ("WRITE", names,)
        else:
            return None
    
    def p_statement_call(self):
        if self.is_sym("CALL"):
            self.get_sym("call-1")
            self.expect_sym("NAME")
            
            call = ("CALL", self.sym.value)
            self.get_sym("call-2")
            
            return call
        else:
            return None
    
    def p_statement_begin(self):
        if self.is_sym("BEGIN"):
            statements = ["BEGIN"]
            
            while True:
                self.get_sym()
                statement = self.p_statement()
                
                if statement:
                    statements.append(statement)
                
                if self.is_sym("END"):
                    self.get_sym()
                    return statements
                
                #self.expect_sym("EOS")
        else:
            return None
    
    def p_statement_if(self):
        if self.is_sym("IF"):
            self.get_sym()

            condition = self.p_condition()
            
            self.expect_sym("THEN")
            self.get_sym()
            
            statement = self.p_statement()

            if self.is_sym("ELSE"):
                self.get_sym()
                else_statement = self.p_statement()
                return ("IF", condition, statement, else_statement,)
            else:
                return ("IF", condition, statement,)
        else:
            return None
    
    def p_statement_while(self):
        if self.is_sym("WHILE"):
            self.get_sym("while-1")
            
            condition = self.p_condition()
            
            self.expect_sym("DO")
            self.get_sym("while-2")
            
            statement = self.p_statement()
            
            return ("WHILE", condition, statement,)
        else:
            return None

    def p_statement_repeat(self):
        if self.is_sym("REPEAT"):
            statements = ["STATEMENTS"]
            while True:
                self.get_sym()
                statement = self.p_statement()

                if statement:
                    statements.append(statement)

                if self.is_sym("UNTIL"):
                    self.get_sym()
                    break

            condition = self.p_condition()
            return ("REPEAT", statements, condition,)
        else:
            return None

    def p_statement_empty(self):
        return ("EMPTY",)

    def p_condition(self):
        if self.is_sym("ODD"):
            self.get_sym("condition-odd")
            expression = self.p_expression()
            return ("CONDITION", "ODD", expression,)
        
        lhs = self.p_expression()
        
        if self.sym.type in ["LT", "LTE", "GT", "GTE", "E_ASSIGN", "NE"]:
            op = self.sym.type
            self.get_sym("condition-operand")
            
            rhs = self.p_expression()
            
            return ("CONDITION", lhs, op, rhs,)
        else:
            self.expect_sym("~comparison-operator")
    
    def p_term_op(self):
        if self.is_sym("PLUS"):
            self.get_sym("term-op-plus")
            
            return "PLUS"
        elif self.is_sym("MINUS"):
            self.get_sym("term-op-minus")
            
            return "MINUS"
        else:
            return None
    
    def p_expression(self):
        sign = self.p_term_op()
        
        expression = ["EXPRESSION", sign]
        lhs = self.required(self.p_term(), "lhs-term")
        
        expression.append(lhs)
        
        while True:
            operator = self.p_term_op()
            
            if not operator:
                return expression
            
            operand = self.required(self.p_term(), "rhs-term")
            
            expression.append((operator, operand,))
    
    def p_factor_op(self):
        if self.is_sym("TIMES"):
            self.get_sym()
            
            return "TIMES"
        elif self.is_sym("DIVIDE"):
            self.get_sym()
            
            return "DIVIDE"
        else:
            return None
    
    def p_term(self):
        expression = ["TERM"]
        lhs = self.required(self.p_factor(), "lhs-factor")
        
        expression.append(lhs)
        
        while True:
            operator = self.p_factor_op()
            
            if not operator:
                return expression
            
            operand = self.required(self.p_factor(), "rhs-factor")
            
            expression.append((operator, operand,))
    
    def p_factor(self):
        if self.is_sym("NAME"):
            value = self.sym.value
            self.get_sym()
            return ("NAME", value)
        elif self.is_sym("NUMBER"):
            value = self.sym.value
            self.get_sym()
            return ("NUMBER", value)
        elif self.is_sym("LPAREN"):
            self.get_sym()
            expression = self.required(self.p_expression(), "expression")
            
            self.expect_sym("RPAREN")
            
            self.get_sym()
            return expression

def is_flat(tree):
    if tree == None:
        return False
    
    for val in tree:
        if type(val) in (list, dict, tuple):
            return False
    return True

def print_tree(tree, depth = 0):
    if is_flat(tree):
        print "  " * depth + str(tree)
    elif type(tree) == list or type(tree) == tuple:
        print_tree(tree[0], depth)
        for val in tree[1:]:
            print_tree(val, depth+1)
    elif type(tree) == dict:
        for key, val in tree.items():
            print "  " * depth + str(key)
            print_tree(val, depth+1)
    elif tree == None:
        pass
    else:
        print "  " * depth + str(tree)

if __name__ == "__main__":
    p = Parser()
    code = open(sys.argv[1]).read()
    
    p.input(code)

    result = p.p_program()
    
    print_tree(result)
