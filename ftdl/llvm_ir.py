# feynmanPatch/ftdl/llvm_ir.py

import io as _io


class LLVMType(object):

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, LLVMType) and self.name == other.name

    def __hash__(self):
        return hash(self.name)


LLVM_VOID = LLVMType("void")
LLVM_I1 = LLVMType("i1")
LLVM_I8 = LLVMType("i8")
LLVM_I32 = LLVMType("i32")
LLVM_I64 = LLVMType("i64")
LLVM_F64 = LLVMType("double")
LLVM_I8PTR = LLVMType("i8*")


class PtrType(LLVMType):

    def __init__(self, pointee, addr_space=0):
        if isinstance(pointee, StructType):
            base = pointee.llvm_id()
        else:
            base = pointee.name
        super(PtrType, self).__init__(base + "*")
        self.pointee = pointee
        self.addr_space = addr_space

    def field_name(self):
        if isinstance(self.pointee, StructType):
            return self.pointee.llvm_id() + "*"
        return self.name


class ArrayType(LLVMType):

    def __init__(self, elem_type, size):
        super(ArrayType, self).__init__(f"[{size} x {elem_type.name}]")
        self.elem_type = elem_type
        self.size = size


class StructType(LLVMType):

    def __init__(self, name, fields):
        super(StructType, self).__init__(name)
        self.struct_name = name
        self.fields = fields

    def llvm_id(self):
        return "%" + self.struct_name


def ptr_type(typ):
    return PtrType(typ)


class LLVMValue(object):

    def __init__(self, name, typ):
        self.name = name
        self.typ = typ

    def __repr__(self):
        return f"{self.typ.name} {self.name}"


class BasicBlock(object):

    def __init__(self, label):
        self.label = label
        self.instructions = []

    def append(self, instr):
        self.instructions.append(instr)

    def write(self, buf):
        buf.write(f"{self.label}:\n")
        for instr in self.instructions:
            buf.write(f"  {instr}\n")


class Function(object):

    def __init__(self, name, ret_type, param_types):
        self.name = name
        self.ret_type = ret_type
        self.param_types = param_types
        self.blocks = []
        self._next_reg = 1

    def new_bb(self, label=None):
        if label is None:
            label = f"bb{len(self.blocks)}"
        block = BasicBlock(label)
        self.blocks.append(block)
        return block

    def fresh_name(self):
        n = self._next_reg
        self._next_reg += 1
        return f"%r{n}"

    def write(self, buf):
        params = []
        for i, pt in enumerate(self.param_types):
            params.append(f"{pt.name} %p{i}")
        param_str = ", ".join(params) if params else ""
        buf.write(f"define {self.ret_type.name} @{self.name}({param_str}) {{\n")
        for block in self.blocks:
            block.write(buf)
        buf.write("}\n")


class LLVMModule(object):

    def __init__(self, name="ftdl_module", triple="x86_64-unknown-linux-gnu"):
        self.name = name
        self.triple = triple
        self.struct_types = {}
        self.global_strings = {}
        self.functions = []
        self.declarations = []

    def add_struct(self, name, fields):
        st = StructType(name, fields)
        self.struct_types[name] = st
        return st

    def add_function(self, name, ret_type, param_types):
        func = Function(name, ret_type, param_types)
        self.functions.append(func)
        return func

    def add_declaration(self, name, ret_type, param_types):
        self.declarations.append((name, ret_type, param_types))

    def declare_global_string(self, key, value):
        self.global_strings[key] = value

    def write(self, buf):
        buf.write(f'; ModuleID = "{self.name}"\n')
        buf.write(f'target triple = "{self.triple}"\n')
        buf.write("\n")

        for stname in sorted(self.struct_types.keys()):
            st = self.struct_types[stname]
            field_strs = []
            for f in st.fields:
                if isinstance(f, PtrType):
                    field_strs.append(f.field_name())
                elif isinstance(f, StructType):
                    field_strs.append(f.llvm_id())
                else:
                    field_strs.append(f.name)
            buf.write(f"%{stname} = type {{ {', '.join(field_strs)} }}\n")
        buf.write("\n")

        for key in sorted(self.global_strings.keys()):
            value = self.global_strings[key]
            escaped = (value.replace("\\", "\\\\")
                             .replace("\"", "\\22")
                             .replace("\n", "\\0A"))
            buf.write(f'@.{key} = private unnamed_addr constant [{len(value) + 1} x i8] c"{escaped}\\00"\n')
        buf.write("\n")

        for name, ret, params in self.declarations:
            param_strs = [p.name for p in params]
            buf.write(f"declare {ret.name} @{name}({', '.join(param_strs)})\n")
        buf.write("\n")

        for func in self.functions:
            func.write(buf)
            buf.write("\n")

    def emit(self):
        buf = _io.StringIO()
        self.write(buf)
        return buf.getvalue()


def make_global_string(module, key, value):
    module.declare_global_string(key, value)
    return f"@.{key}"


def gep_string(func, block, global_ref, value_len):
    dest = func.fresh_name()
    base_type = f"[{value_len + 1} x i8]"
    block.append(
        f"{dest} = getelementptr {base_type}, {base_type}* {global_ref}, i32 0, i32 0"
    )
    return LLVMValue(dest, LLVM_I8PTR)
