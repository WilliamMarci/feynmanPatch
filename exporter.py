# feynmanPatch/exporter.py

from madgraph.core.drawing import DiagramDrawer


def _node_id(index):
    return "v%s" % index


def _edge_id(index):
    return "e%s" % index


def _safe_get_process_strings(amp):
    process = amp.get("process")
    out = {
        "input_string": "",
        "nice_string": "",
        "shell_string": ""
    }
    if process is None:
        return out

    try:
        out["input_string"] = process.input_string()
    except Exception:
        pass

    try:
        out["nice_string"] = process.nice_string()
    except Exception:
        pass

    try:
        out["shell_string"] = process.shell_string()
    except Exception:
        pass

    return out


def _extract_orders(fd):
    try:
        orders = fd.diagram.diagram["orders"]
        return dict(orders)
    except Exception:
        return {}


def _line_style(line):
    try:
        return line.get_info("line")
    except Exception:
        return "straight"


def _line_label(line):
    try:
        return line.get_name()
    except Exception:
        return str(getattr(line, "id", ""))


def _particle_id(line):
    return getattr(line, "id", None)


def _is_fermion(line):
    try:
        return bool(line.is_fermion())
    except Exception:
        return False


def _is_external(line):
    try:
        return bool(line.is_external())
    except Exception:
        return False


def convert_single_diagram(raw_diag, amp, model, options, diagram_index, dtype=""):
    drawer = DiagramDrawer(model=model, amplitude=amp, opt=options)
    fd = drawer.convert_diagram(
        diagram=raw_diag,
        model=model,
        amplitude=amp,
        opt=options
    )

    if fd is None:
        return None

    node_map = {}
    nodes = []

    for i, vertex in enumerate(fd.vertexList, 1):
        nid = _node_id(i)
        node_map[id(vertex)] = nid
        nodes.append({
            "id": nid,
            "vertex_id": getattr(vertex, "id", None),
            "external": bool(vertex.is_external()),
            "level": getattr(vertex, "level", None),
            "x": float(getattr(vertex, "pos_x", 0.0)),
            "y": float(getattr(vertex, "pos_y", 0.0))
        })

    edges = []
    for i, line in enumerate(fd.lineList, 1):
        begin = getattr(line, "begin", None)
        end = getattr(line, "end", None)
        if begin is None or end is None:
            continue

        edges.append({
            "id": _edge_id(i),
            "from": node_map.get(id(begin)),
            "to": node_map.get(id(end)),
            "pdg": _particle_id(line),
            "number": getattr(line, "number", None),
            "state": getattr(line, "state", None),
            "loop": bool(getattr(line, "loop_line", False)),
            "external": _is_external(line),
            "is_fermion": _is_fermion(line),
            "line_type": _line_style(line),
            "label": _line_label(line)
        })

    proc = _safe_get_process_strings(amp)

    data = {
        "schema": "feynmanPatch.diagram.v1",
        "process": proc,
        "diagram": {
            "index": diagram_index,
            "type": dtype or "default",
            "orders": _extract_orders(fd)
        },
        "layout": {
            "source": "madgraph.convert_diagram",
            "nodes": nodes,
            "edges": edges
        }
    }

    return data


def export_all_diagrams(diags, amp, model, options, dtype=""):
    out = []
    for i, raw_diag in enumerate(diags, 1):
        item = convert_single_diagram(
            raw_diag=raw_diag,
            amp=amp,
            model=model,
            options=options,
            diagram_index=i,
            dtype=dtype
        )
        if item is not None:
            out.append(item)
    return out

