# feynmanPatch/ftdl/ast.py


class ASTNode(object):

    def __init__(self):
        self.line = 0
        self.col = 0

    def set_pos(self, token):
        self.line = token.line
        self.col = token.col
        return self


class Program(ASTNode):

    def __init__(self, items):
        super(Program, self).__init__()
        self.items = items


class ImportStmt(ASTNode):

    def __init__(self, name):
        super(ImportStmt, self).__init__()
        self.name = name


class ParticleDecl(ASTNode):

    def __init__(self, name, pdef, decorators):
        super(ParticleDecl, self).__init__()
        self.name = name
        self.pdef = pdef
        self.decorators = decorators


class ParticleDef(ASTNode):

    def __init__(self, value):
        super(ParticleDef, self).__init__()
        self.value = value


class VertexDecl(ASTNode):

    def __init__(self, name, signature, decorators, body):
        super(VertexDecl, self).__init__()
        self.name = name
        self.signature = signature
        self.decorators = decorators
        self.body = body


class TypeRef(ASTNode):

    def __init__(self, parts):
        super(TypeRef, self).__init__()
        self.parts = parts


class LStmt(ASTNode):

    def __init__(self, lterms):
        super(LStmt, self).__init__()
        self.lterms = lterms


class LTerm(ASTNode):
    pass


class Port(LTerm):

    def __init__(self, number):
        super(Port, self).__init__()
        self.number = number


class Instance(LTerm):

    def __init__(self, name, ref):
        super(Instance, self).__init__()
        self.name = name
        self.ref = ref


class ProcessStmt(ASTNode):

    def __init__(self, initial, final):
        super(ProcessStmt, self).__init__()
        self.initial = initial
        self.final = final


class MultiProcessStmt(ASTNode):

    def __init__(self, initial, call, final):
        super(MultiProcessStmt, self).__init__()
        self.initial = initial
        self.call = call
        self.final = final


class CallExpr(ASTNode):

    def __init__(self, name, args):
        super(CallExpr, self).__init__()
        self.name = name
        self.args = args


class Arg(ASTNode):

    def __init__(self, value):
        super(Arg, self).__init__()
        self.value = value
