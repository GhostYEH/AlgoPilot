# AlgoPilot（算法领航员）—— 面向《数据结构与算法》的智能学习平台

## 项目概述

AlgoPilot（算法领航员）是一个基于科大讯飞星火大模型、多智能体协同、个性化学习路径和代码 Trace 诊断的《数据结构与算法》智能学习平台。面向计算机类专业大学生，提供从"学生画像 → 个性化路径 → 多智能体资源生成 → OJ 判题与 Trace 可视化诊断 → 掌握度评估 → 路径动态调整"的全流程学习闭环。

## 核心学习闭环

对话式学生画像 → 个性化学习路径 → 多智能体资源生成 → OJ 与 Trace 诊断 → 掌握度评估 → 路径动态调整

## 五大学习痛点

痛点P1：概念抽象难懂——树、图、动态规划等概念高度抽象，课本静态插图难以展示动态过程
痛点P2：刷题盲目无方向——学生不知道自己该先学什么、后学什么，题海茫茫缺乏个性化路径
痛点P3：错题不知为何错——OJ只返回WA/TLE/RE等冰冷判定，学生看不到程序运行轨迹
痛点P4：学习过程无记录——学过的内容散落各处，无法形成个人学习档案
痛点P5：教师难以因材施教——大班授课下教师无法掌握每个学生的薄弱点

## 现有方案不足

传统OJ平台（洛谷、力扣）：只判对错，无诊断、无画像、无路径规划
MOOC课程：视频单向输出，无个性化、无交互式代码可视化
通用AI助手（ChatGPT、文心一言）：无课程知识库约束，易产生幻觉
算法可视化网站（VisuAlgo）：只能看预设动画，不能追踪学生自己写的代码

## 技术架构

前后端分离 + 多智能体编排的三层架构

前端：Vue 3 + TypeScript + Element Plus，30余个页面，70个组件，13个算法游戏，13个Trace组件
后端：FastAPI + Python，16个API路由模块
AI引擎层：讯飞星火大模型（OpenAI兼容接口）
编排层：自研轻量DAG Orchestrator，零langgraph依赖
Agent层：22个注册条目（20个已实现），6个layer
RAG知识层：Okapi BM25 + 课程Markdown
OJ判题层：Python/C++双语言，subprocess + AST + g++/gdb
安全层：AST分析 + 正则 + 内容审查
数据层：SQLAlchemy 2.0 + SQLite/MySQL

## 多智能体系统（22个Agent，20个已实现）

### 6大Layer

Layer 1 - Profiling Layer：ProfilingAgent、PersonaInitAgent
Layer 2 - Resource Layer：ConceptAgent、GraphAgent、QuizAgent、ScenarioAgent、TraceAgent、ReadingAgent、ResourceDispatchAgent
Layer 3 - Path Layer：LearningPathAgent
Layer 4 - Tutor Layer：AiTutorAgent、CodeReviewAgent、HintAgent、MisconceptionAgent
Layer 5 - Safety Layer：ContentVerifierAgent、SafetyAgent、ASTAnalyzerAgent
Layer 6 - Eval Layer：MasteryEvalAgent、LearningEventAgent、TeacherDashboardAgent

### 资源生成四阶段并行拓扑

Phase 1：document（ConceptAgent）
Phase 2：mindmap ∥ exercises（GraphAgent ∥ QuizAgent）
Phase 3：code_case（ScenarioAgent）
Phase 4：trace_animation ∥ reading（TraceAgent ∥ ReadingAgent）

## 6种资源类型

个性化课程讲解文档：ConceptAgent生成，结合RAG知识库
知识点思维导图：GraphAgent生成，Mermaid格式
分层练习题：QuizAgent生成，基于Bloom认知分层
代码实操案例：ScenarioAgent生成，交互式代码沙盒
Trace执行动画：TraceAgent生成，13种可视化类型
分层拓展阅读：ReadingAgent生成

## 智能辅导系统

AI助教流式答疑：基于RAG知识库的上下文感知辅导
OJ智能诊断：错误代码分析 + Trace可视化
13种Trace可视化组件：变量追踪、调用栈、内存状态等
确定性旁白：经典题目无LLM依赖的可复现旁白

## 在线OJ系统

双语言支持：Python + C++
AST静态审计：死循环检查、数组越界检测
安全机制：子进程超时3秒、危险调用拦截
13种Trace类型：Python sys.settrace + C++ GDB MI统一归一化

## 防幻觉与安全机制

RAG知识约束：Okapi BM25检索课程知识库切片
校验闭环：ContentVerifierAgent对照知识库校验
内容安全：SafetyAgent检测敏感词、幻觉题号、Prompt注入
C++安全：check_cpp_security正则拦截system/fork/exec
AST静态审计：ASTAnalyzerAgent识别死循环、数组越界
子进程超时：Python 3秒、C++ Trace 3秒硬上限

## 教师学情看板

掌握度热力图：可视化班级整体学情分布
学生花名册：查看每个学生的薄弱知识点
OJ学情分析：全班OJ完成情况统计
学习事件追踪：学习行为记录与分析

## 技术创新

创新1：自研轻量DAG编排——借鉴状态图与DAG编排思想，零langgraph依赖，自主实现，易部署
创新2：四阶段并行资源生成——document → (mindmap ∥ exercises) → code_case → (trace_animation ∥ reading)
创新3：Trace协议统一归一化——Python sys.settrace + C++ GDB MI统一为13类可视化类型
创新4：RAG + 校验闭环 + Safety三重防幻觉——BM25约束生成→对照校验回流重试→安全审查
创新5：确定性旁白——经典题目无LLM依赖的可复现旁白

## 应用价值

对学生：个性化学习路径、多维度资源、代码Trace可视化、AI智能辅导
对教师：全面学情看板、精准识别薄弱学生、教学效果评估
对教育：AI+教育深度融合的落地实践，降低大模型幻觉风险，可复制的智能教育范式

## 比赛文档

01 项目说明书
02 系统开发说明书
03 测试说明书
04 部署说明书
05 用户操作手册
06 第三方开源依赖与AI Coding使用说明

## 验证数据

Backend pytest：188 passed
Frontend typecheck：passed
Frontend build：passed
