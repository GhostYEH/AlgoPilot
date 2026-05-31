import type { GuideTableBlock } from '@/modules/shared/moduleRegistry'
import type { LearnSection } from '@/modules/shared/learningTypes'

export { leetcodeCnUrl } from '@/modules/shared/learningTypes'

export const GRAPH_INTRO =
  '图由顶点与边组成，是描述网络、地图、依赖关系与网格题的统一模型。本章对齐课程 ch06-graph 与 SkillCard graph-bfs-dfs：从基本概念与邻接存储入手，掌握 BFS（层序扩展）与 DFS（深度探索），并规避 visited、队列/栈误用等高频坑。每节含分步示意与代码骨架，可在右侧 AI 助教提问或一键跳转资源生成。'

const base = (s: LearnSection): LearnSection => s

export const GRAPH_SECTIONS: LearnSection[] = [
  base({
    id: 'theory',
    title: '1. 图的基本概念',
    subtitle: '顶点 · 边 · 有向/无向 · 权重',
    difficulty: '入门',
    estMinutes: 25,
    keywords: ['图', '顶点', '边', 'ch06-graph'],
    overview:
      '图 G=(V,E) 由顶点集 V 与边集 E 构成。理解「有向/无向」「加权/无权」是选题与建图的第一步；网格题可将 (r,c) 视为结点，四连通/八连通视为边。',
    topicBlocks: [
      {
        title: '一、顶点、边与度',
        points: [
          '顶点（结点）：图中的实体，如城市、课程、网格坐标。',
          '边：连接两个顶点的关系；无向边 (u,v) 可双向走，有向边 u→v 只能单向。',
          '度 deg(u)：与 u 相连的边数；有向图分入度、出度。',
          '路径：沿边依次经过的顶点序列；环是首尾相同的路径。',
        ],
      },
      {
        title: '二、有向图、无向图与权重',
        points: [
          '无向图：社交好友、无向道路；建图时 u—v 常需双向加边。',
          '有向图：课程先修、任务依赖；只加 u→v，BFS 层数表示「最少步数」而非物理距离。',
          '加权图：边带权 w；无权最短路用 BFS，带权最短路需 Dijkstra 等（本章先掌握 BFS）。',
          '连通分量：极大连通子图；DFS/BFS 外层循环可统计分量个数（如岛屿数量）。',
        ],
      },
    ],
    points: [
      '稀疏图 |E|≪|V|² 优先邻接表；稠密图或小 V 可用邻接矩阵。',
      '网格 (r,c) 可映射为 id = r*cols+c，四方向 dr/dc = ±1,0。',
    ],
    checklist: [
      '能写出 G=(V,E) 并区分有向/无向',
      '知道度、路径、环、连通分量的含义',
      '看到网格题能想到「图建模」',
    ],
  }),
  base({
    id: 'representation',
    title: '2. 邻接矩阵与邻接表',
    subtitle: '存储方式 · 时空权衡',
    difficulty: '入门',
    estMinutes: 20,
    keywords: ['邻接表', '邻接矩阵'],
    points: [
      '邻接矩阵 adj[i][j]：O(1) 查边，空间 O(V²)，适合 V≤500 或稠密图。',
      '邻接表 adj[i]=[邻居…]：空间 O(V+E)，遍历邻居 O(deg)，竞赛/面试主流。',
      '建图：读入边 (u,v) 时无向图 adj[u].push(v) 且 adj[v].push(u)；有向只 push 单向。',
      'Python 常用 defaultdict(list)；C++ 用 vector<vector<int>>。',
    ],
    codeSketch: `# 邻接表建图（无向图示例）
n, m = map(int, input().split())
adj = [[] for _ in range(n)]
for _ in range(m):
    u, v = map(int, input().split())
    adj[u].append(v)
    adj[v].append(u)  # 有向图则只 append(v)`,
    complexityHint: '邻接表存图 O(V+E)；遍历所有边 O(V+E)。',
  }),
  base({
    id: 'bfs',
    title: '3. 广度优先搜索 BFS',
    subtitle: '队列 · 层序扩展 · 无权最短路',
    difficulty: '基础',
    estMinutes: 30,
    keywords: ['BFS', '队列', 'graph-bfs-dfs'],
    overview:
      'BFS 从起点出发，按「层」向外扩展：先入队的先访问。边权均为 1 时，BFS 第一次到达某点的层数即最短路长度。实现用队列；**入队时即标记 visited**，避免重复入队 TLE。',
    points: [
      '模板：起点入队并标记 → while 队列非空：出队 u → 扩展未访问邻居 v 入队并标记。',
      '层序遍历：每次处理当前 queue.size() 个结点，即一层。',
      '适用：无权最短路、最少步数、扩散染色（岛屿、 rotten orange）。',
    ],
    pitfalls: [
      '出队时才标记 visited → 同一结点多次入队 → TLE。',
      '有向图只加了单向边，导致「可达」判断错误。',
      '把 BFS 层数当成带权图最短路（权非 1 时应用 Dijkstra）。',
    ],
    codeSketch: `from collections import deque

def bfs(adj, start):
    n = len(adj)
    visited = [False] * n
    q = deque([start])
    visited[start] = True
    order = []
    while q:
        u = q.popleft()
        order.append(u)
        for v in adj[u]:
            if not visited[v]:
                visited[v] = True
                q.append(v)
    return order`,
    main: { id: 200, title: '岛屿数量', slug: 'number-of-islands' },
    checklist: ['能手写 BFS 框架', '理解「入队即 visited」', '知道 BFS 求无权最短路'],
  }),
  base({
    id: 'dfs',
    title: '4. 深度优先搜索 DFS',
    subtitle: '递归 / 栈 · 连通性 · 回溯前置',
    difficulty: '基础',
    estMinutes: 30,
    keywords: ['DFS', '递归', '栈'],
    overview:
      'DFS 沿一条路径尽可能深入，走不通再回溯。可用递归（隐式栈）或显式栈模拟。适合连通分量、环检测、路径存在性、网格染色与回溯类前置。',
    points: [
      '递归模板：标记 u → 访问 u → 对每个未访问邻居递归 dfs(v)。',
      '迭代：栈 push 起点；pop u 后 push 未访问邻居（注意顺序与递归版一致）。',
      '统计连通分量：for 每个未访问 i，dfs(i) 且分量数 +1。',
      '网格 DFS：四方向递归，越界或已访问则 return。',
    ],
    codeSketch: `def dfs(adj, u, visited, order):
    visited[u] = True
    order.append(u)
    for v in adj[u]:
        if not visited[v]:
            dfs(adj, v, visited, order)

def dfs_all(adj):
    n = len(adj)
    visited = [False] * n
    order = []
    for i in range(n):
        if not visited[i]:
            dfs(adj, i, visited, order)
    return order`,
    related: [{ id: 207, title: '课程表', slug: 'course-schedule' }],
    checklist: ['递归与栈两种 DFS 能互说', '能写连通分量计数外层循环'],
  }),
  base({
    id: 'pitfalls',
    title: '5. 常见错误与调试',
    subtitle: 'visited · 队列/栈 · 重复访问 · 连通分量',
    difficulty: '基础',
    estMinutes: 20,
    keywords: ['visited', 'TLE', '易错点'],
    points: [
      'visited 标记时机：BFS 在**入队时**标记；DFS 在**进入结点时**标记（递归开头或栈 pop 后）。',
      '队列/栈误用：BFS 必须用队列（FIFO）；DFS 用递归或栈（LIFO），勿混用导致顺序错误。',
      '重复访问：网格题忘记 mark grid[r][c]，或 BFS 出队才 mark，导致指数级重复。',
      '连通分量遗漏：只从起点 BFS/DFS 一次，未对未访问结点再启动 → 漏计岛屿/分量。',
      '方向数组：四连通 [[1,0],[-1,0],[0,1],[0,-1]] 写错符号或行列混淆。',
    ],
    pitfalls: [
      '网格题用全局 visited 却未在 dfs 入口检查边界与障碍字符。',
      '有向图拓扑题误当无向图双向加边。',
      '混淆「路径长度」与「DFS 递归深度」。',
    ],
    checklist: [
      '能说出 BFS 与 DFS 各自 visited 写在哪一行',
      '知道何时需要外层 for 扫全图',
    ],
  }),
  base({
    id: 'practice',
    title: '6. 实操与 OJ',
    subtitle: '网格 BFS/DFS · 拓扑 · lab-05',
    difficulty: '进阶',
    estMinutes: 40,
    keywords: ['200', '207', 'OJ'],
    points: [
      '200 岛屿数量：网格 1/0，四连通分量计数 — DFS/BFS 染色均可。',
      '207 课程表：有向图环检测 — DFS 三色标记或 Kahn 拓扑（BFS 入度）。',
      '实验 lab-05-graph-bfs-dfs：对 6 顶点无向图手写 BFS/DFS 序。',
      'Trace 调试时关注 queue / visited / stack 快照（skill graph-bfs-dfs）。',
    ],
    main: { id: 200, title: '岛屿数量', slug: 'number-of-islands' },
    related: [
      { id: 207, title: '课程表', slug: 'course-schedule' },
      { id: 994, title: '腐烂的橘子', slug: 'rotting-oranges' },
    ],
  }),
  base({
    id: 'summary',
    title: '7. 图论篇总结',
    subtitle: 'BFS vs DFS · 选用指南',
    difficulty: '入门',
    estMinutes: 10,
    keywords: ['总结', 'graph-bfs-dfs'],
    points: [
      '无权最短路 / 最少步数 / 层序 → BFS + 队列。',
      '连通性 / 路径 / 环 / 网格染色 / 回溯前置 → DFS。',
      '建图先想清楚有向无向；稀疏图用邻接表；网格映射结点 id。',
      '生成资源建议：document（BFS vs DFS）、code_case（邻接表模板）、trace_animation（queue 变化）。',
    ],
  }),
]

export const GRAPH_COUNT = GRAPH_SECTIONS.length

export const GRAPH_EXTRA: GuideTableBlock[] = [
  {
    sectionId: 'representation',
    title: '邻接矩阵 vs 邻接表',
    columns: [
      { prop: 'aspect', label: '维度', width: 100 },
      { prop: 'matrix', label: '邻接矩阵', minWidth: 160 },
      { prop: 'list', label: '邻接表', minWidth: 160 },
    ],
    data: [
      { aspect: '空间', matrix: 'O(V²)', list: 'O(V+E)' },
      { aspect: '查边 u—v', matrix: 'O(1)', list: 'O(deg(u))' },
      { aspect: '遍历所有边', matrix: 'O(V²)', list: 'O(V+E)' },
      { aspect: '适用', matrix: 'V 小、稠密图', list: '稀疏图、竞赛主流' },
    ],
  },
  {
    sectionId: 'summary',
    title: 'BFS vs DFS 选用',
    columns: [
      { prop: 'scene', label: '场景', width: 120 },
      { prop: 'pick', label: '选用', minWidth: 100 },
      { prop: 'reason', label: '原因', minWidth: 200 },
    ],
    data: [
      { scene: '无权最短路', pick: 'BFS', reason: '第一次到达即最少边数' },
      { scene: '连通分量计数', pick: 'DFS/BFS', reason: '外层 for + 一次遍历' },
      { scene: '环检测（有向）', pick: 'DFS', reason: '三色标记或拓扑' },
      { scene: '层序打印', pick: 'BFS', reason: '天然按层扩展' },
    ],
  },
]
