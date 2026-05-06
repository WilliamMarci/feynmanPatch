# feynmanPatch/ftdl/llvm_gen.py

from .ast import (
    Program, ImportStmt, ParticleDecl, ParticleDef,
    VertexDecl, TypeRef, LStmt, Port, Instance,
    ProcessStmt, MultiProcessStmt, CallExpr,
)
from .llvm_ir import (
    LLVMModule, LLVMType, LLVMValue,
    LLVM_VOID, LLVM_I1, LLVM_I8, LLVM_I32, LLVM_I64, LLVM_F64,
    LLVM_I8PTR, PtrType, StructType,
    make_global_string, gep_string,
)


class LLVMCodeGen(object):

    def __init__(self, sema):
        self.sema = sema
        self.module = LLVMModule("ftdl_module")
        self._str_counter = 0
        self._diag_idx = 0

    def generate(self):
        self._declare_runtime()
        self._declare_struct_types()
        func = self.module.add_function("main", LLVM_I32, [])
        block = func.new_bb("entry")
        self._emit_header(func, block)
        self._emit_declarations(func, block)
        self._emit_diagrams(func, block)
        func.blocks[0].append("ret i32 0")
        return self.module

    def _declare_runtime(self):
        self.module.add_declaration("printf", LLVM_I32, [LLVM_I8PTR])

    def _declare_struct_types(self):
        node_fields = [LLVM_I32, LLVM_F64, LLVM_F64, LLVM_I8PTR]
        self.module.add_struct("FTDLNode", node_fields)

        edge_fields = [LLVM_I32, LLVM_I32, LLVM_I32, LLVM_I8PTR]
        self.module.add_struct("FTDLEdge", edge_fields)

        node_ptr = PtrType(self.module.struct_types["FTDLNode"])
        edge_ptr = PtrType(self.module.struct_types["FTDLEdge"])
        diag_fields = [node_ptr, LLVM_I32, edge_ptr, LLVM_I32, LLVM_I8PTR]
        self.module.add_struct("FTDLDiagram", diag_fields)

    def _emit_call_printf(self, func, block, value):
        key = f"str{self._str_counter}"
        self._str_counter += 1
        gref = make_global_string(self.module, key, value)
        gep = gep_string(func, block, gref, len(value))
        block_ref = func.blocks[0]
        dest = func.fresh_name()
        block_ref.append(f"{dest} = call i32 @printf(i8* {gep.name})")

    def _emit_header(self, func, block):
        self._emit_call_printf(func, block, "FTDL Diagram Output v0.1\\n")

    def _emit_declarations(self, func, block):
        for item in self.sema.ast.items:
            if not isinstance(item, (ImportStmt, ParticleDecl, VertexDecl)):
                continue
            label = None
            if isinstance(item, ImportStmt):
                label = f"Import module: {item.name}\\n"
            elif isinstance(item, ParticleDecl):
                pval = self._pdef_to_string(item.pdef)
                decos = " ".join(item.decorators) if item.decorators else ""
                label = f"Particle: {item.name} = {pval} @{decos}\\n"
            elif isinstance(item, VertexDecl):
                sig_str = self._sig_to_string(item.signature)
                decos = " ".join(item.decorators) if item.decorators else ""
                body_note = "(body)" if item.body else "(no body)"
                label = f"Vertex: {item.name} [{sig_str}] @{decos} {body_note}\\n"
            if label:
                self._emit_call_printf(func, block, label)

    def _pdef_to_string(self, pdef):
        if isinstance(pdef.value, str):
            return '"{}"'.format(pdef.value)
        elif isinstance(pdef.value, list):
            return "{{{}}}".format(", ".join(str(v) for v in pdef.value))
        return str(pdef.value)

    def _sig_to_string(self, sig):
        parts = []
        for tref in sig:
            if len(tref.parts) == 1:
                parts.append(tref.parts[0])
            else:
                parts.append("{{{}}}".format(", ".join(tref.parts)))
        return ", ".join(parts)

    def _emit_diagrams(self, func, block):
        for item in self.sema.ast.items:
            if isinstance(item, ProcessStmt):
                self._emit_process(func, block, item)
            elif isinstance(item, MultiProcessStmt):
                self._emit_multi_process(func, block, item)
            elif isinstance(item, CallExpr):
                self._emit_call(func, block, item)

    def _emit_process(self, func, block, stmt):
        self._diag_idx += 1
        diag_num = self._diag_idx
        init_parts = ", ".join(inst.name for inst in stmt.initial)
        final_parts = ", ".join(inst.name for inst in stmt.final)
        vname = getattr(stmt, "_resolved_vertex", None)
        vinfo = ""
        if vname and hasattr(vname, "name"):
            vinfo = f" (matched: {vname.name})"
        else:
            vinfo = " (no @core match)"
        label = f"[Diagram {diag_num}] {init_parts} > {final_parts}{vinfo}\\n"
        self._emit_call_printf(func, block, label)

    def _emit_multi_process(self, func, block, stmt):
        self._diag_idx += 1
        diag_num = self._diag_idx
        init_parts = ", ".join(inst.name for inst in stmt.initial)
        final_parts = ", ".join(inst.name for inst in stmt.final)
        call_name = stmt.call.name
        label = f"[Diagram {diag_num}] {init_parts} > {call_name}[...] > {final_parts}\\n"
        self._emit_call_printf(func, block, label)

    def _emit_call(self, func, block, stmt):
        self._diag_idx += 1
        diag_num = self._diag_idx
        args_str = ", ".join(str(a) for a in stmt.args)
        label = f"[Diagram {diag_num}] call {stmt.name}[{args_str}]\\n"
        self._emit_call_printf(func, block, label)


def generate_ir(sema):
    gen = LLVMCodeGen(sema)
    llvm_module = gen.generate()
    return llvm_module.emit()
