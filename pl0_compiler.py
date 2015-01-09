from pl0_node_visitor import *
import sys
import pl0_parser
import StringIO
import os

class Block:
    def __init__(self):
        self.constants = {}
        self.variables  = {}
        self.procedures = {}

    def define(self, name, value):
        # if self.constants.has_key(name)
        self.constants[name] = value

    def update(self, name, value):
        self.variables[name] = value

    def declare(self, name, value):
        self.procedures[name] = value

    def debug(self):
        print "-- Stack Frame --"
        print "Constants: " + `self.constants`
        print "Variables: " + `self.variables`
        print "Procedures: " + `self.procedures`

    def lookup(self, name):
        if self.constants.has_key(name):
            return ("CONSTANT", self.constants[name],)
        elif self.variables.has_key(name):
            return ("VARIABLE", self.variables[name],)
        elif self.procedures.has_key(name):
            return ("PROCEDURE", self.procedures[name],)
        else:
            return (False, None,)

class Compiler(NodeVisitor):
    def __init__(self):
        self.stack = []
        self.label_id = 0
        self.line_no = 0
        self.locations = {}
        self.code = ""

    def intermediate_label(self, hint = ""):
        self.label_id += 1
        return "t_" + hint + "_" + `self.label_id`

    def replace_labels(self):
        for location, line_no in self.locations.items():
            self.code = self.code.replace(location, str(line_no))

    def find(self, name):
        for x in range(1, len(self.stack) + 1):
            defined, value = self.stack[-x].lookup(name)

            if defined:
                return (defined, value, -x,)

        raise NameError("Undefined name referenced: " + `name`)

    def generate(self, node):
        self.push()
        result = self.visit_node(node)
        self.pop()
        self.replace_labels()
        return self.code

    def push(self):
        self.stack.append(Block())

    def pop(self):
        return self.stack.pop()

    def accept_variables(self, node):
        for var in node[1:]:
            variable_name = self.intermediate_label("var_" + var[1])
            self.stack[-1].update(var[1], (variable_name, node.index(var) + 2))

    def accept_constants(self, node):
        for var in node[1:]:
            self.stack[-1].define(var[1], var[2])

    def accept_procedures(self, node):
        for proc in node[1:]:
            proc_name = self.intermediate_label("proc_" + proc[1])
            proc_start = self.intermediate_label("proc_start_" + proc[1])

            self.stack[-1].declare(proc[1], proc_name)
            self.push()

            self.locations[proc_name] = self.line_no

            line = "%d %s %s\n" % (self.line_no, "JMP 0", proc_start)
            self.code += line
            self.line_no += 1

            NodeVisitor.visit_expressions(self, proc[2][1:4])

            self.locations[proc_start] = self.line_no

            if proc[2][2]:
                variable_count = len(proc[2][2]) - 1
            else:
                variable_count = 0

            line = "%d %s %d\n" % (self.line_no, "INT 0", variable_count + 3)
            self.code += line
            self.line_no += 1

            NodeVisitor.visit_node(self, proc[2][4])

            line = "%d %s\n" % (self.line_no, "OPR 0 0")
            self.code += line
            self.line_no += 1

            self.pop()

    def accept_program(self, node):
        line = "%d %s\n" % (self.line_no, "JMP 0 main")
        self.code += line
        self.line_no += 1

        block = node[1]
        NodeVisitor.visit_expressions(self, block[1:4])

        self.locations["main"] = self.line_no

        if block[2]:
            variable_count = len(block[2]) - 1
        else:
            variable_count = 0

        line = "%d %s %d\n" % (self.line_no, "INT 0", variable_count + 3)
        self.code += line
        self.line_no += 1

        NodeVisitor.visit_node(self, block[4])
        line = "%d %s\n" % (self.line_no, "OPR 0 0")
        self.code += line
        self.line_no += 1

    def accept_while(self, node):
        top_label = self.intermediate_label("while_start")
        bottom_label = self.intermediate_label("while_end")

        condition = node[1]
        loop = node[2]

        self.locations[top_label] = self.line_no

        NodeVisitor.visit_node(self, condition)

        line = "%d %s %s\n" % (self.line_no, "JPC 0", bottom_label)
        self.code += line
        self.line_no += 1

        NodeVisitor.visit_node(self, loop)

        line = "%d %s %s\n" % (self.line_no, "JPC 0", top_label)
        self.code += line
        self.line_no += 1

        self.locations[bottom_label] = self.line_no

    def accept_repeat(self, node):
        top_label = self.intermediate_label("repeat_start")
        bottom_label = self.intermediate_label("repeat_end")

        condition = node[2]
        loop = node[1]

        self.locations[top_label] = self.line_no

        NodeVisitor.visit_node(self, loop)
        NodeVisitor.visit_node(self, condition)

        line = "%d %s %s\n" % (self.line_no, "JPC 0", bottom_label)
        self.code += line
        self.line_no += 1

        line = "%d %s %s\n" % (self.line_no, "JMP 0", top_label)
        self.code += line
        self.line_no += 1

        self.locations[bottom_label] = self.line_no

    def accept_if(self, node):
        false_label = self.intermediate_label("if_false")

        condition = node[1]
        body = node[2]

        NodeVisitor.visit_node(self, condition)

        line = "%d %s %s\n" % (self.line_no, "JPC 0", false_label)
        self.code += line
        self.line_no += 1

        NodeVisitor.visit_node(self, body)

        end_label = ""
        if len(node) == 4:
            end_label = self.intermediate_label("if_end")
            line = "%d %s %s\n" % (self.line_no, "JMP 0", end_label)
            self.code += line
            self.line_no += 1

        self.locations[false_label] = self.line_no

        if len(node) == 4:
            else_body = node[3]

            NodeVisitor.visit_node(self, else_body)

            self.locations[end_label] = self.line_no

    def accept_condition(self, node):
        if node[1] == "ODD":
            condition = node[2]
            NodeVisitor.visit_node(self, condition)
            line = "%d %s\n" % (self.line_no, "OPR 0 6")
            self.code += line
            self.line_no += 1
        else:
            operator = node[2]
            lhs = node[1]
            rhs = node[3]

            NodeVisitor.visit_node(self, lhs)
            NodeVisitor.visit_node(self, rhs)

            operator_convert = {
                "LT": "OPR 0 10",
                "LTE": "OPR 0 13",
                "GT": "OPR 0 12",
                "GTE": "OPR 0 11",
                "E_ASSIGN": "OPR 0 8",
                "NE": "OPR 0 9"
            }
            line = "%d %s\n" % (self.line_no, operator_convert[operator])
            self.code += line
            self.line_no += 1

    def accept_set(self, node):
        NodeVisitor.visit_node(self, node[2])

        assign_to = node[1][1]
        defined, value, level = self.find(assign_to)

        if defined != "VARIABLE":
            raise NameError("Invalid assignment to non-variable " + assign_to + " of type " + defined)

        line = "%d %s %d %d\n" % (self.line_no, "STO", -level - 1, value[1])
        self.code += line
        self.line_no += 1

    def accept_call(self, node):
        defined, value, level = self.find(node[1])

        if defined != "PROCEDURE":
            raise NameError("Expecting procedure but got: " + defined)

        line = "%d %s %d %s\n" % (self.line_no, "CAL", -level - 1, value)
        self.code += line
        self.line_no += 1

    def accept_term(self, node):
        NodeVisitor.visit_node(self, node[1])

        for term in node[2:]:
            NodeVisitor.visit_node(self, term[1])

            line = ""
            if term[0] == "TIMES":
                line = "%d %s\n" % (self.line_no, "OPR 0 4")
            elif term[0] == "DIVIDE":
                line = "%d %s\n" % (self.line_no, "OPR 0 5")
            self.code += line
            self.line_no += 1

    def accept_expression(self, node):
        NodeVisitor.visit_node(self, node[2])

        for term in node[3:]:
            NodeVisitor.visit_node(self, term[1])

            line = ""
            if term[0] == "PLUS":
                line = "%d %s\n" % (self.line_no, "OPR 0 2")
            elif term[0] == "MINUS":
                line = "%d %s\n" % (self.line_no, "OPR 0 3")
            self.code += line
            self.line_no += 1

        if node[1] == "MINUS":
            line = "%d %s\n" % (self.line_no, "LIT 0 -1")
            self.code += line
            self.line_no += 1

            line = "%d %s\n" % (self.line_no, "OPR 0 4")
            self.code += line
            self.line_no += 1

    def accept_read(self, node):
        for name in node[1][1:]:
            defined, value, level = self.find(name[1])

            if defined == "VARIABLE":
                line = "%d %s %d %d\n" % (self.line_no, "RED", -level - 1, value[1])
                self.code += line
            else:
                raise NameError("Invalid value name " + node[1] + " of type " + defined)
            self.line_no += 1

    def accept_write(self, node):
        for name in node[1][1:]:
            NodeVisitor.visit_node(self, name)

            line = "%d %s\n" % (self.line_no, "WRT 0 0")
            self.code += line
            self.line_no += 1

    def accept_number(self, node):
        line = "%d %s %d\n" % (self.line_no, "LIT 0", node[1])
        self.code += line
        self.line_no += 1

    def accept_name(self, node):
        defined, value, level = self.find(node[1])

        if defined == "VARIABLE":
            line = "%d %s %d %d\n" % (self.line_no, "LOD", -level - 1, value[1])
            self.code += line
        elif defined == "CONSTANT":
            line = "%d %s %d\n" % (self.line_no, "LIT 0", value)
            self.code += line
        else:
            raise NameError("Invalid value name " + node[1] + " of type " + defined)
        self.line_no += 1

if __name__ == "__main__":
    code = open(sys.argv[1]).read()

    parser = pl0_parser.Parser()
    parser.input(code)
    program = parser.p_program()

    compiler = Compiler()
    a = compiler.generate(program)

    print compiler.code

    f = file("./code.txt", "w+")
    f.write(compiler.code)
    f.close()