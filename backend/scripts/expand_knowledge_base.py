"""生成扩充版 knowledge_base/chunks.json（80+ 条，每条约 300–800 字）。"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "knowledge_base" / "chunks.json"

MODULES = [
    ("array", "数组"),
    ("linked-list", "链表"),
    ("hash-table", "哈希表"),
    ("string", "字符串"),
    ("two-pointers", "双指针"),
    ("stack-queue", "栈与队列"),
    ("sorting", "排序算法"),
    ("binary-tree", "二叉树"),
    ("backtracking", "回溯"),
    ("greedy", "贪心"),
    ("dp", "动态规划"),
    ("monotonic-stack", "单调栈"),
    ("graph", "图论"),
]

CHUNK_SPECS = [
    (
        "concept",
        "概念详解",
        lambda mk, ml: (
            f"【{ml}·概念】{ml}是数据结构与算法课程的核心模块之一。"
            f"学习时应先建立抽象模型，再联系具体实现与复杂度。"
            f"大一计科学生需掌握：基本定义、适用场景、与相邻模块（如数组、链表、树）的对比，"
            f"以及在本平台 OJ 与模块进度中的对应题单。"
            f"讲解须避免跳步：从「问题是什么」到「为何选这种结构/技巧」再到「如何编码」。"
            f"与教材章节对应时，可引用《数据结构与算法》常见目录，勿编造不存在的章节号。"
            f"模块 key={mk}，教学辅助不直接给出可提交的完整竞赛答案。"
        ),
    ),
    (
        "example",
        "典型例题",
        lambda mk, ml: (
            f"【{ml}·例题】典型题型分层：入门（模拟/遍历）、进阶（优化边界）、综合（多技巧组合）。"
            f"以{ml}为例：先读清输入规模与约束，再选暴力→优化路径。"
            f"平台内建议用「思路+伪代码+复杂度」讲解，编程题只给框架与关键循环不变式。"
            f"常见标签：基础实现、双技巧结合、与哈希/栈/树等交叉。"
            f"批改时关注边界：空输入、单元素、重复元素、溢出与下标越界。"
            f"勿在讲解中虚构 LeetCode/力扣 四位题号；可描述题型名称如「两数之和」「反转链表」而不绑死题号。"
        ),
    ),
    (
        "common_error",
        "常见错误",
        lambda mk, ml: (
            f"【{ml}·易错点】学生常见误区：①未先画图/写不变式就写代码；②混淆 0/1 下标与「第 k 个」表述；"
            f"③忽略空表/单结点/全相同数据；④复杂度分析漏掉隐藏因子（如 sort、哈希查找均摊）。"
            f"在{ml}专题中，易把「能过样例」当成「理解正确」：需用反例自测。"
            f"调试建议：打印关键指针位置、小规模手推、对比暴力解。"
            f"AI 生成内容若与知识库矛盾（如声称哈希最坏 O(1) 无例外），应判为需修订。"
            f"鼓励用平台知识库片段对照，减少幻觉。"
        ),
    ),
    (
        "code_template",
        "代码模板",
        lambda mk, ml: (
            f"【{ml}·模板】Python3 教学模板结构：def solve(nums):  # 注释：输入含义\n"
            f"    # 1. 预处理（排序/哈希/前缀和等，视{ml}而定）\n"
            f"    # 2. 主循环/递归：写明循环变量含义与终止条件\n"
            f"    # 3. 返回结果\n"
            f"链表类注意 dummy = ListNode(0); cur = dummy。树类注意空结点 return。"
            f"回溯类：path.append → dfs → path.pop。DP 类：明确 dp[i] 含义与遍历方向。"
            f"模板 15～35 行含注释即可，禁止粘贴完整 OJ 可提交答案。"
            f"复杂度在注释末行标注：# 时间 O(? ) 空间 O(? )。"
        ),
    ),
    (
        "complexity",
        "复杂度分析",
        lambda mk, ml: (
            f"【{ml}·复杂度】分析步骤：界定基本操作、计数最坏/均摊、写清 n、m 含义。"
            f"数组访问 O(1)，尾部增删均摊 O(1)；链表按结点 O(1) 改链 O(1)，按值查找 O(n)。"
            f"哈希平均 O(1) 查找，最坏 O(n)；排序常作为预处理 O(n log n)。"
            f"树高 h：遍历 O(n)；BST 查找平均 O(log n) 最坏 O(n)。回溯常为指数级，需说明剪枝。"
            f"DP 时间与状态数、转移代价相关；单调栈均摊 O(n)。"
            f"生成内容若写「O(1)」须说明前提（如哈希、双指针在有序数组上），否则校验应提示修订。"
        ),
    ),
    (
        "pattern",
        "解题模式",
        lambda mk, ml: (
            f"【{ml}·模式】识别信号词：「连续子数组/子串」→滑动窗口或前缀和；"
            f"「有序+配对」→双指针；「频次/是否存在」→哈希；「下一个更大/矩形」→单调栈；"
            f"「选或不选」→回溯或 DP；「局部最优可证」→贪心。"
            f"{ml}模块内应能画出决策树：先判数据规模（n≤1e5 禁 O(n^2) 暴力），再选结构。"
            f"与前置模块衔接：学完数组/链表后再学{ml}，避免跳章。"
            f"平台路径 Agent 会按依赖排序，学习时以模块 key={mk} 打卡进度。"
        ),
    ),
    (
        "review",
        "复习要点",
        lambda mk, ml: (
            f"【{ml}·复习】自测清单：能否口述定义、画结构图、写模板、讲一道例题、列 3 个易错点。"
            f"建议间隔复习：第 1 天学概念+1 题，第 3 天混合题，第 7 天限时模拟。"
            f"与画像薄弱点联动：若 weak_points 含{ml}，资源库优先生成题单与讲解文档。"
            f"校验 Agent 对照本模块知识库切片；未通过校验的资源标为草稿，仅供参考。"
            f"完成度与正确率纳入学习效果评估的 mastery 维度，而非简单加分。"
        ),
    ),
]

SYNONYM_NOTE = {
    "binary-tree": ["BST", "二叉搜索树", "平衡树"],
    "hash-table": ["哈希", "map", "dict"],
    "dp": ["动态规划", "DP"],
    "two-pointers": ["双指针", "对撞指针", "快慢指针"],
    "sorting": ["排序", "稳定性", "归并排序", "快速排序", "堆排序", "TopK"],
    "graph": ["BFS", "DFS", "邻接表", "邻接矩阵", "visited", "ch06-graph", "graph-bfs-dfs"],
}

# 图论模块：与 ch06-graph、graph-bfs-dfs SkillCard、OJ Trace 对齐的专用切片
GRAPH_CHUNK_BODIES: dict[str, str] = {
    "concept": (
        "【图论·概念】图 G=(V,E) 是《数据结构与算法》核心结构，含顶点集与边集；"
        "需区分有向/无向、加权/无权。稀疏图用邻接表（遍历邻接点 O(deg)），"
        "稠密图可用邻接矩阵 O(1) 查边。BFS 用队列按层扩展，适合无权最短路层数；"
        "DFS 用栈或递归深入，适合连通分量、环检测与回溯前置。"
        "先修栈队列与二叉树遍历；平台 ch06-graph 学习页与 SkillCard graph-bfs-dfs 联动，"
        "OJ Trace 展示 queue 与 visited 快照。模块 key=graph，教学辅助不直接给出可提交完整答案。"
    ),
    "example": (
        "【图论·例题】典型分层：入门网格连通（岛屿数量，坐标 (r,c) 建模为结点）、"
        "标准图遍历（BFS 层数/DFS 连通块）、综合拓扑排序与环检测（课程表）。"
        "读题先判「无权最短路/层数」→BFS，「连通块/路径存在/环」→DFS 或并查集。"
        "平台建议思路+伪代码+复杂度；网格题注意四连通 dr/dc 方向数组。"
        "勿虚构 LeetCode 四位题号；可描述题型名称。结合 lab-05-graph-bfs-dfs 与 OJ Trace 手推访问序。"
    ),
    "common_error": (
        "【图论·易错点】①BFS 未在入队前标记 visited，同一结点重复入队导致 TLE；"
        "②DFS 递归前未标记 visited，重复扩展子树；③有向图只加单向边致路径不可达；"
        "④混淆 BFS 层数与 DFS 深度作为无权最短路答案；⑤网格题方向数组越界或八/四连通写错；"
        "⑥邻接表建无向图时重复加边致度数翻倍。调试：手画 6 顶点图对比 BFS/DFS 序，"
        "用 Trace 观察 queue 队首与 visited 集合；与 graph-bfs-dfs SkillCard 常见错误清单一致。"
    ),
    "code_template": (
        "【图论·模板】邻接表建图：graph = defaultdict(list)；graph[u].append(v)。"
        "BFS 骨架：from collections import deque\n"
        "def bfs(start):\n"
        "    q = deque([start]); visited = {start}\n"
        "    while q:\n"
        "        u = q.popleft()  # Trace 展示队首\n"
        "        for v in graph[u]:\n"
        "            if v not in visited:\n"
        "                visited.add(v); q.append(v)  # 入队前标记 visited\n"
        "DFS：def dfs(u): visited.add(u); ... 递归邻居。禁止粘贴完整 OJ 可提交答案。"
        "复杂度：BFS/DFS O(V+E)。网格图 V=行*列，E≈4V。"
    ),
    "complexity": (
        "【图论·复杂度】令 V 为顶点数、E 为边数。邻接表空间 O(V+E)，邻接矩阵 O(V²)。"
        "BFS/DFS 各访问边与点各一次，时间 O(V+E)；无权最短路 BFS 层扩展正确。"
        "稠密图 |E|≈V² 时矩阵可行；稀疏图 |E|≈V 优先邻接表。"
        "网格 n×m 建模为 V=nm 结点、E≈4nm 边。拓扑排序 O(V+E)。"
        "生成内容若写 BFS O(1) 须说明按边遍历；visited 集合均摊 O(1) 查重。"
    ),
    "pattern": (
        "【图论·模式】信号词：「最少步数/层数/无权最短路」→BFS；"
        "「连通分量/岛屿/能否到达」→DFS 或并查集；「依赖/先修课程」→拓扑排序；"
        "「网格四连通」→坐标转结点 ID。先判 n,m 规模选邻接表；学完 stack-queue 与 binary-tree 再学 graph。"
        "平台路径 Agent 按依赖排序；OJ 受挫时 SkillCard graph-bfs-dfs 触发 Trace 辅导。"
        "模块 key=graph，打卡 ch06-graph 与 lab-05-graph-bfs-dfs。"
    ),
    "review": (
        "【图论·复习】自测：口述邻接表/矩阵区别、手写 BFS/DFS 访问序、说明 visited 置 true 时机、"
        "讲一道网格或拓扑题。间隔复习：第 1 天概念+手画 6 顶点图，第 3 天混合 BFS/DFS 题，"
        "第 7 天限时 OJ。薄弱点含图论时资源库优先生成 Trace 动画与 graph-bfs-dfs 题单；"
        "校验 Agent 对照 ch06-graph 知识库；掌握度纳入 mastery 评估。"
    ),
}


def build_chunks() -> list[dict]:
    chunks: list[dict] = []
    for mk, ml in MODULES:
        extra_kw = SYNONYM_NOTE.get(mk, [])
        for suffix, title_suffix, body_fn in CHUNK_SPECS:
            cid = f"{mk}-{suffix}"
            if mk == "graph" and suffix in GRAPH_CHUNK_BODIES:
                body = GRAPH_CHUNK_BODIES[suffix]
            else:
                body = body_fn(mk, ml)
            # 填充到约 320–600 字
            while len(body) < 320:
                body += (
                    f" 延伸：结合{ml}完成平台小节与 OJ 练习，"
                    f"助教对话可引用模块 {mk} 的知识点，"
                    f"禁止编造外链与虚假题号。"
                )
            if len(body) > 780:
                body = body[:777] + "…"
            keywords = [ml, title_suffix, mk.replace("-", " ")] + extra_kw
            chunks.append(
                {
                    "id": cid,
                    "module_key": mk,
                    "title": f"{ml}·{title_suffix}",
                    "keywords": keywords,
                    "content": body,
                    "chunk_type": suffix,
                }
            )

    chunks.append(
        {
            "id": "course-overview",
            "module_key": "",
            "title": "课程总览与学习路径",
            "keywords": ["数据结构", "算法", "大一", "计科", "学习路径", "多智能体"],
            "content": (
                "本平台面向大一计算机专业《数据结构与算法》课程，主线模块顺序建议："
                "数组→链表→哈希表→字符串→双指针→栈与队列→排序算法→二叉树→回溯→贪心→动态规划→单调栈→图论。"
                "多智能体编排采用 DAG：知识库检索→角色 Agent 生成→ContentVerifier 校验→安全过滤→落库；"
                "校验未通过标为草稿。知识库切片按模块组织，检索使用 BM25 与同义词扩展（如 BST→二叉搜索树）。"
                "学习路径 Agent 在模块依赖 DAG 上做拓扑校验，启发式规划为主、LLM 润色为辅。"
                "画像 Agent 七维渐进抽取，评估 Agent 综合掌握度、持续性、练习与资源利用。"
                "教学辅助不直接提供可提交的完整竞赛答案；OJ 与模块进度联动。"
            )
            * 1,
            "chunk_type": "concept",
        }
    )
    return chunks


def main() -> None:
    data = build_chunks()
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(data)} chunks to {OUT}")


if __name__ == "__main__":
    main()
