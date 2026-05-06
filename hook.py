# feynmanPatch/hook.py

import os
import traceback

from .config import load_config
from .exporter import export_all_diagrams
from .layout import optimize_layout
from .render_tex import render_tex
from .render_svg import render_svg
from .utils import ensure_dir, now_tag, safe_process_name, write_json, write_text


def _debug_print(config, text):
    if config.get("runtime", {}).get("debug", False):
        print("[feynmanPatch] %s" % text)


def _make_output_dir(config, amp):
    base_dir = config["output"]["base_dir"]

    proc = amp.get("process")
    try:
        process_name = proc.shell_string()
    except Exception:
        process_name = "unknown_process"

    tag = safe_process_name(process_name) + "_" + now_tag()
    outdir = os.path.join(base_dir, tag)
    ensure_dir(outdir)
    return outdir


def on_mg5_draw(interface, amp, diags, filename, model, options,
                selection="all", dtype="", raw_line="", draw_args=None):
    config = load_config()

    if not config.get("enabled", True):
        return

    if not config.get("trigger", {}).get("on_display_diagrams", True):
        return

    try:
        outdir = _make_output_dir(config, amp)
        _debug_print(config, "output dir: %s" % outdir)

        diagrams = export_all_diagrams(
            diags=diags,
            amp=amp,
            model=model,
            options=options,
            dtype=dtype
        )

        manifest = {
            "schema": "feynmanPatch.manifest.v1",
            "count": len(diagrams),
            "selection": selection,
            "diagram_type": dtype or "default",
            "source_eps_filename": filename,
            "files": []
        }

        for item in diagrams:
            item = optimize_layout(item, config)
            idx = item["diagram"]["index"]
            stem = "diagram_%04d" % idx

            json_name = stem + ".json"
            tex_name = stem + ".tex"
            svg_name = stem + ".svg"

            if config["output"].get("write_json", True):
                write_json(os.path.join(outdir, json_name), item)

            if config["output"].get("write_tex", True):
                tex_text = render_tex(item, config)
                write_text(os.path.join(outdir, tex_name), tex_text)

            if config["output"].get("write_svg", True):
                svg_text = render_svg(item, config)
                write_text(os.path.join(outdir, svg_name), svg_text)

            manifest["files"].append({
                "diagram_index": idx,
                "json": json_name if config["output"].get("write_json", True) else None,
                "tex": tex_name if config["output"].get("write_tex", True) else None,
                "svg": svg_name if config["output"].get("write_svg", True) else None
            })

        write_json(os.path.join(outdir, "manifest.json"), manifest)
        _debug_print(config, "generated %d diagram(s)" % len(diagrams))

    except Exception:
        if config.get("runtime", {}).get("fail_silently", True):
            if config.get("runtime", {}).get("debug", False):
                traceback.print_exc()
            return
        raise

