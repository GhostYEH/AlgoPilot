## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9
- width: 1280
- height: 720
- safe_margin_x: 56
- safe_margin_top: 46
- safe_margin_bottom: 42

## narrative
- mode: narrative
- core_message: AlgoPilot 不是简单的 AI 聊天机器人或 OJ，而是一套能记住学习状态、解释代码错误并据此重规划学习路径的全流程智能学习系统。
- title_voice: 结论式、推进式；标题必须推动“断裂 → 闭环 → 证据 → 工程 → 价值”的叙事，不用中性栏目名充当标题。
- notes_register: 中文口语化答辩；先结论，再沿一条主路径解释；主动说明边界。

## visual_style
- visual_style: blueprint
- visual_mix_blueprint: 70
- visual_mix_isometric: 20
- visual_mix_data_stage: 10
- image_rendering: blueprint
- image_palette: tech-neon
- image_rendering_behavior: 深色工程图纸、细线网格、单一结构线色、模块连线、数据流箭头、尺寸线和关键路径高亮；所有可读文字与事实标注保留在原生 SVG 层。
- isometric_behavior: 仅 Slide 07、08、09 使用局部低透视等距模型；立体结构只解释层级与依赖，不承载长文本，不使用装饰性漂浮模块。
- data_stage_behavior: 仅 Slide 01、04、20 使用数据产品舞台；低亮背景、克制发光轨迹、一个焦点，不生成虚构 UI 或图表。
- forbidden: purple gradients; glass panels; meaningless particles; floating orbs; excessive rounded cards; large-radius containers; decorative neon everywhere; generic AI brain; fake UI; fake charts; template card grids; shadows as hierarchy
- card_policy: 卡片不是默认容器；只有并列事实确需边界时使用，radius 0-6，默认 2，无阴影。
- grid_policy: 背景网格低对比、线宽 1；不得穿过正文；不得成为视觉噪音。

## colors
- bg: #071521
- secondary_bg: #10283B
- primary: #4CC9F0
- accent: #FFB703
- secondary_accent: #52B788
- body_text: #F3F7FA
- text_secondary: #A9C2D3
- text_tertiary: #6E8CA0
- border: #24455B
- grid: #163246
- warning: #FF6B6B
- code_bg: #0B1D2A
- color_rule: 每页不超过五个语义颜色角色；accent 只标记关键路径或转折；secondary_accent 只标记通过、完成与验证状态。

## typography
- title_family: Noto Sans SC, Segoe UI, sans-serif
- body_family: Noto Sans SC, Segoe UI, sans-serif
- code_family: Consolas, Noto Sans SC, monospace
- cover_title: 88
- hero_headline: 72
- section_title: 64
- title: 54
- subtitle: 42
- body: 32
- annotation: 24
- technical_label: 24
- footnote: 18
- page_number: 18
- title_weight: 700
- subtitle_weight: 600
- body_weight: 400

## typography_policy
- formula_policy: text-only
- typography_rule: 不得通过缩小正文解决信息过载；删减、拆分视觉层级或转移到讲稿。

## stroke_and_geometry
- grid_stroke: 1
- minor_stroke: 1.5
- structure_stroke: 2
- key_path_stroke: 4
- default_radius: 2
- max_radius: 6
- shadow: none
- glow: only on Slide 01, 04, 20 key path; restrained
- border_color_policy: structural borders use #24455B; screenshot focus frames may use #4CC9F0; warning borders only for a verified error state; status colors should appear in paths, dots, fills, or text instead of competing container outlines
- border_accent_limit: at most one non-warning border accent color per page

## icons
- library: tabler-outline
- min_size: 32
- preferred_size: 40
- effective_stroke: 2.4-3
- allowed:
  - tabler-outline/user-scan
  - tabler-outline/route-2
  - tabler-outline/robot
  - tabler-outline/database
  - tabler-outline/code
  - tabler-outline/scan-traces
  - tabler-outline/shield-check
  - tabler-outline/test-pipe-2
  - tabler-outline/school
  - tabler-outline/network
- emoji: forbidden
- generic_icon_mix: forbidden

## images
- rendering: blueprint
- palette: tech-neon
- ai_path: host-native
- source_mix: ai + provided
- text_policy: none
- ai_guardrail: AI 图片只承担氛围与抽象系统空间；禁止虚构产品界面、事实数据、图表、用户案例和中文标签。
- ai_allowed_pages: 01, 04, 20 only
- ai_forbidden_content: any text; numbers; product UI; dashboards; charts; named modules; labeled architecture; unverified technical structure; fake data; fake features
- allowed_files:
  - cover_blueprint_hero.png
  - product_stage_atmosphere.png
  - closing_path_hero.png
  - homepage.png
  - learning-path.png
  - oj-trace-workbench.png
  - teacher-dashboard.png
- hero_pages:
  - 01: cover_blueprint_hero.png
  - 04: product_stage_atmosphere.png + homepage.png
  - 20: closing_path_hero.png
- screenshot_pages:
  - 04: K:/A3latest/presentation/assets/screenshots/homepage.png
  - 06: K:/A3latest/presentation/assets/screenshots/teacher-dashboard.png
  - 10: K:/A3latest/presentation/assets/screenshots/learning-path.png
  - 12: K:/A3latest/presentation/assets/screenshots/oj-trace-workbench.png
- screenshot_rule: 真实截图不得被 AI 重绘；使用原生 SVG 热点、尺寸线、焦点框与状态标签解释。
- screenshot_version_rule: only the four locked current-workspace sources; no cross-version screenshot mixing
- screenshot_viewport: 16:9 normalized delivery frame, target 1680x945
- screenshot_crop_rule: homepage top-first 2550x1434; learning-map centered 1084x610; OJ full 1680x945; teacher top-first 1680x945
- screenshot_annotation_rule: max 4 hotspots; 2px cyan straight-corner focus frame; numbered dots; single-line leader; monospace label; no shadow

## diagram_authoring
- editable_svg_only: architecture; data flow; learning loop; multi-agent topology; resource topology; anti-hallucination flow; data ownership
- ai_architecture_diagrams: forbidden
- isometric_source: native SVG geometry only
- text_layer: all labels, facts, numbers, node names and status markers remain editable SVG text

## content_facts
- agent_registry: 22 registered; 20 implemented; 2 planned extension nodes; 6 layers
- resource_types: 5 A3 core resources + 1 extension reading resource
- resource_topology: document -> mindmap||exercises -> code_case -> trace_animation||reading
- verification_retries: max 2
- rag: Okapi BM25; k1 1.5; b 0.75; top_k 4
- trace: Python sys.settrace + C++ GDB MI; 13 visualization components; max 200 steps
- oj: Python + C++; default 3 second timeout; AST audit; dangerous call blocking
- database: 8 ORM tables in current frozen repository; user_id ownership applies per model contract
- api: 67 FastAPI HTTP route decorators in current frozen repository
- frontend: 73 component Vue files; 23 view Vue files; 24 named routes; 13 algorithm game components
- content_assets: 126 OJ problems; 13 skill cards; 14 chapters + 6 labs + 2 projects
- archived_test_result: 188 passed; 0 failed; 1 warning; executed 2026-07-12; commit pending
- current_test_result: 190 passed; 0 failed; 1 warning; executed 2026-07-13 at commit dc3e1503fdffaa7c778f83192048c58785cc5870
- frontend_verification: typecheck passed; production build passed in 2.43 seconds
- limitation: current OJ/Trace is a lightweight course-learning execution environment, not a production public sandbox

## page_rhythm
- 01: anchor
- 02: dense
- 03: anchor
- 04: anchor
- 05: breathing
- 06: breathing
- 07: dense
- 08: dense
- 09: dense
- 10: breathing
- 11: anchor
- 12: anchor
- 13: dense
- 14: dense
- 15: dense
- 16: breathing
- 17: anchor
- 18: dense
- 19: breathing
- 20: anchor

## page_visual_language
- 01: data-stage + blueprint hero
- 02: blueprint broken-chain diagram
- 03: blueprint closed loop
- 04: data-stage + real screenshot
- 05: blueprint event path
- 06: blueprint + real screenshot
- 07: blueprint + local isometric model
- 08: blueprint + local isometric model
- 09: blueprint + local isometric model
- 10: blueprint + real screenshot
- 11: blueprint protocol convergence
- 12: blueprint + real screenshot
- 13: blueprint dual safety lanes
- 14: blueprint data ownership graph
- 15: blueprint evidence mapping
- 16: blueprint innovation radial
- 17: blueprint data hero
- 18: blueprint asset ledger
- 19: blueprint value paths + real screenshot
- 20: data-stage + blueprint closing hero

## page_core_messages
- 01: 系统不止回答问题，而是记住状态、解释错误并重规划下一步。
- 02: 五个典型痛点的根因是学习链路彼此断裂。
- 03: 动态画像、路径规划、资源生成、训练执行、诊断评估和动态调整形成六个不重复阶段，调整结果回写画像与路径。
- 04: 核心学习链路已经落到真实可操作的平台界面。
- 05: 一次错误会进入事件、记忆、掌握度与路径调整链路。
- 06: 学生反馈与教师学情来自同一条真实数据证据链。
- 07: 所有 AI 请求都经过统一编排、知识检索、校验和安全治理。
- 08: 多智能体价值来自六层职责分工，而不是数量堆砌。
- 09: 并行发生在有数据依赖依据的位置。
- 10: 个性化由持久化状态驱动，而不是一次性 Prompt。
- 11: Python 与 C++ 追踪被归一为同一套可视化协议。
- 12: 判题、Trace 与深度诊断发生在同一工作台。
- 13: 内容可靠性与代码执行安全由两条独立防线治理。
- 14: 学习记忆必须建立在账号级数据归属与角色隔离上。
- 15: A3 核心要求都有代码、API 或页面状态证据。
- 16: 创新在于把生成重新接回学习过程。
- 17: 188 个后端用例全部通过，核心链路进入自动化验证。
- 18: 产品、内容与工程资产共同构成项目完成度。
- 19: 当前可运行与可演示能力必须和后续生产化升级项明确分开。
- 20: 让错误留下证据，让系统知道下一步。

## pptx_structure
- mode: baseline
- page_role_mapping: cover/toc/section/ending/content markers on SVG roots; no reusable layout distillation requested
- native_objects: false

## execution
- total_pages: 20
- generation_mode: continuous
- refine_spec: true
- source_language: zh
- page_order: sequential
- one_core_conclusion_per_page: required
- svg_authoring: handwritten sequential pages only
- live_preview: start before page 01
- first_page_gate: required before page 02
- full_quality_gate: required before notes and export
- notes: required at notes/total.md
