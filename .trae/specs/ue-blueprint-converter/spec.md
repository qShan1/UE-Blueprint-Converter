# UE Blueprint Converter Spec

## Why
UE Blueprint 导出的纯文本格式混杂了大量无关元数据（GUID、坐标、枚举值等），直接喂给大语言模型时噪音大、Token 浪费严重，且丢失了蓝图原有的图结构语义。需要一个工具将原始粘贴文本"洗"成 AI 易于理解的、结构化的、保留核心逻辑的表达形式。

## What Changes
- 创建 CLI 工具 `ue-blueprint-converter`（Python），接收标准输入或文件输入，输出清洗后的蓝图逻辑描述
- 实现蓝图原始文本的解析层（Lexer/Parser），识别节点类型、引脚、连接、变量、函数/事件引用
- 实现清洗/变换层（Transformer），去除元数据噪音（GUID、无用坐标、平台枚举），合并冗余信息，保留控制流和数据流
- 实现输出层（Formatter），输出结构化文本格式（Markdown 或类似 Graphviz/DOT 的文本图描述），便于 AI 理解
- 内置一批常见蓝图节点（事件节点、流程控制、变量操作、函数调用、数学运算、Actor/Component 操作）的识别和语义化转换规则
- 支持输出多种格式：`--format plain`（纯文本逻辑流）、`--format markdown`（Markdown 结构化）、`--format mermaid`（Mermaid 流程图代码）
- 支持 `--stats` 选项输出蓝图统计信息（节点数、分支数、函数调用数等）

## Impact
- 新增独立工具模块，不修改现有代码
- 项目新增 Python 依赖（可选）：可供后续集成到 CI/文档流水线

## ADDED Requirements
### Requirement: 蓝图输入解析
系统 SHALL 支持从 stdin 或文件读取 UE Blueprint 复制的原始文本。

#### Scenario: 标准输入解析
- **WHEN** 用户通过管道传递蓝图文本
- **THEN** 系统成功解析并识别所有节点和连接

#### Scenario: 文件输入解析
- **WHEN** 用户提供蓝图文本文件路径
- **THEN** 系统读取文件并成功解析

### Requirement: 元数据清洗
系统 SHALL 自动移除蓝图文本中的以下噪音信息：
- GUID/UUID
- 节点屏幕坐标（位置 X/Y）
- 引擎内部枚举值（如 `EBlueprintPinDirection`）
- 编译期标记（如 `bIsPureCast`、`bIsConst` 等内部标志）

#### Scenario: 清洗验证
- **WHEN** 输入包含上述噪音
- **THEN** 输出中不包含这些噪音信息

### Requirement: 逻辑结构提取
系统 SHALL 识别并提取蓝图的以下逻辑元素：
- 事件节点（EventBeginPlay、EventTick、自定义事件等）
- 执行线（Exec 引脚连接）和控制流（分支、循环、序列）
- 数据线（Data 引脚连接）和数据依赖
- 变量读取/写入
- 函数/事件调用及其参数映射
- 类型信息（用于提供强类型上下文）

#### Scenario: 控制流提取
- **WHEN** 蓝图包含 Branch、ForLoop、Sequence 等控制流节点
- **THEN** 输出正确反映执行分支和循环结构

#### Scenario: 数据流提取
- **WHEN** 蓝图包含变量操作和函数调用
- **THEN** 输出清晰展示数据来源、转换和去向

### Requirement: 结构化输出
系统 SHALL 支持三种输出格式：
1. `plain`：缩进的纯文本逻辑流描述，每个节点一行，用缩进表示执行层级
2. `markdown`：Markdown 格式，包含节点列表、连接表格、变量说明
3. `mermaid`：Mermaid.js 流程图代码，可直接渲染为可视化流程图

#### Scenario: Markdown 输出
- **WHEN** 用户指定 `--format markdown`
- **THEN** 输出包含节点清单表、连接关系表、变量使用说明

#### Scenario: Mermaid 输出
- **WHEN** 用户指定 `--format mermaid`
- **THEN** 输出可被 Mermaid 渲染器解析的 `flowchart` 代码块

### Requirement: 统计信息
系统 SHALL 在指定 `--stats` 时输出：
- 节点总数及类型分布
- 分支/序列/循环节点数
- 变量引用数（读/写分别统计）
- 外部函数/事件调用数

#### Scenario: 统计输出
- **WHEN** 用户指定 `--stats`
- **THEN** 输出以上统计信息

### Requirement: 未知节点降级
系统 SHALL 对未能识别的节点类型提供降级处理，至少输出其节点名称和已知引脚信息，不丢弃无法识别的节点。

#### Scenario: 未知节点处理
- **WHEN** 输入包含未在内置规则中的节点
- **THEN** 输出中包含该节点的基础信息（名称、引脚列表），并标注为 [Unknown]