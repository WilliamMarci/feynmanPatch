# feynmanPatch/ftdl/parser.py

from .tokens import (
    TOK_EOF, TOK_ID, TOK_STRING, TOK_NUMBER,
    TOK_COMMA, TOK_EQUALS, TOK_GT,
    TOK_LBRACE, TOK_RBRACE, TOK_LBRACKET, TOK_RBRACKET,
    TOK_LPAREN, TOK_RPAREN, TOK_AT,
    TOK_IMPORT, TOK_PARTICLE, TOK_VERTEX,
)
from .ast import (
    Program, ImportStmt, ParticleDecl, ParticleDef,
    VertexDecl, TypeRef, LStmt, Port, Instance,
    ProcessStmt, MultiProcessStmt, CallExpr,
)


class ParseError(Exception):
    pass


class Parser(object):

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def _peek(self, offset=0):
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]

    def _advance(self):
        tok = self.tokens[self.pos]
        if tok.type != TOK_EOF:
            self.pos += 1
        return tok

    def _check(self, ttype):
        return self._peek().type == ttype

    def _match(self, ttype):
        if self._check(ttype):
            return self._advance()
        tok = self._peek()
        raise ParseError(
            "Expected %s but got %s at L%d:%d" % (ttype, tok.type, tok.line, tok.col)
        )

    def _match_if(self, ttype):
        if self._check(ttype):
            return self._advance()
        return None

    def _is_at_type(self):
        return self._check(TOK_IMPORT) or self._check(TOK_PARTICLE) or self._check(TOK_VERTEX)

    def _is_at_item_start(self):
        return self._check(TOK_AT) or self._is_at_type() or self._check(TOK_ID) or self._check(TOK_EOF)

    def _is_at_deco(self):
        return self._check(TOK_AT)

    def _is_at_lterm(self):
        return self._check(TOK_LBRACKET) or self._check(TOK_ID)

    def parse(self):
        items = self._parse_items()
        return Program(items)

    def _parse_items(self):
        items = []
        items.append(self._parse_item())
        while self._match_if(TOK_COMMA):
            if self._check(TOK_EOF):
                break
            items.append(self._parse_item())
        return items

    def _parse_item(self):
        decos = self._parse_decos()
        tok = self._peek()
        if tok.type == TOK_PARTICLE:
            return self._parse_particle(decos)
        elif tok.type == TOK_VERTEX:
            return self._parse_vertex(decos)
        elif tok.type == TOK_IMPORT:
            if decos:
                raise ParseError("Decorators not allowed on import at L%d:%d" % (tok.line, tok.col))
            return self._parse_import()
        elif tok.type == TOK_ID:
            if decos:
                raise ParseError("Decorators not allowed on statement at L%d:%d" % (tok.line, tok.col))
            return self._parse_stmt()
        elif tok.type == TOK_EOF:
            return None
        else:
            raise ParseError("Unexpected token %s at L%d:%d" % (tok.type, tok.line, tok.col))

    def _parse_import(self):
        tok = self._match(TOK_IMPORT)
        imp = ImportStmt(self._match(TOK_ID).lexeme)
        return imp.set_pos(tok)

    def _parse_decos(self):
        decos = []
        while self._is_at_deco():
            decos.append(self._parse_deco())
        return decos

    def _parse_deco(self):
        self._match(TOK_AT)
        return self._match(TOK_ID).lexeme

    def _parse_particle(self, decos):
        tok = self._match(TOK_PARTICLE)
        name = self._match(TOK_ID).lexeme
        self._match(TOK_EQUALS)
        pdef = self._parse_pdef()
        decos.extend(self._parse_decos())
        return ParticleDecl(name, pdef, decos).set_pos(tok)

    def _parse_pdef(self):
        if self._check(TOK_STRING):
            return ParticleDef(self._match(TOK_STRING).lexeme)
        else:
            self._match(TOK_LBRACE)
            plist = self._parse_plist()
            self._match(TOK_RBRACE)
            return ParticleDef(plist)

    def _parse_plist(self):
        items = [self._parse_pitem()]
        while self._match_if(TOK_COMMA):
            items.append(self._parse_pitem())
        return items

    def _parse_pitem(self):
        if self._check(TOK_ID):
            return self._match(TOK_ID).lexeme
        elif self._check(TOK_STRING):
            return self._match(TOK_STRING).lexeme
        else:
            tok = self._peek()
            raise ParseError("Expected id or string at L%d:%d" % (tok.line, tok.col))

    def _parse_vertex(self, decos):
        tok = self._match(TOK_VERTEX)
        name = self._match(TOK_ID).lexeme
        self._match(TOK_LBRACKET)
        sig = self._parse_signature()
        self._match(TOK_RBRACKET)

        decos.extend(self._parse_decos())

        body = None
        if self._match_if(TOK_EQUALS):
            self._match(TOK_LBRACE)
            body = self._parse_body()
            self._match(TOK_RBRACE)
        return VertexDecl(name, sig, decos, body).set_pos(tok)

    def _parse_signature(self):
        types = [self._parse_type()]
        while self._match_if(TOK_COMMA):
            types.append(self._parse_type())
        return types

    def _parse_type(self):
        if self._check(TOK_LBRACE):
            self._match(TOK_LBRACE)
            ids = [self._match(TOK_ID).lexeme]
            while self._match_if(TOK_COMMA):
                ids.append(self._match(TOK_ID).lexeme)
            self._match(TOK_RBRACE)
            return TypeRef(ids)
        else:
            return TypeRef([self._match(TOK_ID).lexeme])

    def _parse_body(self):
        body = []
        body.append(self._parse_lstmt())
        while self._match_if(TOK_COMMA):
            body.append(self._parse_lstmt())
        return body

    def _parse_lstmt(self):
        lterms = [self._parse_lterm()]
        while self._is_at_lterm():
            lterms.append(self._parse_lterm())
        return LStmt(lterms)

    def _parse_lterm(self):
        if self._check(TOK_LBRACKET):
            return self._parse_port()
        elif self._check(TOK_ID):
            return self._parse_instance()
        tok = self._peek()
        raise ParseError("Expected [ or id at L%d:%d" % (tok.line, tok.col))

    def _parse_port(self):
        tok = self._match(TOK_LBRACKET)
        num = self._match(TOK_NUMBER).lexeme
        self._match(TOK_RBRACKET)
        return Port(num).set_pos(tok)

    def _parse_instance(self):
        tok = self._match(TOK_ID)
        name = tok.lexeme
        self._match(TOK_LPAREN)
        ref = self._parse_ref()
        self._match(TOK_RPAREN)
        return Instance(name, ref).set_pos(tok)

    def _parse_ref(self):
        if self._check(TOK_NUMBER):
            return self._match(TOK_NUMBER).lexeme
        else:
            return self._match(TOK_ID).lexeme

    def _parse_stmt(self):
        saved = self.pos
        insts_left = self._parse_inst_list()
        if not self._match_if(TOK_GT):
            self.pos = saved
            return self._parse_call()

        if self._check(TOK_ID) and self._is_call_lookahead():
            call = self._parse_call()
            if self._match_if(TOK_GT):
                insts_right = self._parse_inst_list()
                return MultiProcessStmt(insts_left, call, insts_right)
            insts_right = self._parse_inst_list()
            return ProcessStmt(insts_left + [call], insts_right)

        insts_right = self._parse_inst_list()
        return ProcessStmt(insts_left, insts_right)

    def _parse_inst_list(self):
        insts = []
        while self._check(TOK_ID) and self._is_instance_next():
            insts.append(self._parse_instance())
        return insts

    def _is_instance_next(self):
        return (self.pos + 1 < len(self.tokens)
                and self.tokens[self.pos + 1].type == TOK_LPAREN)

    def _is_call_lookahead(self):
        p = self.pos
        return (p + 1 < len(self.tokens)
                and self.tokens[p].type == TOK_ID
                and self.tokens[p + 1].type == TOK_LBRACKET)

    def _parse_call(self):
        name = self._match(TOK_ID).lexeme
        self._match(TOK_LBRACKET)
        args = self._parse_args()
        self._match(TOK_RBRACKET)
        return CallExpr(name, args)

    def _parse_args(self):
        args = []
        args.append(self._parse_arg())
        while self._match_if(TOK_COMMA):
            args.append(self._parse_arg())
        return args

    def _parse_arg(self):
        if self._check(TOK_NUMBER):
            return self._match(TOK_NUMBER).lexeme
        elif self._check(TOK_ID):
            return self._match(TOK_ID).lexeme
        elif self._check(TOK_LBRACKET):
            tok = self._match(TOK_LBRACKET)
            num = self._match(TOK_NUMBER).lexeme
            self._match(TOK_RBRACKET)
            return Port(num).set_pos(tok)
        else:
            tok = self._peek()
            raise ParseError("Expected number, id, or port at L%d:%d" % (tok.line, tok.col))


def parse_source(source):
    from .lexer import Lexer
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()
