# UE Blueprint Visualizer Spec

## Why
现有 CLI 工具虽能将蓝图文本转换为结构化文本和 Mermaid 流程图，但用户仍然无法直观地"看到"蓝图的结构。需要一个 Web 可视化界面，让用户粘贴蓝图文本后，以类似 UE 引擎蓝图编辑器的节点图方式呈现，提供更直观的视觉理解。

## What Changes
- 新增 Web 服务层（基于 FastAPI），将现有 Parser/Transformer/Formatter 暴露为 REST API
- 新增单页 Web 前端（React + TypeScript + Vite），提供可视化蓝图编辑器风格的界面
- 实现节点图渲染引擎：绘制带有输入/输出引脚的节点卡片，以及 Bezier 曲线连接线
- 实现类似 UE 蓝图编辑器的暗色主题视觉风格
- 支持粘贴蓝图文本后一键渲染为可视化节点图
- 支持节点的基本交互（拖拽移动、选中高亮）
- 支持切换查看纯文本/Markdown/Mermaid 格式输出

## Impact
- 新增 `web/` 目录存放前端代码
- 新增 `server.py` 或类似入口作为后端 API 服务
- 不修改现有 `ue_bp_converter/` 核心代码
- 项目新增依赖：FastAPI、uvicorn（后端）；React、Vite、TypeScript（前端）

## ADDED Requirements
### Requirement: Web API 服务
系统 SHALL 提供 REST API 端点，接收蓝图文本并返回解析后的结构化数据和渲染所需信息。

#### Scenario: 蓝图解析 API
- **WHEN** 用户发送 POST 请求携带蓝图文本
- **THEN** 返回 JSON 格式的节点列表、引脚信息、执行流和数据流

#### Scenario: 格式转换 API
- **WHEN** 用户请求指定格式（plain/markdown/mermaid）
- **THEN** 返回对应格式的文本输出

#### Scenario: 统计 API
- **WHEN** 用户请求统计信息
- **THEN** 返回节点总数、类型分布、变量引用数等统计数据

### Requirement: 可视化节点图渲染
系统 SHALL 将蓝图解析结果渲染为节点图，视觉风格类似 UE 蓝图编辑器。

#### Scenario: 节点渲染
- **WHEN** 蓝图包含事件节点（如 EventBeginPlay）
- **THEN** 节点显示为顶部带标题的圆角卡片，左侧带执行输出引脚，底部可带数据引脚

#### Scenario: 引脚视觉区分
- **WHEN** 节点有不同类型引脚
- **THEN** 执行引脚（exec）用实心三角形/箭头标记，数据引脚用圆形标记并用颜色区分类型（布尔=红色、整型=青色、浮点=黄色、字符串=绿色、对象=蓝色）

#### Scenario: 连接线渲染
- **WHEN** 节点之间存在执行流或数据流连接
- **THEN** 绘制 Bezier 曲线连接对应的引脚，执行线用白色实线，数据线用对应类型的彩色虚线

#### Scenario: 未知节点降级渲染
- **WHEN** 蓝图包含未识别的节点类型
- **THEN** 节点渲染为特殊样式的灰色卡片，标注 `[Unknown]` 标记

### Requirement: 交互操作
系统 SHALL 支持基本的节点图交互操作。

#### Scenario: 节点拖拽
- **WHEN** 用户拖拽节点
- **THEN** 节点跟随鼠标移动，连接线实时更新

#### Scenario: 节点选中
- **WHEN** 用户点击节点
- **THEN** 节点高亮显示（边框变为亮色）

#### Scenario: 画布平移与缩放
- **WHEN** 用户在画布空白区域拖拽
- **THEN** 画布整体平移
- **WHEN** 用户使用滚轮
- **THEN** 画布缩放

### Requirement: 多视图切换
系统 SHALL 提供可视化图、纯文本、Markdown、Mermaid 四种视图模式。

#### Scenario: 视图切换
- **WHEN** 用户点击视图切换按钮
- **THEN** 界面在可视化节点图 / 纯文本 / Markdown / Mermaid 之间切换
- **THEN** Mermaid 视图提供一键复制功能

### Requirement: 输入与示例
系统 SHALL 提供蓝图文本输入区域和示例加载功能。

#### Scenario: 文本粘贴
- **WHEN** 用户将蓝图文本粘贴到输入框
- **THEN** 自动或点击按钮后触发解析和可视化渲染

#### Scenario: 示例加载
- **WHEN** 用户点击"加载示例"按钮
- **THEN** 下拉选择 simple_event / branch_flow / variable_and_loop 示例
- **THEN** 自动加载示例文本并触发渲染

### Requirement: 视觉风格
系统 SHALL 采用类似 UE 蓝图编辑器的暗色主题。

#### Scenario: 主题色彩
- **WHEN** 界面加载
- **THEN** 背景为深色（#1a1a2e 或类似深色），节点卡片为深灰色（#2d2d44），文字为浅色
- **THEN** 执行引脚连线为白色，数据引脚连线使用类型对应的颜色

## MODIFIED Requirements
（无修改项）

## REMOVED Requirements
（无移除项）