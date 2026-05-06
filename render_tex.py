# feynmanPatch/render_tex.py

def _tex_escape_label(label):
    if label is None:
        return ""
    return str(label).replace("\\", "\\\\")


def _edge_style(edge):
    line_type = edge.get("line_type", "straight")
    is_fermion = edge.get("is_fermion", False)

    if line_type == "wavy":
        return "decorate, decoration={snake, amplitude=1.5mm, segment length=5mm}"
    if line_type == "curly":
        return "decorate, decoration={coil, aspect=0, segment length=4mm, amplitude=1.5mm}"
    if line_type == "dashed":
        return "dashed"
    if line_type == "dotted":
        return "dotted"

    if is_fermion:
        return "postaction={decorate}, decoration={markings, mark=at position 0.55 with {\\arrow{>}}}"

    return ""


def render_tex(diagram_data, config):
    nodes = diagram_data["layout"]["nodes"]
    edges = diagram_data["layout"]["edges"]
    did = diagram_data["diagram"]["index"]

    lines = []
    lines.append("\\documentclass[tikz,border=2pt]{standalone}")
    lines.append("\\usepackage{tikz}")
    lines.append("\\usetikzlibrary{decorations.pathmorphing,decorations.markings}")
    lines.append("\\begin{document}")
    lines.append("\\begin{tikzpicture}[x=8cm,y=6cm]")

    for node in nodes:
        lines.append(
            "\\coordinate (%s) at (%.6f,%.6f);" % (
                node["id"], node["x"], node["y"]
            )
        )

    for edge in edges:
        style = _edge_style(edge)
        if style:
            lines.append("\\draw[%s] (%s) -- (%s);" % (
                style, edge["from"], edge["to"]
            ))
        else:
            lines.append("\\draw (%s) -- (%s);" % (
                edge["from"], edge["to"]
            ))

    for node in nodes:
        if not node["external"]:
            lines.append("\\fill (%s) circle (1.2pt);" % node["id"])

    for edge in edges:
        label = _tex_escape_label(edge.get("label", ""))
        if label:
            lines.append("\\path (%s) -- (%s) node[midway, above] {$%s$};" % (
                edge["from"], edge["to"], label
            ))

    if config.get("tex", {}).get("show_diagram_id", True):
        lines.append("\\node at (0.5,-0.12) {diagram %s};" % did)

    lines.append("\\end{tikzpicture}")
    lines.append("\\end{document}")
    return "\n".join(lines)

