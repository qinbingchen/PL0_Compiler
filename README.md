##综述
本PL0编译器采用Python编写，目前提供了3个工具：pl0_lexer、pl0_parser和pl0_compiler，三者均可作为独立程序运行。另有解释器pl0_interpreter和语法树绘制工具pl0_graphviz正在开发中，在答辩时可能可以完成（已附带一张早期版本的语法树图）。另外，目前的程序还没有图形界面，答辩时也会添加上。

##运行环境
本PL0编译器采用Python编写，提交时的语言版本是2.7.9。安装Python运行后，可以直接在命令行中输入
	
	python [tool_path] [code_file_path]
	
来运行其中一项工具。
运行pl0_compiler会在用户根目录下生成输出结果。

##词法分析器pl0_lexer
词法分析主要采用ply库中的lex完成。这个库支持用正则表达式定义词法，如

	def t_NAME(t):
    	r"[a-zA-Z_][a-zA-Z0-9_]*"
    	return t
    	
定义了变量/常量/名的规则。而

	def t_COMMENT(t):
    	r"\#.*"
    	pass
    	
定义了注释的规则。
pl0_lexer共定义了如下关键字：

	"ODD", "CALL", "BEGIN", "END", "IF", "THEN", "ELSE", "WHILE", "DO", "REPEAT", "UNTIL","CONST", "VAR", "PROCEDURE", "READ", "WRITE"
	
以及如下符号名：

	"DOT", "EOS", "UPDATE",
    "COMMA", "LPAREN", "RPAREN",
    "PLUS", "MINUS", "TIMES", "DIVIDE",
    "LT", "LTE", "GT", "GTE", "NE",
    "E_ASSIGN",
    "NAME", "NUMBER"

pl0_lexer对每个接受的符号给出一行输出，输出格式为
	
	LexToken([token_name],[token],[line_number],[character_number])
	
例如：
	
	LexToken(NE,'<>',23,160)
	LexToken(NAME,'t',1,10)

pl0_lexer的输出可以被pl0_parser接受。

##语法分析器pl0_parser
pl0_parser接受pl0_lexer的输出，采用递归下降子程序法生成语法树，并以树形结构输出。
对于下面这个简单的程序片段：

	BEGIN
		WRITE(k);
		k := n;
		n := m + n;
		m := k;
		count := count + 1
	END

pl0_parser的输出是：
	
	BEGIN
      WRITE
        NAMES
          ('NAME', 'k')
      SET
        ('NAME', 'k')
        EXPRESSION
          TERM
            ('NAME', 'n')
      SET
        ('NAME', 'n')
        EXPRESSION
          TERM
            ('NAME', 'm')
          PLUS
            TERM
            ('NAME', 'n')
      SET
        ('NAME', 'm')
        EXPRESSION
          TERM
            ('NAME', 'k')
      SET
        ('NAME', 'count')
        EXPRESSION
          TERM
            ('NAME', 'count')
          PLUS
            TERM
            ('NUMBER', 1)

pl0_parser的输出可以被pl0_compiler接受。

pl0_parser的主要函数包括get_sym(self)和is_sym(self, name)前者用于获取下一个符号，后者用于判断当前状态是否为某一个符号。

pl0_parser使用expect_sym(self, name)和required(self, result, name)来处理一些语法错误。例如if后面一定会跟随condition和then，就可以用这种方式来强制声明。以下是处理if语句的函数：

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
            
##P-code生成工具pl0_compiler
pl0_compiler接受pl0_parser的输出，输出P-code，附带行号。对于上述程序片段，pl0_compiler的输出为：

	14 LOD 0 5
	15 WRT 0 0
	16 LOD 0 4
	17 STO 0 5
	18 LOD 0 3
	19 LOD 0 4
	20 OPR 0 2
	21 STO 0 4
	22 LOD 0 5
	23 STO 0 3
	24 LOD 0 6
	25 LIT 0 1
	26 OPR 0 2
	27 STO 0 6
	28 JPC 0 10
	29 OPR 0 0
	
pl0_compiler的主要成员变量包括：

- stack，数组类型，用于定义作用域，每出现一个procedure，就会进行一次push()，结束时pop()，初始值为[]。
- label_id，整数类型，用于给每个常量名/变量名/过程名/关键跳转位置分配唯一的名字。初始值为0，每生成一个符号，其值加一。
- line_no，整数类型，用于记录当前行号。初始值为0，每打印一行，其值加一。
- locations，字典类型，用于记录关键跳转位置。键为跳转位置名，值为跳转位置行号。初始值为{}。
- code，字符串类型，暂存代码。在最后输出代码之前需要替换跳转位置名，在此之前所有的输出都写入code。初始值为""。

下面以处理repeat的函数为例，演示以上变量的用法：

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
        
其中NodeVisitor是一个用于访问语法书节点，并调用相应处理函数的类。