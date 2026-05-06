# FTDL v0.1 — Feynman Diagram Language

## 概览

FTDL（Feynman Diagram Language）是一门用于声明式描述费曼图的领域特定语言。用户通过声明**粒子**、**顶点**和**过程语句**来构造费曼图的拓扑结构。

编译器将 FTDL 源码编译为 LLVM IR，并可以导出为 JSON、TikZ/TeX、SVG 和 PDF 格式。

## 快速开始

```bash
# 安装: 纯 Python stdlib, 无需 pip
cd feynmanPatch

# 编译为 LLVM IR
python -m ftdl example.ftdl

# 导出为 JSON (与 MadGraph 格式兼容)
python -m ftdl example.ftdl -f json

# 导出为 TeX / SVG / PDF
python -m ftdl example.ftdl -f tex
python -m ftdl example.ftdl -f svg
python -m ftdl example.ftdl -f pdf

# 一次性导出全部格式
python -m ftdl example.ftdl -f all

# TUI 交互式编辑器
python -m ftdl --tui example.ftdl
```

## 语法参考

### 程序结构

FTDL 程序由一组声明组成，声明之间用逗号 `,` 分隔：

```
<声明>, <声明>, ...
```

### Import 语句

```
import <模块名>
```

引入预定义的模型模块（如 `core`, `sm`）。

```
import core,
import sm
```

### 粒子声明

```
<装饰器>* particle <名称> = <定义>
```

- **名称**: 标识符，代表粒子/反粒子集合
- **定义**: 可以是字符串 `"name"` 或集合 `{p1, p2, ...}`
- **装饰器**: `@fermi`（费米子）, `@boson`（玻色子，波浪线）

```
particle u = {u} @fermi
particle q = {u, u~, d, d~} @fermi
particle g = {g} @boson
particle h = {h} @boson
particle b = {b, b~} @fermi
particle e = {e+, e-} @fermi
```

### 顶点声明

```
<装饰器>* vertex <名称> [<签名>] <装饰器>* (= { <体> })?
```

顶点分为四类，通过装饰器区分：

#### @core — 基础顶点

模型库中的基本相互作用顶点，**由普通过程语句自动匹配**，通常不需要显式调用。

```
vertex hbb [h, b, b~] @core
vertex gqq [g, q, q~] @core
vertex zll [z, l+, l-] @core
vertex hzz [h, z, z] @core
vertex hww [h, w+, w-] @core
```

当用户书写 `h(1) > b(2) b~(3)` 时，编译器自动查找匹配的 `@core` 顶点。

#### @point — 点顶点

显式局域点顶点，适用于 EFT、反常耦合等需显式指定的情形。

```
vertex hgg_eft [h, g, g] @point
vertex hzww [h, z, w+, w-] @point
vertex hza_anom [h, z, a] @point
```

调用方式：`hgg_eft[1,2,3]` 或 `h(1) > hgg_eft[1,2,3] > g(2) g(3)`。

#### @blob — 复合顶点（含内部结构）

用于 loop / blob 等具有内部拓扑的特殊顶点，需要定义体。

```
@blob
vertex ggzpLoop [g, g, zp] = {
  [1] q(a) q~(b),
  [2] q(b) q~(c),
  [3] q(c) q~(a)
}
```

- `[1]` `[2]` `[3]` 是端口号，对应签名中的粒子类型
- `q(a) q~(b)` 是局部顶点中的粒子线

#### @tchannel — T-道特殊顶点

```
@tchannel
vertex tchannelGamma [e+, e-, e+, e-]
```

### 过程语句

#### 普通过程

```
<粒子实例>* > <粒子实例>*
```

```
h(1) > b(2) b~(3)
e+(1) e-(2) > z(3)
g(1) g(2) > q(3) q~(4)
```

- `<粒子>(<编号>)` 指定外部粒子及其在费曼图中的腿编号
- 编译器自动在 `@core` 顶点中查找唯一匹配
- 若无匹配报错，多匹配报歧义错误

#### 显式顶点调用

```
<顶点名>[<参数>, ...]
```

```
hgg_eft[1,2,3]
ggzpLoop[1,2,3]
```

#### 多顶点过程（含顶点调用）

```
<粒子实例>* > <调用> > <粒子实例>*
```

```
e+(1) e-(2) > tchannelGamma[1,2,3,4] > e+(3) e-(4)
```

### 装饰器汇总

| 装饰器 | 用途 | 适用对象 |
|--------|------|----------|
| `@fermi` | 费米子（画箭头） | particle |
| `@boson` | 玻色子（波浪线） | particle |
| `@core` | 自动匹配基础顶点 | vertex |
| `@point` | 显式点顶点 | vertex |
| `@blob` | 复合/loop 顶点（需定义体） | vertex |
| `@tchannel` | T-道特殊顶点 | vertex |

### 顶点体的语法

顶点体定义局部拓扑：

```
{ <端口> <粒子线>*, ... }
```

端口格式：`[数字]`。粒子线格式：`<粒子>(<标签>)`。

```
{
  [1] q(a) q~(b),
  [2] q(b) q~(c),
  [3] q(c) q~(a)
}
```

## 完整示例

### SM Higgs → bb

```
import core,
particle h = {h} @boson,
particle b = {b, b~} @fermi,
vertex hbb [h, b, b~] @core,
h(1) > b(2) b~(3)
```

生成一个顶点的费曼图，顶点自动匹配到 `hbb`。

### QCD 双胶子 → 夸克对

```
import core,
particle q = {u, u~, d, d~} @fermi,
particle g = {g} @boson,
vertex gqq [g, q, q~] @core,
g(1) g(2) > q(3) q~(4)
```

### EFT Higgs → 双胶子

```
import core,
particle h = {h} @boson,
particle g = {g} @boson,
vertex hgg_eft [h, g, g] @point,
hgg_eft[1,2,3]
```

### T-道 Bhabha 散射

```
import core,
particle e = {e+, e-} @fermi,
@tchannel
vertex tgamma [e+, e-, e+, e-],
e+(1) e-(2) > tgamma[1,2,3,4] > e+(3) e-(4)
```

### 胶子融合 Loop 顶点

```
import core,
particle q = {u, u~, d, d~} @fermi,
@blob
vertex ggzpLoop [g, g, z] = {
  [1] q(a) q~(b),
  [2] q(b) q~(c),
  [3] q(c) q~(a)
},
ggzpLoop[1,2,3]
```

### 多顶点综合示例

```
import core,
import sm,
particle q = {u, u~, d, d~} @fermi,
particle e = {e+, e-} @fermi,
particle g = {g} @boson,
particle h = {h} @boson,
particle b = {b, b~} @fermi,
particle z = {z} @boson,
vertex hbb [h, b, b~] @core,
vertex gqq [g, q, q~] @core,
vertex zll [z, e+, e-] @core,
vertex hgg_eft [h, g, g] @point,
@blob
vertex ggzpLoop [g, g, z] = {
  [1] q(a) q~(b),
  [2] q(b) q~(c),
  [3] q(c) q~(a)
},
@tchannel
vertex tgamma [e+, e-, e+, e-],
h(1) > b(2) b~(3),
hgg_eft[1,2,3],
e+(1) e-(2) > tgamma[1,2,3,4] > e+(3) e-(4)
```

## 输出格式

### JSON

输出格式与 MadGraph `feynmanPatch.diagram.v1` 兼容：

```json
{
  "schema": "feynmanPatch.diagram.v1",
  "process": {"input_string": "h > b, b~", "nice_string": "Process: h > b, b~", "shell_string": "diagram_0001"},
  "diagram": {"index": 1, "type": "process", "orders": {}},
  "layout": {
    "source": "ftdl.compiler",
    "nodes": [{"id": "v1", "vertex_id": 0, "external": true, "level": 0, "x": 0.0, "y": 0.5}, ...],
    "edges": [{"id": "e1", "from": "v1", "to": "v4", "pdg": 0, "number": 1, "is_fermion": false, "line_type": "straight", "label": "h"}, ...]
  }
}
```

### LLVM IR

编译器生成标准 LLVM IR (.ll)，可由 `lli` 直接执行或 `llc` 编译为目标代码。

### TeX / TikZ

生成独立可编译的 TikZ 文档，使用 `pdflatex` 可直接生成 PDF。

### SVG

生成独立 SVG 图形，带有粒子标签和费米子箭头。

## 编译器架构

```
ftdl/
  tokens.py     — Token 定义
  lexer.py      — 词法分析器
  parser.py     — 递归下降解析器
  ast.py        — AST 节点
  sema.py       — 语义分析（符号表, @core 匹配）
  ir_builder.py — 图 IR 构造（AST → DiagramGraph）
  layout_engine.py — 节点布局（位置计算）
  diagram_json.py  — JSON 序列化
  llvm_ir.py    — LLVM IR 构造器（纯 Python）
  llvm_gen.py   — LLVM 代码生成
  render.py     — TeX / SVG 渲染
  compiler.py   — 编译器驱动
  tui.py        — TUI 前端（curses）
```

## 实现特点

- **纯 Python**: 零外部依赖, 仅使用 Python 标准库
- **LLVM IR 后端**: 自研 LLVM IR 构造器, 输出可执行的 .ll 文件
- **多格式导出**: JSON / TeX / SVG / PDF (通过 pdflatex)
- **@core 自动匹配**: 普通过程语句自动查找匹配顶点
- **TUI 编辑器**: curses 文本界面, 支持编译和导出快捷键
