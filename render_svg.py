
# feynmanPatch/render_svg.py

import math

from .utils import normalize_xy


def _svg_header(width, height):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'width="{0}" height="{1}" viewBox="0 0 {0} {1}">'.format(width, height)
    )


def _arrow_polygon(x1, y1, x2, y2, size=7):
    dx = x2 - x1
    dy = y2 - y1
    norm = math.sqrt(dx * dx + dy * dy)
    if norm == 0:
        return ""
    ux = dx / norm
    uy = dy / norm

    mx = x1 + 0.55 * dx
    my = y1 + 0.55 * dy

    bx = mx - size * ux
    by = my - size * uy

    px = -uy
    py = ux

    p1 = (mx, my)
    p2 = (bx + 0.45 * size * px, by + 0.45 * size * py)
    p3 = (bx - 0.45 * size * px, by - 0.45 * size * py)

    return '{:.2f},{:.2f} {:.2f},{:.2f} {:.2f},{:.2f}'.format(
        p1[0], p1[1], p2[0], p2[1], p3[0], p3[1]
    )


def _simple_wave_path(x1, y1, x2, y2, amp=5, periods=6):
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx * dx + dy * dy)
    if length == 0:
        return "M %.2f %.2f" % (x1, y1)

    ux = dx / length
    uy = dy / length
    px = -uy
    py = ux

    points = []
    steps = max(8, periods * 4)
    for i in range(steps + 1):
        t = float(i) / steps
        base_x = x1 + dx * t
        base_y = y1 + dy * t
        offset = amp * math.sin(2 * math.pi * periods * t)
        px_i = base_x + px * offset
        py_i = base_y + py * offset
        points.append((px_i, py_i))

    d = ["M %.2f %.2f" % points[0]]
    for p in points[1:]:
        d.append("L %.2f %.2f" % p)
    return " ".join(d)


def _simple_curly_path(x1, y1, x2, y2, amp=5, periods=8):
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx * dx + dy * dy)
    if length == 0:
        return "M %.2f %.2f" % (x1, y1)

    ux = dx / length
    uy = dy / length
    px = -uy
    py = ux

    points = []
    steps = max(12, periods * 4)
    for i in range(steps + 1):
        t = float(i) / steps
        base_x = x1 + dx * t
        base_y = y1 + dy * t
        offset = amp * math.sin(2 * math.pi * periods * t)
        forward = 2.0 * math.cos(2 * math.pi * periods * t)
        px_i = base_x + px * offset + ux * forward
        py_i = base_y + py * offset + uy * forward
        points.append((px_i, py_i))

    d = ["M %.2f %.2f" % points[0]]
    for p in points[1:]:
        d.append("L %.2f %.2f" % p)
    return " ".join(d)


def render_svg(diagram_data, config):
    layout_cfg = config.get("layout", {})
    svg_cfg = config.get("svg", {})

    width = int(layout_cfg.get("canvas_width", 480))
    height = int(layout_cfg.get("canvas_height", 320))
    stroke_width = float(svg_cfg.get("stroke_width", 1.6))
    font_size = int(svg_cfg.get("font_size", 14))
    vertex_radius = float(svg_cfg.get("vertex_radius", 2.2))

    nodes = diagram_data["layout"]["nodes"]
    edges = diagram_data["layout"]["edges"]

    node_pos = {}
    for node in nodes:
        node_pos[node["id"]] = normalize_xy(node["x"], node["y"], width, height)

    out = []
    out.append(_svg_header(width, height))
    out.append('<defs>')
    out.append('</defs>')
    out.append('<rect x="0" y="0" width="{0}" height="{1}" fill="white"/>'.format(width, height))

    for edge in edges:
        x1, y1 = node_pos[edge["from"]]
        x2, y2 = node_pos[edge["to"]]

        line_type = edge.get("line_type", "straight")
        is_fermion = edge.get("is_fermion", False)

        if line_type == "wavy":
            d = _simple_wave_path(x1, y1, x2, y2)
            out.append(
                '<path d="{0}" fill="none" stroke="black" stroke-width="{1}"/>'.format(d, stroke_width)
            )
        elif line_type == "curly":
            d = _simple_curly_path(x1, y1, x2, y2)
            out.append(
                '<path d="{0}" fill="none" stroke="black" stroke-width="{1}"/>'.format(d, stroke_width)
            )
        elif line_type == "dashed":
            out.append(
                '<line x1="{0:.2f}" y1="{1:.2f}" x2="{2:.2f}" y2="{3:.2f}" '
                'stroke="black" stroke-width="{4}" stroke-dasharray="6,4"/>'.format(
                    x1, y1, x2, y2, stroke_width
                )
            )
        elif line_type == "dotted":
            out.append(
                '<line x1="{0:.2f}" y1="{1:.2f}" x2="{2:.2f}" y2="{3:.2f}" '
                'stroke="black" stroke-width="{4}" stroke-dasharray="2,4"/>'.format(
                    x1, y1, x2, y2, stroke_width
                )
            )
        else:
            out.append(
                '<line x1="{0:.2f}" y1="{1:.2f}" x2="{2:.2f}" y2="{3:.2f}" '
                'stroke="black" stroke-width="{4}"/>'.format(
                    x1, y1, x2, y2, stroke_width
                )
            )

        if is_fermion:
            pts = _arrow_polygon(x1, y1, x2, y2, size=7)
            if pts:
                out.append('<polygon points="{0}" fill="black"/>'.format(pts))

        if svg_cfg.get("particle_label", True):
            mx = (x1 + x2) / 2.0
            my = (y1 + y2) / 2.0 - 6
            label = edge.get("label", "")
            if label:
                out.append(
                    '<text x="{0:.2f}" y="{1:.2f}" font-size="{2}" '
                    'text-anchor="middle" fill="black">{3}</text>'.format(
                        mx, my, font_size, label
                    )
                )

    for node in nodes:
        if not node["external"]:
            x, y = node_pos[node["id"]]
            out.append(
                '<circle cx="{0:.2f}" cy="{1:.2f}" r="{2}" fill="black"/>'.format(
                    x, y, vertex_radius
                )
            )

    out.append('</svg>')
    return "\n".join(out)

