# feynmanPatch/config.py

import json
import os


DEFAULT_CONFIG = {
    "enabled": True,
    "trigger": {"on_display_diagrams": True},
    "output": {
        "base_dir": "feynmanPatch/output",
        "write_json": True,
        "write_tex": True,
        "write_svg": True,
        "overwrite": True,
        "one_file_per_diagram": True,
    },
    "layout": {
        "engine": "madgraph",
        "optimize": False,
        "normalize": True,
        "canvas_width": 480,
        "canvas_height": 320,
    },
    "tex": {"standalone": True, "label_mode": "particle", "show_diagram_id": True},
    "svg": {
        "font_size": 14,
        "stroke_width": 1.6,
        "particle_label": True,
        "vertex_radius": 2.2,
    },
    "runtime": {"fail_silently": True, "debug": False},
}


def _deep_update(dst, src):
    for key, value in src.items():
        if isinstance(value, dict) and isinstance(dst.get(key), dict):
            _deep_update(dst[key], value)
        else:
            dst[key] = value
    return dst


def get_patch_root():
    return os.path.dirname(os.path.abspath(__file__))


def get_default_config_path():
    return os.path.join(get_patch_root(), "config.json")


def load_config():
    config = json.loads(json.dumps(DEFAULT_CONFIG))
    path = get_default_config_path()
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            user_cfg = json.load(f)
        _deep_update(config, user_cfg)
    return config
