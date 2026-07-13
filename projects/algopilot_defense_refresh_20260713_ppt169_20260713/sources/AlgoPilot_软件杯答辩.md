# AlgoPilot_软件杯答辩

- Source: `AlgoPilot_软件杯答辩.pptx`
- Total slides: 24

## Slide 1

AlgoPilot

算法领航员

面向《数据结构与算法》的多智能体智能学习平台

软件杯 A3 赛题 · 2026

## Slide 2

目录

Contents

01

背景与痛点

Background & Pain Points

02

解决方案总览

Solution Overview

03

技术架构

System Architecture

04

核心功能

Core Features

05

创新亮点

06

Innovation Highlights

06

应用价值与数据

Application Value & Data

02 / 24

## Slide 3

01 · BACKGROUND

每个算法学习者都懂的五道坎

?

?

概念抽象难懂

刷题盲目无方向

P1

P2

树、图、动态规划高度抽象

不知先学什么、后学什么

?

课本静态插图难以展示动态过程

题海茫茫缺乏个性化路径

错题不知为何错

学习过程无记录

P3

P4

OJ只返回WA/TLE冰冷判定

学过的内容散落各处

看不到程序运行轨迹

换设备一切归零

教师难以因材施教

P5

大班授课无法掌握个体差异

作业批改与学情分析靠人工

✦ 公认"最难啃的硬骨头" — 各大高校计算机专业课程调研

03 / 24

## Slide 4

01 · BACKGROUND

为什么现有方案不够？

方案

核心不足

评价

✗

传统 OJ（力扣/洛谷）

只判对错，无诊断、无画像、无路径规划

✗

MOOC 课程

视频单向输出，无个性化、无交互式可视化

△

通用 AI 助手

无课程知识库约束，易产生幻觉

✗

算法可视化网站

只能看预设动画，不能追踪自己写的代码

◆

AlgoPilot（我们）

全流程智能闭环 — 画像+路径+资源+Trace+辅导

💡 AlgoPilot 的解决思路

多智能体协同 · RAG 知识库 · 大语言模型 · 代码 Trace 可视化 — 四大技术深度融合

04 / 24

## Slide 5

02 · SOLUTION

AlgoPilot

算法领航员

一个懂你、记你、陪你、纠你的全流程智能学习平台

多智能体协同 + RAG 知识库 + 大语言模型 + 代码 Trace 可视化 深度融合

面向《数据结构与算法》课程，提供对话式学生画像、个性化学习路径、多智能体资源生成、OJ 判题与 Trace 可视化诊断、AI 辅导与教师学情看板。

系统通过 BM25 RAG 检索、内容校验、安全审查和有限重试等机制，降低大模型生成幻觉和不合规内容的风险。

05 / 24

## Slide 6

02 · SOLUTION

从"不会"到"掌握"的智能闭环

学生

画像

→

→

掌握度评估

→ 路径动态调整

→

→

持续迭代 · 动态优化

OJ与

学习

闭环

Trace

路径

→

资源

生成

06 / 24

## Slide 7

03 · ARCHITECTURE

三层架构 + 多智能体编排

前端

Vue 3 + TypeScript

30+ 页面

Mermaid · D3.js

Frontend

Element Plus · CodeMirror

70+ 组件 · 13 游戏

Vue Flow · Pinia

▼

API 层

FastAPI

JWT 鉴权

SSE 流式

16 路由 · Pydantic

bcrypt · 角色隔离

AI 辅导实时输出

API Layer

▼

编排层

RAG 知识层

数据层

自研 DAG Orchestrator · 零 langgraph 依赖

BM25 检索 · 同义词扩展 · 课程Markdown

SQLAlchemy 2.0 · 7 表 · SQLite/MySQL

AI 引擎

Agent Engine

Agent 层

OJ + 安全层

LLM 层

★ 核心层

22 注册 · 20 已实现 · 6 Layer

Python/C++ · AST 审计 · 3s 超时

讯飞星火 · OpenAI 兼容 · 流式+非流式

✦ 自研轻量编排 · 零 langgraph 依赖

07 / 24

## Slide 8

03 · ARCHITECTURE

22 个智能体 · 6 层协作

L1 画像层

L2 资源层

L3 路径层

L4 辅导层

ProfilingAgent

Concept · Graph · Quiz · Scenario

LearningPathAgent

AiTutor · CodeReview · Hint

PersonaInitAgent

Trace · Reading · ResourceDispatch

MisconceptionAgent

L5 安全层 ★

L6 评估层

ContentVerifierAgent · SafetyAgent · ASTAnalyzerAgent

MasteryEval · LearningEvent · TeacherDashboard

智能体协作流程

资源生成

OJ / Trace

用户输入

掌握度

画像对话

路径规划

评估反馈

AI 辅导

📋 注册 22 个 Agent 条目 · 20 个已实现 · 2 个规划中扩展节点（PptAgent / VideoScriptAgent）· 6 个 Layer 端到端覆盖

08 / 24

## Slide 9

03 · ARCHITECTURE

四阶段并行生成，效率翻倍

Phase 2 ⚡并行

Phase 4 ⚡并行

Phase 3

Phase 1

🧠 mindmap

📝 exercises

🎬 trace

📖 reading

GraphAgent

QuizAgent

TraceAgent

ReadingAgent

💻 code_case

📄 document

ScenarioAgent

ConceptAgent

串行入口

串行 →

⚡ 并行拓扑相比串行生成，效率提升 2-3 倍

Phase 2 的 mindmap 和 exercises 互不依赖，可并行生成

Phase 4 的 trace_animation 和 reading 同样并行执行

✦ 6 种资源类型的协同工作流

09 / 24

## Slide 10

04 · CORE FEATURES

懂你：对话式六维画像

语言偏好

数据结构掌握度

六维

编程基础

学习目标

画像

薄弱知识点

学习风格

🔄 动态更新机制

3-5 轮对话自动抽取 · 无需问卷 · 每次学习后画像更新 · 路径随之动态调整

ProfilingAgent 驱动 · 数据库 7 表外键关联持久存储

10 / 24

## Slide 11

04 · CORE FEATURES

记你：动态学习路径 DAG

知识点依赖关系 DAG

LearningPathAgent

数组

✦ 基于画像生成个性化路径

✦ DAG 可视化，可拖动交互

✦ 受挫自动插入巩固节点

✦ 掌握度达阈值自动推进

链表

栈与队列

哈希表

树与二叉树

排序算法

图与图算法

动态规划

⚠ 巩固：从树到图

11 / 24

## Slide 12

04 · CORE FEATURES

陪你：六种覆盖全场景学习资源

📄 讲解文档

🧠 思维导图

📝 分层练习题

✓

ConceptAgent

GraphAgent

QuizAgent

结合 RAG 知识库

Mermaid 格式

Bloom 认知分层

个性化课程讲解

知识结构化可视化

5 道个性化习题

💻 代码实操案例

🎬 Trace 执行动画

📖 分层拓展阅读

</>

ScenarioAgent

TraceAgent

ReadingAgent

交互式代码沙盒

13 种可视化类型

分层难度匹配

即学即练

代码逐行追踪诊断

拓展知识边界

理解

→ 结构化

→ 练习

→ 实践

→ 调试

→ 拓展

12 / 24

## Slide 13

04 · CORE FEATURES

纠你：在线 OJ + 代码诊断

🐍 Python 判题

⚡ C++ 判题

OJ 代码编辑器界面

subprocess 沙盒执行

g++ 编译 + 运行

3s 超时硬上限

危险调用拦截

▶ Run

|

Python 3

C++

Trace

1

def reverse_list(head):

🔍 AST 审计

🛡️ 安全机制

2

prev = None

死循环检测

危险调用拦截

3

curr = head

数组越界检查

输出截断保护

4

while curr:

5

next_node = curr.next

6

curr.next = prev

🎯 AI 诊断分析

7

prev = curr

错误代码自动分析 + 优化建议 + 知识点关联

8

curr = next_node

基于 RAG 知识库的上下文感知诊断

9

return prev

✓ 测试通过 (3/3) | Trace 动画已生成

13 / 24

## Slide 14

04 · CORE FEATURES

代码 Trace 可视化——看见每一步

🐍 Python Trace：sys.settrace

⚡ C++ Trace：GDB MI

Step 5

Step 6

Step 7

变量追踪

调用栈

内存状态

GDB 单步追踪

STL 容器提取

curr → Node(3)

reverse_list

head▸1▸2▸3▸None

→ line 42: curr = curr->next

gdb_stl_extract

13 种 Trace 可视化类型

变量追踪

调用栈

内存状态

链表结构

树/图

数组

指针引用

递归展开

循环展开

条件分支

时间线

旁白

✦ Python sys.settrace + C++ GDB MI 统一为 13 类可视化类型 · 确定性旁白确保经典题目可复现

14 / 24

## Slide 15

04 · CORE FEATURES

学情全景：AI 辅导 + 教师看板

学生端：AI 智能辅导

教师端：全面学情看板

S

T

💬 AI 助教流式答疑

🔍 OJ 智能诊断

🔥 掌握度热力图

📋 学生花名册

基于 RAG 知识库上下文感知

错误代码自动分析

班级整体学情一目了然

逐个查看学生薄弱点

SSE 流式实时输出

Trace 可视化回放

颜色标注薄弱知识点

针对性辅导参考

📊 掌握度评估

📝 个性化错题本

📊 OJ 学情分析

📈 学习事件追踪

MasteryEvalAgent

WeakPoint 标注

全班 OJ 完成情况统计

学习行为记录与分析

基于学习事件数据分析

针对性巩固练习

通过率 / 错误分布

7 表外键关联数据

✦ AiTutorAgent + TeacherDashboardAgent + MasteryEvalAgent + LearningEventAgent 四引擎驱动

15 / 24

## Slide 16

05 · SAFETY & INNOVATION

如何让 AI 不说胡话？三重防幻觉防线

RAG 知识约束

校验闭环

内容安全审查

1

2

3

Okapi BM25 检索

ContentVerifierAgent

SafetyAgent

检索课程知识库切片

对照知识库校验内容

敏感词检测

第三层

约束 LLM 生成范围

检测事实性错误

幻觉题号识别

同义词扩展增强召回

Prompt 注入防护

有限重试机制

第二层

课程级 Markdown

内容输出安全

校验失败自动回流

14 章 + 6 实验 + 2 项目

输出内容截断保护

携带校验反馈重试

第一层

结构化切片存储

敏感内容过滤

加权打分排序

结构化输出校验

C++ 安全拦截

安全

Pydantic Schema 验证

check_cpp_security

格式/类型自动校验

system/fork/exec 拦截

16 / 24

## Slide 17

05 · SAFETY & INNOVATION

从代码到内容，层层设防

🔍 AST 静态审计

🛡️ C++ 安全拦截

⏱️ 子进程超时

3s

</>

✓

ASTAnalyzerAgent

check_cpp_security 正则

Python 判题 3 秒硬上限

识别死循环、数组越界

拦截 system() / fork() / exec()

C++ Trace 3 秒硬上限

执行前熔断，防止资源耗尽

防止危险系统调用

TLE 自动返回，不阻塞系统

✂️ 输出截断保护

🚫 内容安全检测

🔐 Prompt 防护

!

防止无限输出

敏感词 / 幻觉检测

Prompt 注入检测

控制输出长度上限

题目编号真实性校验

防止恶意指令绕过

六道安全防线 · 覆盖代码执行 + 内容生成 + 输出全链路

大模型生成内容仍可能存在错误，重要学术内容应由学生或教师进一步复核

17 / 24

## Slide 18

06 · INNOVATION

零依赖的自研 DAG 编排引擎

自研编排器架构图

零 langgraph 依赖

✦

借鉴状态图与 DAG 编排思想，自主实现

不依赖任何第三方 Agent 框架

Pipeline

资源调度

并行执行器

部署简单，无额外运行时依赖

灵活拓扑编排

✦

DAG 拓扑定义 Agent 依赖关系

四阶段并行资源生成

串行

串行

任务级调度精确到每个 Agent

节点

节点

188 测试通过

✦

Done

涵盖编排器核心逻辑

支持串行 / 并行 / 条件分支拓扑 · 188 测试验证编排正确性

Agent 调用链路测试

端到端流程验证

18 / 24

## Slide 19

06 · INNOVATION

Python/C++ Trace 协议统一归一化

🐍 Python Trace 路径

🎯 统一输出：13 类可视化类型

变量追踪

调用栈

Python

统一事件流

sys.settrace HOOK

Normalized Events

⚡ C++ Trace 路径

内存状态

链表结构

树/图遍历

数组操作

C++ (GDB)

STL 容器提取

统一事件流

指针引用

递归展开

GDB MI 单步

gdb_stl_extract

Normalized Events

D3.js 13 个可视化组件前端渲染

确定性旁白

✦

经典题目（反转链表、unique-paths）无 LLM 依赖

确保可复现、可验证的旁白内容

19 / 24

## Slide 20

06 · INNOVATION

更多技术创新

创新三：四阶段并行

创新四：三重防幻觉

创新五：确定性旁白

document → (mindmap ∥ exercises)

BM25 约束 → 校验回流 → 安全审查

经典题目 → 无 LLM 依赖

→ code_case → (trace ∥ reading)

三层防线系统级降风险

可复现 · 可验证

串行依赖 → 并行拓扑

第一层：Okapi BM25 知识约束

解决的问题

效率提升 2-3 倍

检索课程知识库约束生成范围

纯 LLM 旁白不可复现

每次生成结果不一致

技术细节

第二层：ContentVerifierAgent

对照知识库校验回流重试

Phase 2 的 mindmap 和 exercises

技术方案

互不依赖，可并行生成

经典题目预定义旁白模板

第三层：SafetyAgent

Phase 4 的 trace 和 reading 同理

基于代码执行状态映射

敏感词 / 幻觉 / Prompt注入检测

自研 DAG 调度确保拓扑正确性

覆盖反转链表、unique-paths 等

20 / 24

## Slide 21

07 · APPLICATION VALUE

三种角色，一套平台

学生

教师

教育

Student

Teacher

Education

个性化学习路径

全面学情看板

AI+教育深度融合实践

多维度智能资源

掌握度热力图

降低大模型幻觉风险

代码 Trace 可视化

精准识别薄弱学生

可复制的智能教育范式

AI 智能辅导答疑

教学效果量化评估

多智能体协同参考架构

掌握度量化评估

因材施教辅助决策

零 langgraph 轻量部署

持久化学习记忆

21 / 24

## Slide 22

07 · APPLICATION VALUE

用数据证明完成度

188

22

13

Backend pytest passed

多智能体注册 / 20 已实现

Trace 可视化类型

32 个测试文件 · 全覆盖核心逻辑

6 个 Layer · 端到端覆盖

Python sys.settrace

Frontend typecheck + build 均通过

2 个规划中扩展节点

C++ GDB MI 统一归一化

6 份

70+

6

</>

完整比赛文档

Vue 组件 / 30+ 页面

Layer / 6 种资源类型

项目说明书 · 系统开发说明书

Vue 3 + TypeScript + Element Plus

画像/资源/路径/辅导/安全/评估

测试 · 部署 · 手册 · 开源说明

13 个算法游戏 + 13 个 Trace 组件

6 种资源覆盖学习全链路

22 / 24

## Slide 23

07 · APPLICATION VALUE

完整的项目交付

01 项目说明书

02 系统开发说明书

03 测试说明书

✓

项目背景、目标用户、创新价值、技术实现

架构设计、分层职责、模块说明、目录结构

测试策略、测试用例、执行结果、覆盖率

涵盖五大痛点分析 · 目标用户定义 · 赛题对应关系

9 层架构 · 16 API 路由 · 20+ 服务模块

188 pytest passed · 32 测试文件

04 部署说明书

05 用户操作手册

06 开源与AI说明

部署架构、环境要求、启动方式、配置说明

功能说明、操作步骤、常见问题、系统截图

第三方依赖、AI Coding 使用说明

Windows 一键启动 · 前后端分离部署

30+ 页面 · 70+ 组件完整操作指南

THIRD_PARTY_LICENSES · 开发工具声明

技术栈总览

前端：Vue 3 + TypeScript + Element Plus + CodeMirror + Mermaid + D3.js

后端：FastAPI + Python + SQLAlchemy 2.0 | AI：讯飞星火 + 自研 DAG | OJ：subprocess + GDB + AST

23 / 24

## Slide 24

Thank You

AlgoPilot — 算法领航员

从不会到掌握

AlgoPilot 陪每个学习者走过每一步

软件杯 A3 赛题 · 2026

24 / 24
