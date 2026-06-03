# Tasks

- [x] Task 1: 项目脚手架和 CLI 框架搭建
  - 创建 Python 项目结构（`ue_bp_converter/` 包、`pyproject.toml`、`__init__.py`）
  - 使用 `argparse` 实现 CLI 入口，支持 `--input` / `--format` / `--stats` / `--output` 参数
  - 创建 CLI 入口点脚本 `ue-bp-converter`
  - 创建必要的目录结构：`parser/`、`transformer/`、`formatter/`

- [x] Task 2: 蓝图原始文本解析器（Parser）
  - 识别 Blueprint 复制文本的行结构，区分节点声明行、引脚行、连接行
  - 提取节点信息：节点名称、类型、GUID（暂存给后续清洗用）
  - 提取引脚信息：引脚名称、方向（Input/Output）、类型、连接目标
  - 提取变量引用：变量名、读/写操作
  - 输出中间表示（IR）：节点列表、连接列表、变量引用列表
  - 编写单元测试验证解析正确性

- [x] Task 3: 元数据清洗与逻辑变换层（Transformer）
  - 实现 GUID/UUID 移除逻辑
  - 实现坐标位置信息移除逻辑
  - 实现引擎内部枚举和标志位移除逻辑
  - 识别常见蓝图节点类型并映射到语义标签（Event → `EventBeginPlay`, Branch → `If/Else`, ForLoop → `For Loop` 等）
  - 构建执行流顺序（按 Exec 引脚连接排序）
  - 构建数据流依赖（按 Data 引脚连接关联）
  - 编写单元测试验证清洗正确性

- [x] Task 4: 结构化输出格式化器（Formatter）
  - 实现 `--format plain`：缩进文本逻辑流，每节点一行，缩进表示层级
  - 实现 `--format markdown`：Markdown 表格输出节点清单、连接表、变量说明
  - 实现 `--format mermaid`：输出 Mermaid `flowchart` 代码块
  - 每个格式输出均测试验证

- [x] Task 5: 统计信息输出
  - 实现 `--stats` 功能，统计节点总数及类型分布
  - 统计分支/序列/循环节点数
  - 统计变量引用数（读/写分别统计）
  - 统计外部函数/事件调用数
  - 支持同时与 `--format` 配合使用

- [x] Task 6: 未知节点降级处理
  - 对未匹配内置规则的节点，提取节点名称和引脚列表
  - 在输出中标注为 `[Unknown]` 类型
  - 确保不丢弃任何节点信息

- [x] Task 7: 集成测试与示例
  - 创建示例蓝图输入文件（至少 3 个：简单事件、条件分支、含循环的复杂蓝图）
  - 编写集成测试验证完整 pipeline（输入 → 解析 → 清洗 → 输出）
  - 验证三种输出格式的完整性
  - 验证 `--stats` 输出正确性

# Task Dependencies
- [Task 2] 依赖 [Task 1]
- [Task 3] 依赖 [Task 2]
- [Task 4] 依赖 [Task 3]
- [Task 5] 依赖 [Task 3]
- [Task 6] 依赖 [Task 3]
- [Task 7] 依赖 [Task 4, Task 5, Task 6]