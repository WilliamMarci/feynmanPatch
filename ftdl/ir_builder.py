# feynmanPatch/ftdl/ir_builder.py

from .ast import (
    Program, Diagram, ImportStmt, ParticleDecl, ParticleDef,
    VertexDecl, ProcessStmt, MultiProcessStmt, CallExpr,
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

    def node_by_id(self, nid):
        for n in self.nodes:
            if n["id"] == nid:
                return n
        return None


DECO_LINE_MAP = {
    "fermi": ("straight", True),
    "boson": ("wavy", False),
    "higgs": ("dashed", False),
    "gluon": ("curly", False),
    "ghost": ("dotted", False),
}


class IRBuilder(object):

    def __init__(self, sema):
        self.sema = sema
        self.diagrams = []
        self._particle_props = {}
        self._vertex_map = {}

    def build(self):
        self._collect_particle_props()
        self._collect_vertex_map()

        for diag in self.sema.ast.diagrams:
            graph = self._build_diagram(diag)
            if graph:
                self.diagrams.append(graph)

        if not self.diagrams:
            for item in self.sema.ast.decls:
                pass
            for stmt_list in [[s] for s in self.sema.ast.items
                              if isinstance(s, (ProcessStmt, MultiProcessStmt, CallExpr))]:
                if stmt_list:
                    d = Diagram(stmt_list)
                    g = self._build_diagram(d)
                    if g:
                        self.diagrams.append(g)

        return self.diagrams

    def _collect_particle_props(self):
        for name, info in self.sema.symbols.items():
            if info.kind == "particle":
                node = info.node
                fermion = False
                line_type = "straight"
                for deco in node.decorators:
                    lt, f = DECO_LINE_MAP.get(deco, ("straight", False))
                    line_type = lt
                    fermion = f or fermion
                props = {"fermion": fermion, "line_type": line_type}
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
        return self._particle_props.get(name, {"fermion": False, "line_type": "straight"})

    def _build_diagram(self, diag):
        graph = DiagramGraph()
        graph.process_info = {"name": "diagram", "stmt": diag}

        instance_map = {}
        vertex_node_map = {}
        vertex_id_seq = 0

        for stmt in diag.stmts:
            if isinstance(stmt, ProcessStmt):
                self._add_process_to_graph(
                    graph, stmt, instance_map, vertex_node_map, vertex_id_seq)
                vertex_id_seq += 1
            elif isinstance(stmt, MultiProcessStmt):
                self._add_multiprocess_to_graph(
                    graph, stmt, instance_map, vertex_node_map, vertex_id_seq)
                vertex_id_seq += 1
            elif isinstance(stmt, CallExpr):
                self._add_call_to_graph(
                    graph, stmt, instance_map, vertex_node_map, vertex_id_seq)
                vertex_id_seq += 1

        edge_map = {}
        for ref, (node, inst_name, props) in instance_map.items():
            connections = set()
            for e in graph.edges:
                if e["from"] == node["id"]:
                    connections.add(e["to"])
                if e["to"] == node["id"]:
                    connections.add(e["from"])
            for conn_to in connections:
                key = tuple(sorted([node["id"], conn_to]))
                if key not in edge_map:
                    target = graph.node_by_id(conn_to)
                    if target and not target["external"]:
                        edge_map[key] = (node, inst_name, props)

        for key, (node, inst_name, props) in edge_map.items():
            a, b = key
            for e in graph.edges:
                if (e["from"] == a and e["to"] == b) or (e["from"] == b and e["to"] == a):
                    e.setdefault("label", inst_name)
                    if not e.get("label"):
                        e["label"] = inst_name
                    break

        self._deduplicate_edges(graph)
        self._update_external_status(graph)
        self._collapse_propagators(graph)
        self._update_external_status(graph)

        return graph

    def _update_external_status(self, graph):
        degree = {}
        for n in graph.nodes:
            degree[n["id"]] = 0
        for e in graph.edges:
            degree[e["from"]] = degree.get(e["from"], 0) + 1
            degree[e["to"]] = degree.get(e["to"], 0) + 1
        for n in graph.nodes:
            n["external"] = (degree[n["id"]] <= 1)
            if degree[n["id"]] >= 2 and not n.get("vertex_id", 0):
                n["external"] = False
                n["vertex_id"] = 0

    def _collapse_propagators(self, graph):
        int_ids = set(n["id"] for n in graph.nodes if not n["external"])
        changed = True
        while changed:
            changed = False
            degree = {}
            for e in graph.edges:
                degree[e["from"]] = degree.get(e["from"], 0) + 1
                degree[e["to"]] = degree.get(e["to"], 0) + 1

            propagators = []
            for n in graph.nodes:
                if n["external"]:
                    continue
                if n["vertex_id"] != 0:
                    continue
                if degree.get(n["id"], 0) != 2:
                    continue
                neighbors = []
                incident_edges = []
                for e in graph.edges:
                    if e["from"] == n["id"]:
                        neighbors.append(e["to"])
                        incident_edges.append(e)
                    elif e["to"] == n["id"]:
                        neighbors.append(e["from"])
                        incident_edges.append(e)
                if len(neighbors) == 2:
                    n1, n2 = neighbors
                    if n1 in int_ids and n2 in int_ids:
                        propagators.append((n, n1, n2, incident_edges))

            if propagators:
                changed = True
            for prop_node, n1, n2, incident_edges in propagators:
                label = prop_node["label"] or ""
                lt = "straight"
                ferm = False
                for old_e in incident_edges:
                    if old_e.get("label") and not label:
                        label = old_e["label"]
                    if old_e.get("line_type") and old_e.get("line_type") != "straight":
                        lt = old_e["line_type"]
                    if old_e.get("is_fermion"):
                        ferm = True

                graph.edges = [e for e in graph.edges if e not in incident_edges]
                graph.nodes = [n for n in graph.nodes if n["id"] != prop_node["id"]]

                new_edge = {
                    "id": "e%d" % (graph._edge_counter + 1),
                    "from": n1,
                    "to": n2,
                    "pdg": 0,
                    "number": 0,
                    "state": False,
                    "loop": False,
                    "external": False,
                    "is_fermion": ferm,
                    "line_type": lt,
                    "label": label,
                }
                graph._edge_counter += 1
                graph.edges.append(new_edge)
                graph._edge_counter = max(graph._edge_counter,
                                          max((int(e["id"][1:]) for e in graph.edges), default=0) + 1)

    def _is_external(self, node_id, graph):
        degree = 0
        for e in graph.edges:
            if e["from"] == node_id or e["to"] == node_id:
                degree += 1
        return degree <= 1

    def _find_connections(self, node_id, graph):
        conns = set()
        for e in graph.edges:
            if e["from"] == node_id:
                conns.add(e["to"])
            if e["to"] == node_id:
                conns.add(e["from"])
        return conns

    def _find_or_create_edge(self, graph, from_id, to_id, label, props, number, external=False):
        for e in graph.edges:
            if (e["from"] == from_id and e["to"] == to_id) or \
               (e["from"] == to_id and e["to"] == from_id):
                return e
        return graph.add_edge(
            from_node=graph.node_by_id(from_id),
            to_node=graph.node_by_id(to_id),
            label=label, fermion=props["fermion"],
            line_type=props["line_type"],
            number=number, external=external,
        )

    def _deduplicate_edges(self, graph):
        seen = {}
        unique = []
        for e in graph.edges:
            key = tuple(sorted([e["from"], e["to"]]))
            if key not in seen:
                seen[key] = e
                unique.append(e)
        graph.edges = unique

    def _get_or_create_instance_node(self, graph, inst, instance_map):
        ref = str(inst.ref)
        if ref in instance_map:
            return instance_map[ref][0]
        props = self._get_particle_props(inst.name)
        node = graph.add_node(external=True, label=inst.name)
        instance_map[ref] = (node, inst.name, props)
        return node

    def _get_or_create_vertex_node(self, graph, vid, vertex_node_map):
        key = "iv%d" % vid
        if key in vertex_node_map:
            return vertex_node_map[key]
        node = graph.add_node(external=False, vertex_id=vid + 1 if isinstance(vid, int) else 1)
        vertex_node_map[key] = node
        return node

    def _add_process_to_graph(self, graph, stmt, instance_map, vertex_node_map, vid):
        vnode = self._get_or_create_vertex_node(graph, vid, vertex_node_map)
        for inst in stmt.initial:
            inode = self._get_or_create_instance_node(graph, inst, instance_map)
            props = self._get_particle_props(inst.name)
            graph.add_edge(from_node=inode, to_node=vnode, label=inst.name,
                           fermion=props["fermion"], line_type=props["line_type"],
                           external=True, state=False)
        for inst in stmt.final:
            inode = self._get_or_create_instance_node(graph, inst, instance_map)
            props = self._get_particle_props(inst.name)
            graph.add_edge(from_node=vnode, to_node=inode, label=inst.name,
                           fermion=props["fermion"], line_type=props["line_type"],
                           external=True, state=True)

    def _add_multiprocess_to_graph(self, graph, stmt, instance_map, vertex_node_map, vid):
        vnode = self._get_or_create_vertex_node(graph, vid, vertex_node_map)
        for inst in stmt.initial:
            inode = self._get_or_create_instance_node(graph, inst, instance_map)
            props = self._get_particle_props(inst.name)
            graph.add_edge(from_node=inode, to_node=vnode, label=inst.name,
                           fermion=props["fermion"], line_type=props["line_type"],
                           external=True, state=False)
        for inst in stmt.final:
            inode = self._get_or_create_instance_node(graph, inst, instance_map)
            props = self._get_particle_props(inst.name)
            graph.add_edge(from_node=vnode, to_node=inode, label=inst.name,
                           fermion=props["fermion"], line_type=props["line_type"],
                           external=True, state=True)

    def _add_call_to_graph(self, graph, stmt, instance_map, vertex_node_map, vid):
        vnode = self._get_or_create_vertex_node(graph, vid, vertex_node_map)
        vnode["label"] = stmt.name
        vdecl = self._vertex_map.get(stmt.name)
        for i, arg in enumerate(stmt.args):
            arg_val = str(arg)
            sig_idx = min(i, len(vdecl.signature) - 1) if vdecl else i
            particle_name = arg_val
            if vdecl:
                parts = vdecl.signature[sig_idx].parts
                particle_name = parts[0] if parts else arg_val
            props = self._get_particle_props(particle_name)
            ext_node = graph.add_node(external=True, label=particle_name)
            graph.add_edge(from_node=vnode, to_node=ext_node, label=particle_name,
                           fermion=props["fermion"], line_type=props["line_type"],
                           external=True, state=True)
