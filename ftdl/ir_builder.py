# feynmanPatch/ftdl/ir_builder.py

from .ast import (
    Program, ImportStmt, ParticleDecl, ParticleDef,
    VertexDecl, TypeRef, LStmt, Port, Instance,
    ProcessStmt, MultiProcessStmt, CallExpr,
)


class DiagramGraph(object):

    def __init__(self):
        self.nodes = []
        self.edges = []
        self.process_info = {}
        self._node_counter = 0
        self._edge_counter = 0

    def add_node(self, external=False, vertex_id=None, label=None):
        self._node_counter += 1
        node = {
            "id": "v%d" % self._node_counter,
            "vertex_id": vertex_id if vertex_id is not None else 0,
            "external": external,
            "level": 0,
            "x": 0.0,
            "y": 0.0,
            "label": label,
        }
        self.nodes.append(node)
        return node

    def add_edge(self, from_node, to_node, label, fermion=False,
                 line_type="straight", pdg=0, number=0, state=False,
                 external=False, loop=False):
        self._edge_counter += 1
        edge = {
            "id": "e%d" % self._edge_counter,
            "from": from_node["id"],
            "to": to_node["id"],
            "pdg": pdg,
            "number": number,
            "state": state,
            "loop": loop,
            "external": external,
            "is_fermion": fermion,
            "line_type": line_type,
            "label": label,
        }
        self.edges.append(edge)
        return edge


class IRBuilder(object):

    def __init__(self, sema):
        self.sema = sema
        self.diagrams = []
        self._particle_props = {}
        self._vertex_map = {}

    def build(self):
        self._collect_particle_props()
        self._collect_vertex_map()

        for item in self.sema.ast.items:
            graph = None
            if isinstance(item, ProcessStmt):
                graph = self._build_process(item)
            elif isinstance(item, MultiProcessStmt):
                graph = self._build_multiprocess(item)
            elif isinstance(item, CallExpr):
                graph = self._build_call(item)
            if graph:
                self.diagrams.append(graph)
        return self.diagrams

    def _collect_particle_props(self):
        for name, info in self.sema.symbols.items():
            if info.kind == "particle":
                node = info.node
                fermion = False
                line_type = "straight"
                for deco in node.decorators:
                    if deco == "fermi":
                        fermion = True
                    elif deco == "boson":
                        line_type = "wavy"
                props = {
                    "fermion": fermion,
                    "line_type": line_type,
                }
                self._particle_props[name] = props
                pdef = node.pdef
                if isinstance(pdef.value, list):
                    for pname in pdef.value:
                        if isinstance(pname, str) and pname not in self._particle_props:
                            self._particle_props[pname] = props

    def _collect_vertex_map(self):
        for name, info in self.sema.symbols.items():
            if info.kind == "vertex":
                self._vertex_map[name] = info.node

    def _get_particle_props(self, name):
        return self._particle_props.get(name, {
            "fermion": False,
            "line_type": "straight",
        })

    def _label_from_decorators(self, decorators):
        for deco in decorators:
            if deco in ("fermi", "boson", "gluon"):
                return deco
        return None

    def _build_process(self, stmt):
        graph = DiagramGraph()
        graph.process_info = {"name": "process", "stmt": stmt}

        initial_nodes = []
        for i, inst in enumerate(stmt.initial):
            props = self._get_particle_props(inst.name)
            node = graph.add_node(external=True, label=inst.name)
            initial_nodes.append((node, inst, props))

        final_nodes = []
        for i, inst in enumerate(stmt.final):
            props = self._get_particle_props(inst.name)
            node = graph.add_node(external=True, label=inst.name)
            final_nodes.append((node, inst, props))

        vertex = graph.add_node(external=False, vertex_id=1)

        leg_num = 0
        for node, inst, props in initial_nodes:
            leg_num += 1
            graph.add_edge(
                from_node=node, to_node=vertex,
                label=inst.name,
                fermion=props["fermion"],
                line_type=props["line_type"],
                number=leg_num, state=False,
                external=True,
            )

        for node, inst, props in final_nodes:
            leg_num += 1
            graph.add_edge(
                from_node=vertex, to_node=node,
                label=inst.name,
                fermion=props["fermion"],
                line_type=props["line_type"],
                number=leg_num, state=True,
                external=True,
            )

        return graph

    def _build_multiprocess(self, stmt):
        graph = DiagramGraph()
        graph.process_info = {"name": "multiprocess", "stmt": stmt}

        initial_nodes = []
        for i, inst in enumerate(stmt.initial):
            props = self._get_particle_props(inst.name)
            node = graph.add_node(external=True, label=inst.name)
            initial_nodes.append((node, inst, props))

        call_vertex = graph.add_node(external=False, vertex_id=1,
                                     label=stmt.call.name)

        final_nodes = []
        for i, inst in enumerate(stmt.final):
            props = self._get_particle_props(inst.name)
            node = graph.add_node(external=True, label=inst.name)
            final_nodes.append((node, inst, props))

        leg_num = 0
        for node, inst, props in initial_nodes:
            leg_num += 1
            graph.add_edge(
                from_node=node, to_node=call_vertex,
                label=inst.name,
                fermion=props["fermion"],
                line_type=props["line_type"],
                number=leg_num, state=False,
                external=True,
            )

        for node, inst, props in final_nodes:
            leg_num += 1
            graph.add_edge(
                from_node=call_vertex, to_node=node,
                label=inst.name,
                fermion=props["fermion"],
                line_type=props["line_type"],
                number=leg_num, state=True,
                external=True,
            )

        return graph

    def _build_call(self, stmt):
        graph = DiagramGraph()
        graph.process_info = {"name": "call", "stmt": stmt}

        vertex = graph.add_node(external=False, vertex_id=1, label=stmt.name)

        vdecl = self._vertex_map.get(stmt.name)
        if vdecl:
            for i, arg in enumerate(stmt.args):
                arg_val = str(arg)
                sig_idx = min(i, len(vdecl.signature) - 1)
                sig_parts = vdecl.signature[sig_idx].parts
                particle_name = sig_parts[0] if sig_parts else arg_val

                props = self._get_particle_props(particle_name)
                ext_node = graph.add_node(external=True, label=particle_name)
                graph.add_edge(
                    from_node=vertex, to_node=ext_node,
                    label=particle_name,
                    fermion=props["fermion"],
                    line_type=props["line_type"],
                    number=i + 1, state=True,
                    external=True,
                )
        else:
            for i, arg in enumerate(stmt.args):
                arg_val = str(arg)
                ext_node = graph.add_node(external=True, label=arg_val)
                graph.add_edge(
                    from_node=vertex, to_node=ext_node,
                    label=arg_val, number=i + 1, state=True,
                    external=True,
                )

        return graph
