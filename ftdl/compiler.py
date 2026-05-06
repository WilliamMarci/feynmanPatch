# feynmanPatch/ftdl/compiler.py

import sys
import os

from .parser import parse_source
from .ast import ImportStmt, Program, Diagram
from .sema import SemanticAnalyzer
from .llvm_gen import generate_ir
from .ir_builder import IRBuilder
from .diagram_json import export_diagrams_json
from .layout_engine import LayoutEngine


class FTDLCompiler(object):

    def __init__(self, search_paths=None):
        self.source = ""
        self.ast = None
        self.sema = None
        self.ir = ""
        self.diagrams = []
        self.search_paths = search_paths or []
        self._loaded_imports = set()

    def _resolve_import(self, name):
        for sp in self.search_paths:
            path = os.path.join(sp, name + ".ftdl")
            if os.path.isfile(path):
                return path
        if hasattr(self, "_current_file"):
            dirname = os.path.dirname(self._current_file)
            path = os.path.join(dirname, name + ".ftdl")
            if os.path.isfile(path):
                return path
        path = name + ".ftdl"
        if os.path.isfile(path):
            return os.path.abspath(path)
        return None

    def _load_imports(self, ast, imported_set=None):
        if imported_set is None:
            imported_set = set()
        merged_decls = []
        merged_diags = []
        for item in ast.decls:
            if isinstance(item, ImportStmt):
                if item.name in imported_set:
                    continue
                path = self._resolve_import(item.name)
                if path is None:
                    continue
                imported_set.add(item.name)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        imp_source = f.read()
                    imp_ast = parse_source(imp_source)
                    d, diags = self._load_imports(imp_ast, imported_set)
                    merged_decls.extend(d)
                    merged_diags.extend(diags)
                except Exception:
                    pass
            else:
                merged_decls.append(item)
        merged_diags.extend(ast.diagrams)
        return merged_decls, merged_diags

    def compile_string(self, source, filename="<string>"):
        self.source = source
        self._current_file = filename
        self._loaded_imports = set()
        try:
            raw_ast = parse_source(source)
        except Exception as e:
            return {
                "success": False,
                "error": "Parse error: %s" % str(e)
            }
        if os.path.isfile(filename):
            self.search_paths.insert(0, os.path.dirname(os.path.abspath(filename)))
        else:
            self.search_paths.insert(0, ".")

        try:
            decls, diagrams = self._load_imports(raw_ast)
            self.ast = Program(decls, diagrams)
        except Exception as e:
            return {
                "success": False,
                "error": "Import error: %s" % str(e)
            }
        try:
            self.sema = SemanticAnalyzer(self.ast)
            self.sema.analyze()
        except Exception as e:
            return {
                "success": False,
                "ast": self.ast,
                "error": "Semantic error: %s" % str(e),
                "diagnostics": self.sema.diagnostics if self.sema else []
            }
        try:
            self.ir = generate_ir(self.sema)
        except Exception as e:
            return {
                "success": False,
                "ast": self.ast,
                "error": "Codegen error: %s" % str(e),
                "diagnostics": self.sema.diagnostics
            }
        try:
            builder = IRBuilder(self.sema)
            self.diagrams = builder.build()
        except Exception as e:
            return {
                "success": False,
                "ast": self.ast,
                "ir": self.ir,
                "error": "Diagram build error: %s" % str(e),
                "diagnostics": self.sema.diagnostics
            }
        return {
            "success": True,
            "ast": self.ast,
            "ir": self.ir,
            "diagrams": self.diagrams,
            "diagnostics": self.sema.diagnostics
        }

    def compile_file(self, path):
        if not os.path.isfile(path):
            return {"success": False, "error": "File not found: %s" % path}
        path = os.path.abspath(path)
        if not self.search_paths:
            self.search_paths.append(os.path.dirname(path))
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        return self.compile_string(source, filename=path)

    def compile_to_file(self, input_path, output_path=None):
        if output_path is None:
            output_path = os.path.splitext(input_path)[0] + ".ll"
        result = self.compile_file(input_path)
        if result["success"]:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result["ir"])
            result["output_path"] = output_path
        return result

    def export_json(self, diagrams=None):
        if diagrams is None:
            diagrams = self.diagrams
        return export_diagrams_json(diagrams)

    def export_tex(self, diagram_data, config=None):
        from .render import render_tex
        cfg = config or self._default_tex_config()
        return render_tex(diagram_data, cfg)

    def export_svg(self, diagram_data, config=None):
        from .render import render_svg
        cfg = config or self._default_svg_config()
        return render_svg(diagram_data, cfg)

    def _default_tex_config(self):
        return {
            "layout": {"canvas_width": 480, "canvas_height": 320},
            "tex": {"standalone": True, "label_mode": "particle", "show_diagram_id": True},
            "svg": {"font_size": 14, "stroke_width": 1.6, "particle_label": True, "vertex_radius": 2.2},
        }

    def _default_svg_config(self):
        return {
            "layout": {"canvas_width": 480, "canvas_height": 320},
            "svg": {"font_size": 14, "stroke_width": 1.6, "particle_label": True, "vertex_radius": 2.2},
            "tex": {},
        }
