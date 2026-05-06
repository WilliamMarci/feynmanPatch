# FTDL Compiler Architecture

## Pipeline Overview

```
Source (.ftdl)
     │
     ▼
┌─────────┐
│  Lexer   │  lexer.py  —  tokenizes source into Token stream
└────┬────┘
     │ Token[]
     ▼
┌─────────┐
│  Parser  │  parser.py  —  recursive descent parser → AST
└────┬────┘
     │ Program { decls, diagrams }
     ▼
┌──────────────┐
│  Import Load │  compiler.py  —  resolve `import` statements, merge ASTs
└──────┬───────┘
     │ merged Program
     ▼
┌─────────┐
│  Sema    │  sema.py  —  symbol table, @core vertex matching, diagnostics
└────┬────┘
     │
     ├──────────────────────────────┐
     ▼                              ▼
┌──────────┐                 ┌──────────────┐
│ LLVM Gen  │ llvm_gen.py    │  IR Builder   │ ir_builder.py
│           │ llvm_ir.py     │               │
│   .ll    │                 │ DiagramGraph[]│
└──────────┘                 └──────┬───────┘
                                    │
                                    ▼
                             ┌──────────────┐
                             │ Layout Engine │ layout_engine.py
                             └──────┬───────┘
                                    │ positioned Graph
                                    ▼
                             ┌──────────────┐
                             │  JSON Export  │ diagram_json.py
                             └──────┬───────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              ┌──────────┐  ┌──────────┐   ┌──────────┐
              │ TeX Render│  │SVG Render│   │  PDF     │
              │ render.py │  │render.py │   │pdflatex  │
              └──────────┘  └──────────┘   └──────────┘
```

## Module Reference

| Module | Lines | Responsibility |
|--------|-------|----------------|
| `tokens.py` | 55 | Token types, KEYWORDS, SINGLE_CHAR_TOKENS |
| `lexer.py` | 124 | Character-level tokenizer, handles strings/numbers/ids |
| `parser.py` | 290 | Recursive descent parser implementing full BNF |
| `ast.py` | 104 | AST node classes |
| `sema.py` | 148 | Declaration resolution, vertex matching |
| `compiler.py` | 161 | Pipeline orchestrator, import resolution |
| `ir_builder.py` | 215 | DiagramGraph construction from multi-statement diagrams |
| `layout_engine.py` | 148 | Level-based graph layout |
| `diagram_json.py` | 92 | JSON export (`feynmanPatch.diagram.v1`) |
| `llvm_ir.py` | 205 | Pure Python LLVM IR builder (Module/Function/BasicBlock) |
| `llvm_gen.py` | 140 | AST → LLVM IR code generation |
| `render.py` | 196 | TikZ/TeX and SVG renderers |
| `tui.py` | 370 | curses TUI with vim modal editing |
| `__main__.py` | 190 | CLI entry point (-f json|tex|svg|pdf|ll|all) |
| `__init__.py` | 5 | Package exports |

## Design Principles

1. **Pure Python stdlib**: Zero external dependencies. All components (including LLVM IR builder, graph layout, SVG/TeX rendering) are self-contained.

2. **Separation of concerns**: Lexer → Parser → Sema → IR → JSON pipeline is cleanly separated with immutable intermediate representations.

3. **Matching MadGraph conventions**: JSON output uses identical `feynmanPatch.diagram.v1` schema. Level-based layout mirrors MadGraph's `FeynmanDiagram` positioning algorithm.

4. **Graceful degradation**: The TUI falls back to CLI mode when curses is unavailable. LLVM IR is validated via `lli` at integration test time.

## Import System

The compiler resolves `import` statements by searching:
1. The directory containing the importing file
2. All directories in `search_paths`
3. The current working directory

Imported files are parsed and merged: declarations are prepended, diagrams are appended. Circular and duplicate imports are detected and skipped.

## Diagram Composition

`;` delimits independent diagrams. `,` within a `;`-block joins sub-processes into one composite diagram. Shared particle numbers (e.g., `z(3)`) create connected vertices. The IR builder automatically:
- Creates one internal vertex per sub-process
- Merges shared particle instances
- Identifies external legs (degree 1) vs internal propagators (degree ≥ 2)
