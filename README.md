# feynmanPatch

A lightweight MG5 plugin for exporting diagrams during `display diagrams`.

## Features

- Auto export on `display diagrams`
- JSON intermediate format
- TeX output
- SVG output
- Minimal MG5 patch
- Python standard library only

## Files

- `hook.py`: entry point called by patched MG5
- `exporter.py`: export MG diagram objects to JSON
- `layout.py`: layout optimization hook
- `render_tex.py`: JSON to TikZ/TeX
- `render_svg.py`: JSON to SVG

## Output

Generated files are written to:

- `feynmanPatch/output/...`

