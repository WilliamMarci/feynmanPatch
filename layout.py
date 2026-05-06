# feynmanPatch/layout.py

def optimize_layout(diagram_data, config):
    """
    第一版仅作为接口：
    - 默认保留 MadGraph convert_diagram 后的坐标
    - 可在这里做轻量修正
    """
    layout_cfg = config.get("layout", {})
    if not layout_cfg.get("optimize", False):
        return diagram_data

    # 这里先只保留接口，不做破坏性修改
    # 后续可以在此添加：
    # - 标签避让
    # - 边距修正
    # - 外线长度统一
    return diagram_data

