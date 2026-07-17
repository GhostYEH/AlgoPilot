from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "images"
OUT.mkdir(parents=True, exist_ok=True)
FONT = "C:/Windows/Fonts/msyh.ttc"
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"

def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)

def arrow(d, a, b, color="#3B7A70", width=5):
    d.line([a, b], fill=color, width=width)
    x2, y2 = b; x1, y1 = a
    import math
    ang = math.atan2(y2-y1, x2-x1)
    pts=[]
    for da in (2.55, -2.55):
        pts.append((x2+18*math.cos(ang+da), y2+18*math.sin(ang+da)))
    d.polygon([b,*pts], fill=color)

def box(d, xy, title, body="", fill="#F3F8F7", accent="#2F7469"):
    x1,y1,x2,y2=xy
    d.rounded_rectangle(xy, radius=18, fill=fill, outline="#AFC8C3", width=3)
    d.rectangle((x1,y1,x1+10,y2), fill=accent)
    d.text((x1+28,y1+18), title, font=font(30,True), fill="#173B36")
    if body:
        d.multiline_text((x1+28,y1+64), body, font=font(20), fill="#425B57", spacing=8)

def canvas(title, subtitle):
    im=Image.new("RGB",(1600,900),"#FBFDFC"); d=ImageDraw.Draw(im)
    d.text((70,42),title,font=font(46,True),fill="#173B36")
    d.text((72,104),subtitle,font=font(22),fill="#637D78")
    d.line((70,148,1530,148),fill="#D3E3DF",width=3)
    return im,d

def save(name,title,subtitle,nodes,edges):
    im,d=canvas(title,subtitle)
    for i,j in edges:
        a=nodes[i][0];b=nodes[j][0]
        arrow(d,((a[0]+a[2])//2,a[3]),((b[0]+b[2])//2,b[1]))
    for xy,t,b,c in nodes: box(d,xy,t,b,accent=c)
    im.save(OUT/name)

save("D01-system-architecture.png","AlgoPilot 系统总体架构","真实代码模块与请求链路的分层视图",[
((80,190,1520,295),"Vue 3 前端","23 个视图 · 31 个命名路由 · Element Plus / Pinia / CodeMirror","#1F6E8C"),
((80,365,1520,470),"FastAPI 接口层","67 个 HTTP 端点 · JWT 鉴权 · SSE 流式接口 · Pydantic 校验","#2F7469"),
((80,540,760,690),"智能体与编排服务","22 个注册节点 · 自研 DAG · 安全/校验回流","#8A5C9E"),
((840,540,1520,690),"OJ / Trace 执行服务","Python / C++ 判题 · AST 审计 · Trace / GDB","#B06A2E"),
((80,760,1520,850),"数据与知识层","8 张 ORM 表 · SQLite/MySQL · 126 道 OJ · 14 章课程知识库","#526E3E")],[(0,1),(1,2),(1,3),(2,4),(3,4)])

save("D02-agent-six-layers.png","多智能体六层结构","注册表口径：22 个节点，其中 20 个 implemented、2 个 planned",[
((100,180,1500,270),"Profiling","ProfilingAgent：六维动态画像","#4676A9"),
((100,300,1500,410),"Resource","Concept / Graph / Quiz / Scenario / Trace / Reading；Ppt、VideoScript 为 planned","#8A5C9E"),
((100,440,1500,530),"Path","PlannerAgent / LearningPathAgent：路径规划与重排","#2F7469"),
((100,560,1500,650),"Tutor","Tutor / OjAssistant / OjDiagnosis：答疑与诊断","#B06A2E"),
((100,680,780,830),"Safety","ASTAnalyzer / ContentVerifier / Safety / KnowledgeRetriever","#9B4B45"),
((820,680,1500,830),"Evaluation","Evaluator / Evaluation / Mastery / EventBus","#526E3E")],[(0,1),(1,2),(2,3),(3,4),(3,5)])

save("D03-resource-dag.png","四阶段资源生成 DAG","资源生成、校验回流与效果评估的可观测拓扑",[
((100,190,1500,290),"阶段 1 · 学习上下文","ProfilingAgent + LearningPathAgent","#4676A9"),
((100,350,1500,450),"阶段 2 · 知识检索","KnowledgeRetriever 绑定课程知识库证据","#2F7469"),
((100,510,1500,635),"阶段 3 · 并行生成","Concept · Graph · Quiz · Scenario · Trace · Reading","#8A5C9E"),
((100,700,720,835),"阶段 4A · 校验回流","ContentVerifier + SafetyAgent","#9B4B45"),
((880,700,1500,835),"阶段 4B · 效果评估","EvaluationAgent 写入学习闭环","#526E3E")],[(0,1),(1,2),(2,3),(2,4)])

save("D04-oj-trace-flow.png","OJ / Trace 数据流","本轮真实复现：WA → Trace → 规则诊断 → 学习干预",[
((120,180,1480,280),"浏览器工作台","题目、CodeMirror、运行/提交/可视化调试","#1F6E8C"),
((120,345,720,485),"静态安全链路","ASTAnalyzer：危险调用、死循环与语法预检","#9B4B45"),
((880,345,1480,485),"动态执行链路","Python trace_runner / C++ GDB · 超时与资源限制","#B06A2E"),
((120,565,1480,675),"证据化诊断","判题结果 + 变量快照 + 首次逻辑偏差 + 修复建议","#8A5C9E"),
((120,750,1480,840),"学习闭环","写入学习记忆、画像证据与 PlannerAgent 路径巩固节点","#526E3E")],[(0,1),(0,2),(1,3),(2,3),(3,4)])

save("D05-database-er.png","数据库 E-R 关系图","SQLAlchemy 元数据实扫：8 张表",[
((80,180,490,310),"users","账号、角色与创建时间","#1F6E8C"),
((600,180,1010,310),"student_profiles","六维画像与摘要","#4676A9"),
((1120,180,1520,310),"learning_progress","模块/小节进度","#2F7469"),
((80,430,490,560),"learning_path_plans","个性化路径计划","#8A5C9E"),
((600,430,1010,560),"generated_resources","多智能体资源","#8A5C9E"),
((1120,430,1520,560),"oj_submissions","OJ 提交与判定","#B06A2E"),
((280,680,760,820),"student_learning_memories","错因、诊断与长期学习记忆","#526E3E"),
((850,680,1330,820),"learning_event_logs","学习事件与 Agent 处理日志","#9B4B45")],[(0,1),(0,2),(0,3),(0,4),(0,5),(5,6),(6,7)])

save("D06-dual-safety.png","内容安全与执行安全双链路","生成内容与用户代码采用独立但可审计的防护链路",[
((100,190,720,315),"内容生成输入","画像 + 课程知识库 + 生成任务","#4676A9"),
((100,405,720,545),"内容安全链","KnowledgeRetriever → ContentVerifier → SafetyAgent","#9B4B45"),
((100,680,720,825),"可发布资源","证据绑定、结构校验与安全状态","#526E3E"),
((880,190,1500,315),"用户代码输入","Python / C++ 源码与测试用例","#1F6E8C"),
((880,405,1500,545),"执行安全链","AST 审计 → 隔离子进程 → 超时/输出上限","#B06A2E"),
((880,680,1500,825),"判题与 Trace 证据","WA/AC/TLE/RE + 变量轨迹 + 诊断报告","#8A5C9E")],[(0,1),(1,2),(3,4),(4,5)])

save("D07-learning-loop.png","AlgoPilot 个性化学习闭环","画像、路径、资源、练习与评估持续互相校正",[
((540,175,1060,285),"六维学生画像","ProfilingAgent + 行为证据","#4676A9"),
((1050,360,1510,485),"个性化学习路径","Planner / LearningPath","#2F7469"),
((880,650,1400,785),"资源与 AI 辅导","六类资源 + Tutor/OJ 辅导","#8A5C9E"),
((200,650,720,785),"OJ / Trace 实践","真实代码、判题与轨迹证据","#B06A2E"),
((90,360,550,485),"掌握度与效果评估","Mastery / Evaluation / EventBus","#526E3E")],[(0,1),(1,2),(2,3),(3,4),(4,0)])

save("D08-dependency-categories.png","第三方依赖分类","依赖声明以 package.json、requirements.txt 与 THIRD_PARTY_LICENSES.md 为准",[
((100,200,720,350),"前端开源依赖","Vue / Router / Pinia / Element Plus / CodeMirror / Mermaid","#1F6E8C"),
((880,200,1500,350),"后端开源依赖","FastAPI / SQLAlchemy / Pydantic / pytest / Ruff / PyInstaller","#2F7469"),
((100,520,720,680),"运行与工具链","Node.js / npm / Python / C++ 编译器 / GDB","#B06A2E"),
((880,520,1500,680),"项目自有代码与数据","业务逻辑、编排框架、课程/OJ 数据与演示数据","#8A5C9E")],[])

save("D09-ai-review-flow.png","AI Coding 人工复核流程","AI 仅辅助生成与分析，最终责任由项目团队承担",[
((100,190,1500,285),"需求与约束确认","明确赛题、隐私、安全、许可证与可验证边界","#4676A9"),
((100,360,1500,455),"AI 辅助草拟","代码建议、测试建议、文档润色；不得自动采信","#8A5C9E"),
((100,530,720,660),"人工代码复核","架构一致性、边界条件、安全与依赖许可","#9B4B45"),
((880,530,1500,660),"自动化验证","Ruff / pytest / typecheck / build / 专项测试","#2F7469"),
((100,745,1500,840),"团队确认与发布","保留真实证据、修正文档、不隐藏失败与限制","#526E3E")],[(0,1),(1,2),(1,3),(2,4),(3,4)])
