# feynmanPatch/ftdl/__main__.py

import sys
import os
import json


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        _print_help()
        return

    if sys.argv[1] == "--tui":
        from .tui import FTDLTUI
        tui_args = sys.argv[2:]
        sys.argv = [sys.argv[0]] + tui_args
        tui = FTDLTUI()
        tui.main()
        return

    inpath = None
    fmt = "ll"
    outpath = None

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ("-o", "--output"):
            if i + 1 < len(sys.argv):
                outpath = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        elif arg in ("-f", "--format"):
            if i + 1 < len(sys.argv):
                fmt = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        elif arg.startswith("-"):
            i += 1
        else:
            inpath = arg
            i += 1

    if not inpath:
        print("Error: no input file specified")
        _print_help()
        sys.exit(1)

    from .compiler import FTDLCompiler
    compiler = FTDLCompiler()
    result = compiler.compile_file(inpath)

    if not result["success"]:
        print("compilation failed")
        print("Error: %s" % result.get("error", "unknown"))
        if result.get("diagnostics"):
            for d in result["diagnostics"]:
                print("WARNING: %s" % d)
        sys.exit(1)

    for d in result.get("diagnostics", []):
        print("WARNING: %s" % d)

    base = outpath or os.path.splitext(inpath)[0]

    if fmt == "ll":
        llpath = base + ".ll"
        with open(llpath, "w", encoding="utf-8") as f:
            f.write(result["ir"])
        print("compilation successful")
        print("LLVM IR written to: %s" % llpath)

    elif fmt == "json":
        diags = result.get("diagrams", [])
        if not diags:
            print("no diagrams generated")
            return
        json_data = compiler.export_json(diags)
        for i, d in enumerate(json_data):
            jpath = "%s_%04d.json" % (base, i + 1)
            with open(jpath, "w", encoding="utf-8") as f:
                json.dump(d, f, indent=2, sort_keys=False)
        print("exported %d diagram(s) to JSON" % len(json_data))

    elif fmt == "tex":
        diags = result.get("diagrams", [])
        if not diags:
            print("no diagrams generated")
            return
        json_data = compiler.export_json(diags)
        for i, d in enumerate(json_data):
            tex = compiler.export_tex(d)
            tpath = "%s_%04d.tex" % (base, i + 1)
            with open(tpath, "w", encoding="utf-8") as f:
                f.write(tex)
        print("exported %d diagram(s) to TeX" % len(json_data))

    elif fmt == "svg":
        diags = result.get("diagrams", [])
        if not diags:
            print("no diagrams generated")
            return
        json_data = compiler.export_json(diags)
        for i, d in enumerate(json_data):
            svg = compiler.export_svg(d)
            spath = "%s_%04d.svg" % (base, i + 1)
            with open(spath, "w", encoding="utf-8") as f:
                f.write(svg)
        print("exported %d diagram(s) to SVG" % len(json_data))

    elif fmt == "pdf":
        diags = result.get("diagrams", [])
        if not diags:
            print("no diagrams generated")
            return
        json_data = compiler.export_json(diags)
        for i, d in enumerate(json_data):
            tex = compiler.export_tex(d)
            tpath = "%s_%04d.tex" % (base, i + 1)
            with open(tpath, "w", encoding="utf-8") as f:
                f.write(tex)
            _compile_pdf(tpath)
        print("exported %d diagram(s) to PDF" % len(json_data))

    elif fmt == "all":
        diags = result.get("diagrams", [])
        if not diags:
            print("no diagrams generated")
            return
        json_data = compiler.export_json(diags)
        for i, d in enumerate(json_data):
            jpath = "%s_%04d.json" % (base, i + 1)
            with open(jpath, "w", encoding="utf-8") as f:
                json.dump(d, f, indent=2, sort_keys=False)
            tex = compiler.export_tex(d)
            tpath = "%s_%04d.tex" % (base, i + 1)
            with open(tpath, "w", encoding="utf-8") as f:
                f.write(tex)
            svg = compiler.export_svg(d)
            spath = "%s_%04d.svg" % (base, i + 1)
            with open(spath, "w", encoding="utf-8") as f:
                f.write(svg)
            _compile_pdf(tpath)
        print("exported %d diagram(s) to JSON + TeX + SVG + PDF" % len(json_data))


def _compile_pdf(tex_path):
    import subprocess
    workdir = os.path.dirname(tex_path) or "."
    basename = os.path.basename(tex_path)
    try:
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", basename],
            cwd=workdir, capture_output=True, timeout=30,
        )
        aux = os.path.splitext(tex_path)[0] + ".aux"
        log = os.path.splitext(tex_path)[0] + ".log"
        for f in [aux, log]:
            if os.path.isfile(f):
                os.remove(f)
    except Exception:
        pass


def _print_help():
    print("FTDL Compiler v0.1")
    print("Usage: python -m ftdl <command|file.ftdl> [options]")
    print()
    print("Commands:")
    print("  <file.ftdl>        Compile an FTDL source file to LLVM IR (.ll)")
    print("  --tui [file.ftdl]  Open the TUI editor/compiler")
    print()
    print("Options:")
    print("  -f, --format FMT   Output format: ll, json, tex, svg, pdf, all")
    print("                     Default: ll")
    print("  -o, --output PATH  Output file path (auto-generated if omitted)")
    print()
    print("Examples:")
    print("  python -m ftdl example.ftdl")
    print("  python -m ftdl example.ftdl -f json")
    print("  python -m ftdl example.ftdl -f pdf -o output")
    print("  python -m ftdl --tui example.ftdl")


if __name__ == "__main__":
    main()
