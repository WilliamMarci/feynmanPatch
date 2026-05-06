# feynmanPatch/ftdl/tokens.py

TOK_EOF = "EOF"
TOK_ID = "ID"
TOK_STRING = "STRING"
TOK_NUMBER = "NUMBER"
TOK_COMMA = ","
TOK_EQUALS = "="
TOK_GT = ">"
TOK_LBRACE = "{"
TOK_RBRACE = "}"
TOK_LBRACKET = "["
TOK_RBRACKET = "]"
TOK_LPAREN = "("
TOK_RPAREN = ")"
TOK_AT = "@"
TOK_IMPORT = "IMPORT"
TOK_PARTICLE = "PARTICLE"
TOK_VERTEX = "VERTEX"

KEYWORDS = {
    "import": TOK_IMPORT,
    "particle": TOK_PARTICLE,
    "vertex": TOK_VERTEX,
}

SINGLE_CHAR_TOKENS = {
    ",": TOK_COMMA,
    "=": TOK_EQUALS,
    ">": TOK_GT,
    "{": TOK_LBRACE,
    "}": TOK_RBRACE,
    "[": TOK_LBRACKET,
    "]": TOK_RBRACKET,
    "(": TOK_LPAREN,
    ")": TOK_RPAREN,
    "@": TOK_AT,
}


class Token(object):

    def __init__(self, type_, lexeme, line, col):
        self.type = type_
        self.lexeme = lexeme
        self.line = line
        self.col = col

    def __repr__(self):
        return "Token(%s, %r, L%d:%d)" % (self.type, self.lexeme, self.line, self.col)


class LexError(Exception):
    pass
