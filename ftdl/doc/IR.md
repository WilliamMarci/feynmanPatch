# FTDL Internal Representation

## AST (Abstract Syntax Tree)

The parser produces an AST with these node types:

```
Program
├── decls: list[ImportStmt | ParticleDecl | VertexDecl]
└── diagrams: list[Diagram]

Diagram
└── stmts: list[ProcessStmt | MultiProcessStmt | CallExpr]

ImportStmt
└── name: str

ParticleDecl
├── name: str
├── pdef: ParticleDef
└── decorators: list[str]

ParticleDef
└── value: str | list[str]

VertexDecl
├── name: str
├── signature: list[TypeRef]
├── decorators: list[str]
└── body: list[LStmt] | None

TypeRef
└── parts: list[str]

ProcessStmt
├── initial: list[Instance]
└── final: list[Instance]

MultiProcessStmt
├── initial: list[Instance]
├── call: CallExpr
└── final: list[Instance]

CallExpr
├── name: str
└── args: list[int | str | Port]

Instance
├── name: str
└── ref: int | str

Port
└── number: int
```

## Semantic Analysis Pass

The semantic analyzer (`sema.py`) performs:

1. **Declaration pass**: Build symbol table from `Program.decls`
   - Classify vertices by decorator (`@core`, `@point`, `@blob`, `@tchannel`)
2. **Resolution pass**: For each statement in each diagram:
   - Resolve process statements by matching against `@core` vertices
   - Resolve explicit calls against declared vertex names
   - Report ambiguities and missing matches

## DiagramGraph IR

The IR builder (`ir_builder.py`) converts each `Diagram` AST node to a `DiagramGraph`:

```
DiagramGraph
├── nodes: list[dict]
│   ├── id: str          # "v1", "v2", ...
│   ├── vertex_id: int   # 0 for external, >0 for internal
│   ├── external: bool
│   ├── level: int       # assigned by layout
│   ├── x: float         # [0,1] coordinate
│   ├── y: float         # [0,1] coordinate
│   └── label: str
└── edges: list[dict]
    ├── id: str          # "e1", "e2", ...
    ├── from: str        # node id
    ├── to: str          # node id
    ├── pdg: int         # PDG code (0 if unused)
    ├── number: int      # leg number
    ├── state: bool      # true=final, false=initial
    ├── loop: bool       # loop line flag
    ├── external: bool   # connected to external leg
    ├── is_fermion: bool  # draw arrow
    ├── line_type: str   # "straight" | "wavy" | "curly" | "dashed" | "dotted"
    └── label: str       # particle label
```

### Multi-Vertex Graph Construction

When a `Diagram` contains multiple comma-separated statements:

1. For each sub-statement, create an internal vertex node and edges to its particle instances
2. Particle instances with the same `ref` number map to the same node
3. After adding all sub-statements:
   - Nodes connected to ≤1 edge → external (leg)
   - Nodes connected to ≥2 edges → internal propagator
4. Final deduplication pass removes duplicate edges

## Layout Engine

The layout engine (`layout_engine.py`) computes (x,y) positions:

1. **External identification**: Separate external nodes into left (initial) and right (final) based on edge `state`
2. **External placement**: Left at x=0, right at x=1, evenly spaced in y
3. **Level assignment** (multi-vertex): BFS from vertices connected to left external nodes
4. **Internal placement**: x proportional to level / max_level, y centered
5. **Y-adjustment**: Pull internal vertices toward average y of their connected external nodes

## JSON Serialization

The diagram JSON schema (`diagram_json.py`) matches `feynmanPatch.diagram.v1`:

```json
{
  "schema": "feynmanPatch.diagram.v1",
  "process": {
    "input_string": "...",
    "nice_string": "...",
    "shell_string": "diagram_0001"
  },
  "diagram": {
    "index": 1,
    "type": "process",
    "orders": {}
  },
  "layout": {
    "source": "ftdl.compiler",
    "nodes": [...],
    "edges": [...]
  }
}
```
