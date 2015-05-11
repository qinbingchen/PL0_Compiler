import sys
import lex as lex

keywords = [
    "ODD", "CALL", "BEGIN", "END", "IF", "THEN", "ELSE", "WHILE", "DO", "REPEAT", "UNTIL",
    "CONST", "VAR", "PROCEDURE", "READ", "WRITE"
]

tokens = keywords + [
    "DOT", "EOS", "UPDATE",
    "COMMA", "LPAREN", "RPAREN",
    "PLUS", "MINUS", "TIMES", "DIVIDE", "PRINT",
    "LT", "LTE", "GT", "GTE", "NE",
    "E_ASSIGN",
    "NAME", "NUMBER"
]

t_ignore = " \t"

def t_NAME(t):
    r"[a-zA-Z_][a-zA-Z0-9_]*"
    
    if t.value.upper() in keywords:
        t.value = t.value.upper()
        t.type = t.value
    
    return t

def t_newline(t):
    r"\n+|(\r\n)+"
    t.lexer.lineno += len(t.value)

def t_COMMENT(t):
    r"\#.*"
    # No return value. Token discarded
    pass

t_DOT = r"\."
t_EOS = r";"

t_UPDATE = r":="

t_COMMA = r","
t_LPAREN = r"\("
t_RPAREN = r"\)"

t_LT = r"<"
t_LTE = r"<="
t_GT = r">"
t_GTE = r">="
t_NE = r"<>"

t_ODD = r"ODD"
t_PLUS = r"\+"
t_MINUS = r"\-"
t_TIMES = r"\*"
t_DIVIDE = r"/"

t_E_ASSIGN = r"="

def t_NUMBER(t):
    r"\d+"
    
    t.value = int(t.value)
    
    return t

# Error handling rule
def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()

def create():
    return lexer.clone()

if __name__ == "__main__":
    #code = open(sys.argv[1]).read()
    code = open("/Users/qin/Desktop/right.pl").read()
    lex.input(code)

    while True:
        tok = lex.token()
        if not tok:
            break
    
        print tok
