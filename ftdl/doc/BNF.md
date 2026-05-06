# FTDL BNF Grammar v0.2

## Lexical Tokens

```
ID       ::= HEAD TAIL*
HEAD     ::= letter | "_" | "+" | "-" | "~"
TAIL     ::= letter | digit | "_" | "+" | "-" | "~"
STRING   ::= '"' char* '"'
NUMBER   ::= digit+
```

Keywords: `import`, `particle`, `vertex`

## Syntax

```
<prog>      ::= <decls> <diagrams>

<decls>     ::= ε
              | <decl-item> ("," <decl-item>)*

<decl-item> ::= <imp>
              | <particle>
              | <vertex>

<diagrams>  ::= <diagram>
              | <diagrams> ";" <diagram>

<diagram>   ::= <stitem>
              | <diagram> "," <stitem>

<stitem>    ::= <proc>
              | <call>
              | <mproc>
```

### Import

```
<imp>       ::= "import" <id>
```

### Particle Declaration

```
<particle>  ::= <decos-opt> "particle" <id> "=" <pdef> <decos-opt>

<pdef>      ::= <string>
              | "{" <plist> "}"

<plist>     ::= <pitem>
              | <plist> "," <pitem>

<pitem>     ::= <id> | <string>
```

### Vertex Declaration

```
<vertex>    ::= <decos-opt> "vertex" <id> "[" <sig> "]" <decos-opt> <vbody-opt>

<vbody-opt> ::= "=" "{" <body> "}"
              | ε

<sig>       ::= <ty>
              | <sig> "," <ty>

<ty>        ::= <id>
              | "{" <ids> "}"

<ids>       ::= <id>
              | <ids> "," <id>

<body>      ::= <lstmt>
              | <body> "," <lstmt>

<lstmt>     ::= <lterm>
              | <lstmt> <lterm>

<lterm>     ::= <port> | <inst>
```

### Process Statements

```
<proc>      ::= <insts> ">" <insts>

<mproc>     ::= <insts> ">" <call> ">" <insts>

<call>      ::= <id> "[" <args> "]"

<args>      ::= <arg>
              | <args> "," <arg>

<arg>       ::= <num> | <id> | <port>
```

### Instances

```
<inst>      ::= <id> "(" <ref> ")"

<ref>       ::= <num> | <id>

<insts>     ::= <inst>
              | <insts> <inst>

<port>      ::= "[" <num> "]"
```

### Decorators

```
<decos-opt> ::= <decos> | ε

<decos>     ::= <deco>
              | <decos> <deco>

<deco>      ::= "@" <id>
```

## Decorator Reference

| Decorator  | Target   | Meaning                    | Line Style |
|------------|----------|----------------------------|------------|
| `@fermi`   | particle | Fermion (spin-1/2)        | straight + arrow |
| `@boson`   | particle | Vector boson (spin-1)     | wavy       |
| `@higgs`   | particle | Scalar (spin-0)           | dashed     |
| `@gluon`   | particle | Gluon                     | curly/coil |
| `@ghost`   | particle | Faddeev-Popov ghost       | dotted     |
| `@core`    | vertex   | Auto-matched SM vertex    | —          |
| `@point`   | vertex   | Explicit local vertex     | —          |
| `@blob`    | vertex   | Composite blob/loop vertex | —         |
| `@tchannel`| vertex   | T-channel special vertex  | —          |

## Diagram Composition Rules

- **`;`** separates independent diagrams. Each `;`-delimited block produces one output diagram.
- **`,`** within a `;`-block joins sub-processes into a single composite diagram.
- Shared particle instance numbers (e.g., `z(3)` appearing in multiple sub-processes) create connected vertices sharing an internal propagator.
- Unshared particle instance numbers become external legs of the composite diagram.

### Example: s-channel Z → μμ

```
e+(1) e-(2) > z(3), z(3) > mu+(4) mu-(5)
```

Two vertices connected by `z(3)` propagator. External legs: e+(1), e-(2), mu+(4), mu-(5).
