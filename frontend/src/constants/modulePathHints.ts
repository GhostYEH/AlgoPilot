import type { ModulePhase } from './modules'

/** 各学习阶段目标说明 */
export const MODULE_PHASE_GOALS: Record<ModulePhase, string> = {
  foundation: '掌握线性结构与哈希映射，为后续算法题打牢基础。',
  technique: '熟练双指针、栈队列等经典技巧，提升解题模板化能力。',
  tree: '理解树形递归、回溯与搜索框架，应对中等难度综合题。',
  advanced: '攻克贪心、动态规划、单调栈与图论，形成高阶思维体系。',
}

export interface ModulePathHint {
  summary: string
  goals: string[]
  estHours: number
}

/** 各模块路径节点说明（学习路径 / 我的学习共用） */
export const MODULE_PATH_HINTS: Record<string, ModulePathHint> = {
  array: {
    summary: '数组是算法入门第一站，涵盖遍历、双指针雏形与二分思想。',
    goals: ['理解下标与区间', '掌握原地修改技巧', '完成力扣数组基础题单'],
    estHours: 6,
  },
  'linked-list': {
    summary: '链表训练指针思维与边界处理，是面试高频考点。',
    goals: ['熟练虚拟头结点', '掌握反转与快慢指针', '理解环与相交判定'],
    estHours: 8,
  },
  'hash-table': {
    summary: '哈希表提供 O(1) 查找，是两数之和、字母异位词等题的核心。',
    goals: ['选对 map / set', '处理计数与去重', '理解空间换时间权衡'],
    estHours: 7,
  },
  string: {
    summary: '字符串专题覆盖反转、KMP 入门与栈辅助解析。',
    goals: ['掌握双指针与滑动窗口', '理解字符统计模板', '完成字符串篇主刷题'],
    estHours: 8,
  },
  'two-pointers': {
    summary: '双指针统一有序数组、链表与去重类问题的解法框架。',
    goals: ['区分同向与相向指针', '掌握三数之和去重', '与哈希解法对比选型'],
    estHours: 6,
  },
  'stack-queue': {
    summary: '栈与队列支撑括号匹配、单调栈雏形与 BFS 前置知识。',
    goals: ['实现基础 ADT', '理解 FILO / FIFO', '为树层序与单调栈铺垫'],
    estHours: 5,
  },
  'binary-tree': {
    summary: '二叉树是递归与分治的核心载体，覆盖遍历、路径与 BST。',
    goals: ['统一前中后序框架', '掌握层序与属性题', '独立完成 30+ 经典题'],
    estHours: 20,
  },
  backtracking: {
    summary: '回溯通过「选择—探索—撤销」系统性搜索组合与排列解空间。',
    goals: ['画出决策树', '掌握剪枝时机', '区分排列与组合模板'],
    estHours: 10,
  },
  greedy: {
    summary: '贪心在每步做局部最优选择，需证明正确性后快速编码。',
    goals: ['识别贪心性质', '掌握区间与分配类题', '与 DP 对比选型'],
    estHours: 8,
  },
  dp: {
    summary: '动态规划将重叠子问题与最优子结构转化为状态转移方程。',
    goals: ['定义状态与转移', '区分一维与二维 DP', '完成背包与 LIS 经典题'],
    estHours: 15,
  },
  'monotonic-stack': {
    summary: '单调栈在 O(n) 内解决「下一个更大元素」等邻域极值问题。',
    goals: ['维护单调递增/递减栈', '理解索引存栈', '对接每日温度等题'],
    estHours: 6,
  },
  graph: {
    summary: '图论覆盖最短路、拓扑排序与并查集，是竞赛与面试进阶内容。',
    goals: ['掌握 BFS / DFS 建图', '理解 Dijkstra 与 Floyd', '规划专题周计划'],
    estHours: 12,
  },
}
