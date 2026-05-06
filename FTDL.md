下面给出一个**简洁命名**的 FTDL v0.1 风格 BNF/近似 BNF。  
我会尽量保持：

- **名字短**
- **结构清晰**
- **覆盖当前讨论过的核心语法**
- 同时区分：
  - `particle`
  - `vertex`
  - `import`
  - 过程语句
  - 顶点调用
  - 装饰器
  - `@core / @point / @blob / @tchannel`
  - 有/无定义体的顶点

> 说明：  
> 下面更接近 **EBNF 风格的 BNF**，因为纯 BNF 写列表会很冗长。  
> 若你需要，我后面也可以再给你一份**严格纯 BNF 版本**。

---

# FTDL BNF

````text
<prog> ::= <items>

<items> ::= <item>
          | <items> "," <item>

<item> ::= <imp>
         | <particle>
         | <vertex>
         | <stmt>

<imp> ::= "import" <id>

<particle> ::= <decos> "particle" <id> "=" <pdef> <decos>
             | "particle" <id> "=" <pdef> <decos>
             | <decos> "particle" <id> "=" <pdef>
             | "particle" <id> "=" <pdef>

<pdef> ::= <str>
         | "{" <plist> "}"

<plist> ::= <pitem>
          | <plist> "," <pitem>

<pitem> ::= <id>
          | <str>

<vertex> ::= <decos> "vertex" <id> "[" <sig> "]" <decos> "=" "{" <body> "}"
           | "vertex" <id> "[" <sig> "]" <decos> "=" "{" <body> "}"
           | <decos> "vertex" <id> "[" <sig> "]" "=" "{" <body> "}"
           | "vertex" <id> "[" <sig> "]" "=" "{" <body> "}"
           | <decos> "vertex" <id> "[" <sig> "]" <decos>
           | "vertex" <id> "[" <sig> "]" <decos>
           | <decos> "vertex" <id> "[" <sig> "]"
           | "vertex" <id> "[" <sig> "]"

<sig> ::= <ty>
        | <sig> "," <ty>

<ty> ::= <id>
       | "{" <ids> "}"

<ids> ::= <id>
        | <ids> "," <id>

<body> ::= <lstmts>
         | ε

<lstmts> ::= <lstmt>
           | <lstmts> "," <lstmt>

<lstmt> ::= <lterm>
          | <lstmt> <lterm>

<lterm> ::= <port>
          | <inst>
          | <call>

<stmt> ::= <proc>
         | <call>
         | <mproc>

<proc> ::= <insts> ">" <insts>

<mproc> ::= <insts> ">" <call> ">" <insts>

<insts> ::= <inst>
          | <insts> <inst>

<call> ::= <id> "[" <args> "]"

<args> ::= <arg>
         | <args> "," <arg>

<arg> ::= <num>
        | <id>
        | <port>

<inst> ::= <id> "(" <ref> ")"

<ref> ::= <num>
        | <id>

<port> ::= "[" <num> "]"

<decos> ::= <deco>
          | <decos> <deco>

<deco> ::= "@" <id>

<id> ::= <name>

<num> ::= <digit>
        | <num> <digit>

<name> ::= <head>
         | <name> <tail>

<head> ::= <letter>
         | "_"
         | "+"
         | "-"
         | "~"

<tail> ::= <letter>
         | <digit>
         | "_"
         | "+"
         | "-"
         | "~"

<str> ::= "\"" <chars> "\""
````

---

# 说明

## 1. 这个版本支持的东西
它支持：

- `import core`
- `particle u = {"u"} @fermi`
- `particle q = {u, u~, d, d~} @fermi`
- `vertex hbb [h, b, b~] @core`
- `vertex hgg [h, g, g] @point`
- `@blob vertex ggzpLoop [g, g, zp] = { ... }`
- `h(1) > b(2) b~(3)`
- `ggzpLoop[1,2,3]`
- `e+(1) e-(2) > tchannelGamma[1,2,3,4] > e+(3) e-(4)`

---

## 2. `<vertex>` 写得比较长的原因
因为当前语法允许：

- 装饰器在前
- 装饰器在后
- 有定义体
- 无定义体

如果你想让 BNF 更干净，我建议**冻结一种规范写法**，例如：

- 装饰器只允许在前
- `vertex` 只允许两种形式：
  - 有体
  - 无体

这样会简洁很多。

例如可以收紧成：

````text
<vertex> ::= <decos_opt> "vertex" <id> "[" <sig> "]" <vtail>

<vtail> ::= "=" "{" <body> "}"
          | ε

<decos_opt> ::= <decos>
              | ε
````

这会漂亮很多。

---

## 3. `<lstmt>` 这里目前是“局部顶点参与者串”
也就是支持：

```text
[1] q(a) q~(b)
```

这被解析为：

- 一个 `<lstmt>`
- 内含多个 `<lterm>`

---

## 4. `<call>` 参数里允许 `<port>`
这是为了给未来“定义体内嵌套调用”预留。  
如果你现在想严格限制 v0.1，不支持嵌套定义调用，可以把：

```text
<arg> ::= <num> | <id> | <port>
```

改成主图版本：

```text
<arg> ::= <num>
```

这样更严格。

---

# 更推荐的“规范化 BNF”

如果你想要更像标准语言规范，我建议直接采用一个**更干净的规范版**，即限制装饰器只放前面。  
这样会显著简化语法。

---

## 规范化版本

````text
<prog> ::= <items>

<items> ::= <item>
          | <items> "," <item>

<item> ::= <imp>
         | <particle>
         | <vertex>
         | <stmt>

<imp> ::= "import" <id>

<particle> ::= <decos_opt> "particle" <id> "=" <pdef>

<pdef> ::= <str>
         | "{" <plist> "}"

<plist> ::= <pitem>
          | <plist> "," <pitem>

<pitem> ::= <id>
          | <str>

<vertex> ::= <decos_opt> "vertex" <id> "[" <sig> "]" <vbody_opt>

<vbody_opt> ::= "=" "{" <body_opt> "}"
              | ε

<sig> ::= <ty>
        | <sig> "," <ty>

<ty> ::= <id>
       | "{" <ids> "}"

<ids> ::= <id>
        | <ids> "," <id>

<body_opt> ::= <body>
             | ε

<body> ::= <lstmt>
         | <body> "," <lstmt>

<lstmt> ::= <lterm>
          | <lstmt> <lterm>

<lterm> ::= <port>
          | <inst>

<stmt> ::= <proc>
         | <call>
         | <mproc>

<proc> ::= <insts> ">" <insts>

<mproc> ::= <insts> ">" <call> ">" <insts>

<insts> ::= <inst>
          | <insts> <inst>

<call> ::= <id> "[" <args> "]"

<args> ::= <arg>
         | <args> "," <arg>

<arg> ::= <num>

<inst> ::= <id> "(" <ref> ")"

<ref> ::= <num>
        | <id>

<port> ::= "[" <num> "]"

<decos_opt> ::= <decos>
              | ε

<decos> ::= <deco>
          | <decos> <deco>

<deco> ::= "@" <id>
````

---

# 我建议你最终采用哪个版本

我建议你在正式规范里采用上面这个**规范化版本**，原因是：

- 更像正式技术规范
- 更容易写 parser
- 更容易写 AST
- 更利于以后扩展
- 命名已经足够简洁

---

如果你愿意，我下一步可以继续给你补两样东西之一：

1. **把这份 BNF 改写成严格纯 BNF**
2. **给这份 BNF 配套 AST 节点表**

如果你要继续推进实现，我更推荐下一步做：

# 《FTDL v0.1 语言规范草案》修订建议：基础顶点与点顶点机制

## 1. 问题陈述

当前草案对 `vertex` 的理解偏向于：

- **复合顶点模板**
- **带接口的可调用结构**
- **用于 loop / blob / t-channel 等特殊拓扑**

但这不足以覆盖物理学家日常使用中更基础、也更常见的一类对象：

> **理论模型中预定义的“基本相互作用顶点”**

例如标准模型中的：
- $$H \to b \bar b$$
- $$Z \to \mu^+ \mu^-$$
- $$W \to \ell \nu$$
- $$HZZ$$
- $$HWW$$
- QCD 的 $$g q \bar q$$、$$g g g$$、$$g g g g$$

在这些情况下，用户在主图书写时通常不会希望显式写：
- “调用哪个顶点模板”
- “接口顺序是什么”
- “这个顶点实例名是什么”

用户更希望直接写过程：

```text
h(1) > b(2) b~(3)
```

然后系统根据已导入模型库自动匹配：
- 是否存在允许的顶点类型
- 对应的耦合对象
- 对应的渲染语义
- 对应的振幅规则

因此，FTDL 需要在现有“复合顶点模板”之外，再引入：

1. **模型基础顶点**
2. **显式点顶点**
3. **自动匹配与显式调用并存机制**

---

# 2. 设计目标

修订后的语言设计应满足：

## 2.1 对普通物理过程
用户可以只写：
```text
h(1) > b(2) b~(3)
```
由系统自动匹配到某个模型中的基础顶点。

## 2.2 对反常耦合 / EFT / 高阶有效点
用户既可以：
- 让系统自动匹配
- 也可以显式指定某个点顶点对象

例如：
```text
h(1) > z(2) z(3)
```
由系统自动选择标准模型 `hzz`

或显式指定：
```text
h(1) > hzww[1,2,3,4] > ...
```

## 2.3 对 loop / blob / 特殊拓扑
继续保留已有的复合顶点机制。

---

# 3. 新的顶点分类

建议在 FTDL 中将“顶点”分为三类。

---

## 3.1 基础顶点（core vertex）
表示模型库中预定义的基本相互作用顶点。

### 特征
- 由模型包提供
- 用户通常**不显式调用**
- 通过普通过程语句自动匹配
- 语义上是“一个点”

例如：
```text
vertex hbb [h, b, b~] @core
vertex zll [z, l+, l-] @core
vertex gqq [g, q, q~] @core
```

其中：
- `@core` 表示这是模型自动匹配顶点
- 它通常不需要定义体
- 它主要用于模型规则、类型检查、振幅规则、导出语义

---

## 3.2 点顶点（point vertex）
表示一个应在图上渲染为“单点”的顶点对象，但它不一定是模型自动匹配的基础顶点。

适用于：
- EFT 顶点
- 反常耦合
- 用户自定义高阶局域相互作用
- 需要显式区分的点相互作用

例如：
```text
vertex hzww [h, z, w, w] @point
```

### 特征
- 渲染上是单点
- 可以显式调用
- 可以不写定义体
- 通常由用户主动指定使用

---

## 3.3 复合顶点（composite vertex）
即当前已有的：
- `@blob`
- `@tchannel`
- loop 顶点
- 复合模板顶点

例如：
```text
@blob
vertex ggzpLoop [g, g, zp] = {
  [1] q(a) q~(b),
  [2] q(b) q~(c),
  [3] q(c) q~(a)
}
```

---

# 4. 建议的语义修正

核心修正如下：

## 4.1 普通过程语句不再只是“普通顶点”
而是：

> **一个待匹配的局部相互作用声明**

例如：
```text
h(1) > b(2) b~(3)
```

语义不再只是“构造一个匿名普通顶点”，而是：

1. 读取参与粒子类型：`h, b, b~`
2. 在已导入模型中查找满足匹配条件的基础顶点 `@core`
3. 若唯一匹配，则绑定该顶点规则
4. 若无匹配，报错
5. 若多重匹配，报歧义错误或要求显式指定

---

## 4.2 显式点顶点调用作为补充机制
对于不希望自动匹配、或者需要指定特殊耦合对象的情况，允许显式调用 `@point` 顶点。

例如：
```text
anomHZZ[1,2,3]
```

或过程式写法：
```text
h(1) > anomHZZ[1,2,3] > z(2) z(3)
```

---

# 5. 对语法的最小改动建议

为了兼容现有设计，建议不推翻原有 `vertex` 语法，而是增加**顶点类别装饰器**。

---

## 5.1 新增装饰器种类

### `@core`
表示：
- 模型库中的自动匹配基础顶点
- 通常不显式调用
- 由普通过程语句自动解析到它

### `@point`
表示：
- 一个单点顶点
- 通常需要显式调用
- 渲染上是局域点
- 可用于 EFT / 反常耦合 / 自定义接触项

### 已有装饰器继续保留
- `@blob`
- `@tchannel`

于是顶点的渲染/语义类别大致变为：

- `@core`
- `@point`
- `@blob`
- `@tchannel`

---

# 6. 顶点定义语法的扩展

## 6.1 基础顶点
基础顶点可以只声明签名，不写定义体：

```text
vertex hbb [h, b, b~] @core
vertex hzz [h, z, z] @core
vertex hww [h, w+, w-] @core
vertex gqq [g, q, q~] @core
```

这里：
- `[h, b, b~]` 是参与粒子类型签名
- `@core` 声明其为自动匹配顶点
- 不需要接口体，也不需要显式调用

---

## 6.2 显式点顶点
点顶点也可只声明签名：

```text
vertex hzww [h, z, w+, w-] @point
vertex hza_anom [h, z, a] @point
vertex hgg_eft [h, g, g] @point
```

这类顶点默认：
- 不自动匹配，除非实现明确允许
- 用于显式调用

---

## 6.3 复合顶点保持现状
```text
@blob
vertex ggzpLoop [g, g, zp] = {
  [1] q(a) q~(b),
  [2] q(b) q~(c),
  [3] q(c) q~(a)
}
```

---

# 7. 对主图语句语义的修订

## 7.1 普通过程语句
形式：
```text
particle_list > particle_list
```

修订后语义：
- 该语句表示一个**待匹配的局部相互作用**
- 实现应优先在当前导入模型中查找 `@core` 顶点
- 若存在唯一匹配，则将该语句绑定到该基础顶点
- 若无匹配，则可退化为“匿名普通顶点”或报错；建议 v0.1 报错
- 若有多个匹配，则报歧义错误

### 例子
```text
h(1) > b(2) b~(3)
```
匹配：
```text
vertex hbb [h, b, b~] @core
```

---

## 7.2 显式点顶点语句
形式可保留原有顶点调用：

```text
hgg_eft[1,2,3]
```

或过程式糖衣：

```text
h(1) > hgg_eft[1,2,3] > g(2) g(3)
```

建议语义：
- 该语句直接绑定到指定 `@point` 顶点
- 不做自动匹配替换

---

## 7.3 复合顶点语句
保持现有：
```text
ggzpLoop[1,2,3]
```

或：
```text
e+(1) e-(2) > tchannelGamma[1,2,3,4] > e+(3) e-(4)
```

---

# 8. 接口的重新解释

你提出：

> `@point` 语法上就不需要定义接口，而 `@core` 也不需要在过程式中显式指定。

这个方向是合理的。  
因此需要将当前 `[ ... ]` 的语义从“接口”推广成更一般的：

> **有序参与者签名**

即：

- 对 `@blob` / `@tchannel` / 复合顶点：`[ ... ]` 是接口列表
- 对 `@core` / `@point`：`[ ... ]` 是参与粒子签名列表

换言之，`vertex NAME [ ... ]` 的统一含义变为：

> **该顶点对象的有序外部连接签名**

只是不同类别的顶点，对这个签名的使用方式不同。

---

# 9. 推荐的统一顶点定义体系

我建议将 `vertex` 统一定义为：

```text
vertex NAME [signature] decorators_opt
vertex NAME [signature] decorators_opt = { body }
```

其中：
- `signature` 总是顶点外部连接类型列表
- 是否需要 `body` 由装饰器类别决定

---

## 9.1 规则

### `@core`
- 允许无定义体
- 不要求显式调用
- 用于自动匹配

### `@point`
- 允许无定义体
- 可显式调用
- 视为局域点

### `@blob`, `@tchannel`
- 通常有定义体或特殊渲染语义
- 用于显式调用或特殊模板

---

# 10. 匹配规则建议

为了支持：
```text
h(1) > b(2) b~(3)
```
需要加入正式匹配规则。

---

## 10.1 基础匹配
给定过程语句：
```text
A > B C
```
或更一般：
```text
A1 A2 ... > B1 B2 ...
```

实现构造粒子类型序列，例如：
```text
[h, b, b~]
```

然后在导入的 `@core` 顶点集合中寻找可匹配对象。

---

## 10.2 匹配标准
v0.1 建议先采用：

- **按无向参与者集合匹配**
- 或 **按归一化有序签名匹配**

具体策略可实现定义，但应保证：
- 同一顶点的物理等价排列能正确匹配
- 错误信息可读

例如：
```text
vertex hbb [h, b, b~] @core
```
应匹配：
```text
h(1) > b(2) b~(3)
```

---

## 10.3 歧义处理
若多个 `@core` 顶点匹配同一个过程语句：
- 报歧义错误
- 或要求用户改用显式 `@point` / 显式顶点指定

---

# 11. 语言层面的最小新增规则

下面给出应加入规范的最小修订内容。

---

## 11.1 新增顶点类别装饰器
```text
@core
@point
@blob
@tchannel
```

---

## 11.2 顶点定义允许省略定义体
语法从：

```text
vertex_decl:
    decorator_seq_opt 'vertex' identifier '[' port_type_list ']' '=' '{' local_stmt_list_opt '}'
```

扩展为：

````text
vertex_decl:
    decorator_seq_opt 'vertex' identifier '[' signature_list ']' decorator_seq_opt
    decorator_seq_opt 'vertex' identifier '[' signature_list ']' decorator_seq_opt '=' '{' local_stmt_list_opt '}'
````

---

## 11.3 过程语句的自动匹配语义
普通过程语句：
```text
particle_list > particle_list
```
若存在唯一 `@core` 匹配，则绑定到该顶点定义。

---

## 11.4 显式点顶点调用
允许：
```text
NAME[id1,id2,...]
```
其中 `NAME` 为 `@point` 顶点。

---

# 12. 例子

## 12.1 标准模型基础顶点
```text
import core,
import sm,

vertex hbb [h, b, b~] @core,
vertex hzz [h, z, z] @core,
vertex hww [h, w+, w-] @core,
vertex zll [z, l+, l-] @core,
vertex gqq [g, q, q~] @core
```

---

## 12.2 用户书写过程，不显式指定顶点
```text
h(1) > b(2) b~(3)
```

解析器行为：
- 在 `@core` 顶点中查找匹配
- 匹配到 `hbb [h,b,b~]`
- 在 IR 中为该语句绑定顶点类型 `hbb`

---

## 12.3 EFT 显式点顶点
```text
vertex hgg_eft [h, g, g] @point
```

使用：
```text
hgg_eft[1,2,3]
```

或：
```text
h(1) > hgg_eft[1,2,3] > g(2) g(3)
```

---

## 12.4 反常耦合显式指定
```text
vertex hza_anom [h, z, a] @point
vertex hza_sm   [h, z, a] @core
```

若用户写：
```text
h(1) > z(2) a(3)
```
系统可自动匹配到 `hza_sm`。

若用户希望明确指定反常耦合：
```text
hza_anom[1,2,3]
```

---

## 12.5 复合顶点保持不变
```text
@blob
vertex ggzpLoop [g, g, zp] = {
  [1] q(a) q~(b),
  [2] q(b) q~(c),
  [3] q(c) q~(a)
}
```

---

## 12.6 t-channel 特殊顶点
```text
@tchannel
vertex tchannelGamma [e+, e-, e+, e-]
```

调用：
```text
e+(1) e-(2) > tchannelGamma[1,2,3,4] > e+(3) e-(4)
```

---

# 13. 对规范结构的建议性结论

如果把你刚才提出的需求纳入正式语言设计，那么 FTDL 顶点系统应重构为：

## 13.1 三层体系
1. **`@core`**：模型自动匹配基础顶点  
2. **`@point`**：显式局域点顶点  
3. **`@blob` / `@tchannel`**：复合或特殊渲染顶点

---

## 13.2 对用户体验的改善
这样用户可以：

### 对普通 SM 顶点
直接写：
```text
h(1) > b(2) b~(3)
```

### 对特殊有效耦合
显式写：
```text
hgg_eft[1,2,3]
```

### 对特殊拓扑
显式写：
```text
e+(1) e-(2) > tchannelGamma[1,2,3,4] > e+(3) e-(4)
```

---

## 13.3 对实现架构的影响
解析器需要新增：
- `@core` 顶点表
- 普通过程语句的顶点自动匹配步骤
- 顶点类别分派逻辑

但这不会破坏你原有 DSL 架构，反而会让它更接近真实物理使用习惯。

---

如果你愿意，我下一步可以直接做两件事中的任意一个：

1. **把这部分正式并入《FTDL v0.1 语言规范草案》**，给你一版“修订后完整规范”
2. **单独写《FTDL 顶点系统规范》**，把 `@core / @point / @blob / @tchannel` 的规则完整写清楚

如果你想继续推进，我建议下一步我直接输出：

> **《FTDL v0.1 语言规范草案（修订版）》**

把前面的规范统一更新进去。
