# feynmanPatch/ftdl/diagram_json.py

from .layout_engine import LayoutEngine
from .ast import CallExpr


def diagram_to_json(graph, diagram_index=1, dtype="default",
                    process_info=None):
    engine = LayoutEngine(graph)
    engine.compute()

    nodes = []
    for node in graph.nodes:
        nodes.append({
            "id": node["id"],
            "vertex_id": node["vertex_id"],
            "external": node["external"],
            "level": node["level"],
            "x": node["x"],
            "y": node["y"],
        })

    edges = []
    for edge in graph.edges:
        edges.append({
            "id": edge["id"],
            "from": edge["from"],
            "to": edge["to"],
            "pdg": edge["pdg"],
            "number": edge["number"],
            "state": edge["state"],
            "loop": edge["loop"],
            "external": edge["external"],
            "is_fermion": edge["is_fermion"],
            "line_type": edge["line_type"],
            "label": edge["label"],
        })

    proc = {}
    if process_info:
        stmt = process_info.get("stmt")
        if stmt and hasattr(stmt, "line"):
            init_names = ", ".join(
                inst.name for inst in getattr(stmt, "initial", [])
            )
            final_names = ", ".join(
                inst.name for inst in getattr(stmt, "final", [])
            )
            if init_names and final_names:
                proc["input_string"] = "%s > %s" % (init_names, final_names)
                proc["nice_string"] = "Process: %s > %s" % (init_names, final_names)
            elif hasattr(stmt, "name") and isinstance(stmt, CallExpr):
                proc["input_string"] = "%s[%s]" % (
                    stmt.name, ", ".join(str(a) for a in stmt.args)
                )
                proc["nice_string"] = "Call: %s" % stmt.name
        proc.setdefault("input_string", "diagram")
        proc.setdefault("nice_string", "Process")
        proc.setdefault("shell_string", "diagram_%04d" % diagram_index)
    else:
        proc = {
            "input_string": "diagram",
            "nice_string": "Process",
            "shell_string": "diagram_%04d" % diagram_index,
        }

    return {
        "schema": "feynmanPatch.diagram.v1",
        "process": proc,
        "diagram": {
            "index": diagram_index,
            "type": dtype,
            "orders": {},
        },
        "layout": {
            "source": "ftdl.compiler",
            "nodes": nodes,
            "edges": edges,
        },
    }


def export_diagrams_json(graphs):
    results = []
    for i, graph in enumerate(graphs, 1):
        proc_info = getattr(graph, "process_info", {})
        result = diagram_to_json(
            graph, diagram_index=i, dtype=proc_info.get("name", "default"),
            process_info=proc_info,
        )
        results.append(result)
    return results
