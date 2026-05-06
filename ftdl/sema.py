# feynmanPatch/ftdl/sema.py

from .ast import (
    Program, ImportStmt, ParticleDecl, ParticleDef,
    VertexDecl, TypeRef, LStmt, Port, Instance,
    ProcessStmt, MultiProcessStmt, CallExpr,
)


class SemaError(Exception):
    pass


class SymbolInfo(object):

    def __init__(self, node, kind):
        self.node = node
        self.kind = kind


class SemanticAnalyzer(object):

    def __init__(self, ast):
        self.ast = ast
        self.symbols = {}
        self.core_vertices = []
        self.point_vertices = []
        self.blob_vertices = []
        self.tchannel_vertices = []
        self.imports = []
        self.diagnostics = []

    def _error(self, msg, node):
        raise SemaError("%s at L%d:%d" % (msg, node.line, node.col))

    def analyze(self):
        self._pass_declare()
        self._pass_resolve()
        return self

    def _pass_declare(self):
        for item in self.ast.items:
            if isinstance(item, ImportStmt):
                self.imports.append(item)
            elif isinstance(item, ParticleDecl):
                if item.name in self.symbols:
                    self._error("Duplicate particle %s" % item.name, item)
                self.symbols[item.name] = SymbolInfo(item, "particle")
            elif isinstance(item, VertexDecl):
                if item.name in self.symbols:
                    self._error("Duplicate vertex %s" % item.name, item)
                info = SymbolInfo(item, "vertex")
                self.symbols[item.name] = info
                self._classify_vertex(item)

    def _classify_vertex(self, vertex):
        for deco in vertex.decorators:
            if deco == "core":
                self.core_vertices.append(vertex)
                return
            elif deco == "point":
                self.point_vertices.append(vertex)
                return
            elif deco == "blob":
                self.blob_vertices.append(vertex)
                return
            elif deco == "tchannel":
                self.tchannel_vertices.append(vertex)
                return
        self.core_vertices.append(vertex)

    def _pass_resolve(self):
        for item in self.ast.items:
            if isinstance(item, ProcessStmt):
                self._resolve_process(item)
            elif isinstance(item, MultiProcessStmt):
                self._resolve_multi_process(item)
            elif isinstance(item, CallExpr):
                self._resolve_call(item)

    def _resolve_process(self, stmt):
        seq = self._extract_particle_seq(stmt)
        match, msg = self._match_core_vertex(seq)
        if match:
            stmt._resolved_vertex = match
            stmt._resolved_type = "core"
        elif msg:
            self.diagnostics.append(msg)
        else:
            self.diagnostics.append(
                "No @core vertex matches %s at L%d:%d" % (seq, stmt.line, stmt.col)
            )

    def _resolve_multi_process(self, stmt):
        call = stmt.call
        if call.name in self.symbols:
            info = self.symbols[call.name]
            if info.kind == "vertex":
                stmt._resolved_vertex = info.node
                stmt._resolved_type = "explicit"
            else:
                self.diagnostics.append(
                    "%s is not a vertex at L%d:%d" % (call.name, stmt.line, stmt.col)
                )
        else:
            self.diagnostics.append(
                "Vertex %s not found at L%d:%d" % (call.name, stmt.line, stmt.col)
            )

    def _resolve_call(self, call):
        if call.name not in self.symbols:
            self.diagnostics.append(
                "Unknown vertex %s at L%d:%d" % (call.name, call.line, call.col)
            )

    def _extract_particle_seq(self, stmt):
        seq = []
        for inst in stmt.initial:
            seq.append(inst.name)
        for inst in stmt.final:
            seq.append(inst.name)
        return seq

    def _match_core_vertex(self, seq):
        seq_set = set(seq)
        candidates = []
        for v in self.core_vertices:
            sig_parts = set()
            for tref in v.signature:
                for part in tref.parts:
                    sig_parts.add(part)
            if seq_set == sig_parts:
                candidates.append(v)

        if len(candidates) == 1:
            return candidates[0], None
        elif len(candidates) > 1:
            names = [v.name for v in candidates]
            return None, "Ambiguous: multiple @core vertices match %s: %s" % (seq, names)
        return None, None
