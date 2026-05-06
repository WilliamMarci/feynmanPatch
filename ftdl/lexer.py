# feynmanPatch/ftdl/lexer.py

from .tokens import Token, LexError, TOK_EOF, TOK_ID, TOK_STRING, TOK_NUMBER
from .tokens import SINGLE_CHAR_TOKENS, KEYWORDS


def _is_letter(ch):
    return ch.isalpha() or ch == "_"


def _is_digit(ch):
    return ch.isdigit()


def _is_head(ch):
    return ch and (ch.isalpha() or ch in "_+-~")


def _is_tail(ch):
    return ch and (ch.isalnum() or ch in "_+-~")


class Lexer(object):

    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1

    def _peek(self, offset=0):
        idx = self.pos + offset
        if idx < len(self.source):
            return self.source[idx]
        return ""

    def _advance(self, n=1):
        for _ in range(n):
            ch = self._peek()
            if ch == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1
            self.pos += 1

    def _skip_whitespace(self):
        ch = self._peek()
        while ch and ch in " \t\r\n":
            self._advance()
            ch = self._peek()

    def _read_string(self):
        line, col = self.line, self.col
        self._advance()
        chars = []
        while True:
            ch = self._peek()
            if ch == "":
                raise LexError("Unterminated string at L%d:%d" % (line, col))
            if ch == '"':
                self._advance()
                break
            if ch == "\\":
                self._advance()
                escaped = self._peek()
                if escaped == "":
                    raise LexError("Unterminated escape in string at L%d:%d" % (line, col))
                chars.append(escaped)
                self._advance()
                continue
            chars.append(ch)
            self._advance()
        return Token(TOK_STRING, "".join(chars), line, col)

    def _read_number(self):
        line, col = self.line, self.col
        digits = []
        while _is_digit(self._peek()):
            digits.append(self._peek())
            self._advance()
        return Token(TOK_NUMBER, int("".join(digits)), line, col)

    def _read_identifier(self):
        line, col = self.line, self.col
        chars = []
        while _is_tail(self._peek()):
            chars.append(self._peek())
            self._advance()
        name = "".join(chars)
        tok_type = KEYWORDS.get(name, TOK_ID)
        return Token(tok_type, name, line, col)

    def next_token(self):
        self._skip_whitespace()
        if self.pos >= len(self.source):
            return Token(TOK_EOF, "", self.line, self.col)

        ch = self._peek()
        line, col = self.line, self.col

        if ch == '"':
            return self._read_string()

        if _is_digit(ch):
            return self._read_number()

        if _is_head(ch):
            return self._read_identifier()

        if ch in SINGLE_CHAR_TOKENS:
            self._advance()
            return Token(SINGLE_CHAR_TOKENS[ch], ch, line, col)

        raise LexError("Unexpected character %r at L%d:%d" % (ch, line, col))

    def tokenize(self):
        tokens = []
        while True:
            tok = self.next_token()
            tokens.append(tok)
            if tok.type == TOK_EOF:
                break
        return tokens
