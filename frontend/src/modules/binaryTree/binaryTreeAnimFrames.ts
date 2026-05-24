/** 二叉树各节分步动画帧（算法与 LeetCode 题意对齐） */

export type TreeKind = 'demo' | 'bst'

export interface TreeNodeDef {
  id: string
  label: string
  cx: number
  cy: number
}

/** 演示树 1(2(4,5), 3) */
export const DEMO_NODES: TreeNodeDef[] = [
  { id: '1', label: '1', cx: 110, cy: 18 },
  { id: '2', label: '2', cx: 70, cy: 58 },
  { id: '3', label: '3', cx: 150, cy: 58 },
  { id: '4', label: '4', cx: 50, cy: 92 },
  { id: '5', label: '5', cx: 90, cy: 92 },
]

export const DEMO_EDGES: [string, string][] = [
  ['1', '2'],
  ['1', '3'],
  ['2', '4'],
  ['2', '5'],
]

/** BST 8(4(2,6), 12) */
export const BST_NODES: TreeNodeDef[] = [
  { id: '8', label: '8', cx: 110, cy: 18 },
  { id: '4', label: '4', cx: 70, cy: 58 },
  { id: '12', label: '12', cx: 150, cy: 58 },
  { id: '2', label: '2', cx: 50, cy: 92 },
  { id: '6', label: '6', cx: 90, cy: 92 },
]

export const BST_EDGES: [string, string][] = [
  ['8', '4'],
  ['8', '12'],
  ['4', '2'],
  ['4', '6'],
]

export interface AnimFrame {
  hot: string[]
  done?: string[]
  dim?: string[]
  path?: string[]
  labels?: Record<string, string>
  stack?: string[]
  queue?: string[]
  /** 栈顶在数组第一项（UI 左侧） */
  p?: string
  q?: string
  lca?: string
  note?: string
  /** 106 / 654 / 617 等构造类辅助文案 */
  arrays?: { title: string; items: string[]; hotIdx?: number[] }[]
}

export type SectionFrames = Record<string, AnimFrame[]>

const ALL_DONE_DEMO = ['1', '2', '3', '4', '5']

/** 前序迭代：栈顶 = stack[0] */
const PREORDER_STACK: AnimFrame[] = [
  { hot: ['1'], stack: ['1'], note: '根入栈' },
  { hot: ['1'], done: ['1'], stack: ['2', '3'], note: '弹出 1 visit；先压右 3 再压左 2（栈顶 2）' },
  { hot: ['2'], done: ['1'], stack: ['4', '5'], note: '弹出 2 visit；压右 5、左 4' },
  { hot: ['4'], done: ['1', '2'], stack: ['5'], note: '弹出 4 visit' },
  { hot: ['5'], done: ['1', '2', '4'], stack: ['3'], note: '弹出 5 visit' },
  { hot: ['3'], done: ['1', '2', '4', '5'], stack: [], note: '弹出 3 visit；前序序列 1→2→4→5→3' },
]

/** 统一迭代模板：中序（空标记法简化示意） */
const INORDER_UNIFIED: AnimFrame[] = [
  { hot: ['4'], stack: ['4', '2', '1'], note: '一路向左压栈至最左 4' },
  { hot: ['4'], done: ['4'], stack: ['2', '1'], note: '弹出 4 visit（中序第一个）' },
  { hot: ['2'], done: ['4'], stack: ['5', '2', '1'], note: '处理 2：压右子 5 后 visit 2' },
  { hot: ['5'], done: ['4', '2'], stack: ['1'], note: '弹出 5 visit' },
  { hot: ['1'], done: ['4', '2', '5'], stack: ['3', '1'], note: '弹出 1 visit' },
  { hot: ['3'], done: ['4', '2', '5', '1'], stack: [], note: '弹出 3；中序 4→2→5→1→3' },
]

export const SECTION_FRAMES: SectionFrames = {
  theory: [
    { hot: ['1'], note: 'BST：左 < 根 < 右（本演示树仅作形状示意）' },
    { hot: ['2', '3', '4', '5'], done: ['1'], note: 'BFS：队列一层层扩展（见层序遍历）' },
    { hot: ['2', '4', '5'], done: ['1'], note: 'DFS 前序：根 → 左 → 右' },
    { hot: ['4', '2', '5', '1', '3'], done: ALL_DONE_DEMO, note: 'DFS 中序：左 → 根 → 右' },
    { hot: ['4', '5', '2', '3', '1'], done: ALL_DONE_DEMO, dim: [], note: 'DFS 后序：左 → 右 → 根' },
  ],
  'traversal-iterative': PREORDER_STACK,
  'unified-traversal': INORDER_UNIFIED,
  'level-order': [
    { hot: ['1'], queue: ['1'], note: '根入队；处理第 1 层 → 记录 1' },
    { hot: ['2', '3'], done: ['1'], queue: ['2', '3'], note: '第 2 层：2、3 入队出队；记录 2' },
    { hot: ['4', '5'], done: ['1', '2', '3'], queue: ['4', '5'], note: '第 3 层：4、5 出队；记录 4（每层第一个）' },
    { hot: ['4'], done: ALL_DONE_DEMO, note: '结果 [[1],[2,3],[4,5]]' },
  ],
  'symmetric-tree': [
    { hot: ['2', '3'], note: '比较外侧镜像对 (2, 3)' },
    { hot: ['4', '5'], done: ['2', '3'], note: '比较内侧对 (4, 5)' },
    { hot: ['1'], done: ['2', '3', '4', '5'], note: '子树均对称 → true' },
    { hot: ['1'], done: ALL_DONE_DEMO, note: '整棵树关于根轴镜像' },
  ],
  'max-depth': [
    { hot: ['4', '5'], labels: { '4': '1', '5': '1' }, note: '叶结点深度 = 1' },
    { hot: ['2', '3'], done: ['4', '5'], labels: { '2': '2', '3': '1' }, note: '2：1+max(1,1)=2；3 为叶深度 1' },
    { hot: ['1'], done: ['2', '3', '4', '5'], labels: { '1': '3' }, note: '根：1+max(2,1)=3' },
    { hot: ['1'], done: ALL_DONE_DEMO, labels: { '1': '3' }, note: '最大深度 3' },
  ],
  'min-depth': [
    { hot: ['4', '5'], labels: { '4': '1', '5': '1' }, note: '左子树最浅叶深度 1' },
    { hot: ['3'], labels: { '3': '1' }, note: '右子仅 3：到叶路径更短' },
    { hot: ['1'], labels: { '1': '2' }, note: '根：1+min(左深, 右深)=2' },
    { hot: ['1'], done: ALL_DONE_DEMO, labels: { '1': '2' }, note: '最小深度 2（路径 1→3）' },
  ],
  'count-nodes': [
    { hot: ['4', '5'], note: '叶结点各计 1' },
    { hot: ['2', '3'], done: ['4', '5'], note: '2、3：左子树个数+右子树个数+1' },
    { hot: ['1'], done: ['2', '3', '4', '5'], note: '根：总计 5 个结点' },
    { hot: ['1'], done: ALL_DONE_DEMO, note: '返回 5' },
  ],
  'balanced-tree': [
    { hot: ['4', '5'], note: '自底向上计算高度' },
    { hot: ['2'], done: ['4', '5'], labels: { '2': '|1−1|≤1' }, note: '结点 2 左右高度差 ≤1' },
    { hot: ['1'], done: ['2', '4', '5'], note: '整棵树高度平衡' },
    { hot: ['1'], done: ALL_DONE_DEMO, note: '返回 true' },
  ],
  'all-paths': [
    { hot: ['1', '2', '4'], path: ['1', '2', '4'], note: '路径 1→2→4' },
    { hot: ['1', '2', '5'], path: ['1', '2', '5'], note: '路径 1→2→5' },
    { hot: ['1', '3'], path: ['1', '3'], note: '路径 1→3' },
    { hot: ['1'], done: ALL_DONE_DEMO, note: '输出 [[1,2,4],[1,2,5],[1,3]]' },
  ],
  'sum-left-leaves': [
    { hot: ['4', '2'], note: '4 是 2 的左叶子 → +4' },
    { hot: ['3'], done: ['4'], note: '3 无左叶子' },
    { hot: ['1'], done: ['2', '3', '4'], note: '左叶子之和 = 4' },
    { hot: ['1'], done: ALL_DONE_DEMO, note: '返回 4' },
  ],
  'find-bottom-left': [
    { hot: ['1'], queue: ['1'], note: '层序：处理第 1 层，记录 1' },
    { hot: ['2', '3'], done: ['1'], queue: ['2', '3'], note: '第 2 层第一个 2' },
    { hot: ['4', '5'], done: ['1', '2', '3'], queue: ['4', '5'], note: '第 3 层第一个 4（最左）' },
    { hot: ['4'], done: ALL_DONE_DEMO, note: '返回 4（不是 5：同层 4 更靠左）' },
  ],
  'path-sum': [
    { hot: ['1', '2', '4'], path: ['1', '2', '4'], labels: { '4': '和=7' }, note: 'target=7：路径 1→2→4' },
    { hot: ['1', '3'], path: ['1', '3'], labels: { '3': '和=4' }, note: '路径 1→3 和为 4 ≠ 7' },
    { hot: ['1', '2', '4'], done: ['1', '2', '4'], path: ['1', '2', '4'], note: '存在根到叶路径和 = 7 → true' },
    { hot: ['1', '2', '4'], done: ALL_DONE_DEMO, path: ['1', '2', '4'], note: '返回 true' },
  ],
  'lowest-common-ancestor': [
    { hot: ['4'], p: '4', note: '在左子树找到 p=4' },
    { hot: ['5'], q: '5', done: ['4'], note: '在右子树找到 q=5' },
    { hot: ['2'], lca: '2', p: '4', q: '5', note: '左右子树均非空 → 当前结点 2 为 LCA' },
    { hot: ['2'], lca: '2', done: ALL_DONE_DEMO, note: '返回结点 2（236 后序）' },
  ],
  'build-tree-in-post': [
    {
      hot: [],
      arrays: [
        { title: 'inorder', items: ['9', '3', '15'] },
        { title: 'postorder', items: ['9', '15', '3'] },
      ],
      note: '给定中序 + 后序',
    },
    {
      hot: [],
      arrays: [
        { title: 'inorder', items: ['9', '3', '15'], hotIdx: [1] },
        { title: 'postorder', items: ['9', '15', '3'], hotIdx: [2] },
      ],
      note: 'post 末元素 3 为根；inorder 中 mid=1',
    },
    {
      hot: ['1'],
      arrays: [
        { title: '左 post', items: ['9'] },
        { title: '右 post', items: ['15'] },
      ],
      note: '左段 [9]、右段 [15] 递归建树 → 3(9,15)',
    },
    { hot: ['1'], done: ['1'], note: '返回根 3（示意用结点 1 代表根位）' },
  ],
  'maximum-binary-tree': [
    {
      hot: [],
      arrays: [{ title: 'nums', items: ['3', '2', '1', '6', '0', '5'], hotIdx: [3] }],
      note: '找最大值 6 作为根',
    },
    { hot: ['2', '3'], note: '左段 [3,2,1] 递归建左子树' },
    { hot: ['3'], done: ['2'], note: '右段 [0,5] 递归建右子树' },
    { hot: ['1'], done: ALL_DONE_DEMO, note: '得到最大二叉树' },
  ],
  'merge-trees': [
    {
      hot: ['1', '2'],
      arrays: [
        { title: 't1', items: ['1', '+', '3', '2'] },
        { title: 't2', items: ['2', '1', 'null', '3'] },
      ],
      note: '两树对应结点同时非空 → 值相加',
    },
    { hot: ['2', '3'], note: '递归 merge(left) 与 merge(right)' },
    { hot: ['1'], done: ['2', '3'], note: '一方为空则接另一方子树' },
    { hot: ['1'], done: ALL_DONE_DEMO, note: '合并完成' },
  ],
  'bst-search': [
    { hot: ['8'], note: 'target=6：6 < 8 → 走左子树' },
    { hot: ['4'], done: ['8'], note: '6 > 4 → 走右子树' },
    { hot: ['6'], done: ['8', '4'], note: '命中结点 6' },
    { hot: ['6'], done: ALL_DONE_DEMO, note: '返回结点 6' },
  ],
  'validate-bst': [
    { hot: ['2'], note: '中序第一个 2' },
    { hot: ['4'], done: ['2'], note: '2 < 4 ✓' },
    { hot: ['6'], done: ['2', '4'], note: '4 < 6 ✓' },
    { hot: ['8'], done: ['2', '4', '6'], note: '6 < 8 ✓' },
    { hot: ['12'], done: ['2', '4', '6', '8'], note: '8 < 12 ✓；合法 BST' },
  ],
  'bst-min-diff': [
    { hot: ['2'], note: '中序遍历，维护 prev' },
    { hot: ['4'], done: ['2'], labels: { '4': 'diff=2' }, note: '|4−2|=2' },
    { hot: ['6'], done: ['2', '4'], labels: { '6': 'diff=2' }, note: '最小差仍为 2' },
    { hot: ['8'], done: ['2', '4', '6'], note: '继续扫描…最小差 2' },
  ],
  'bst-modes': [
    { hot: ['2'], note: '中序统计频次' },
    { hot: ['4'], done: ['2'], note: '众数候选 2、4…' },
    { hot: ['6'], done: ['2', '4'], note: '更新出现次数' },
    { hot: ['2', '4'], done: ALL_DONE_DEMO, note: '返回众数（本树示例）' },
  ],
  'bst-lca': [
    { hot: ['8'], p: '2', q: '6', note: 'p=2、q=6 均 < 8 → 向左' },
    { hot: ['4'], lca: '4', p: '2', q: '6', done: ['8'], note: '2<4 且 6>4 → 分叉，LCA=4' },
    { hot: ['4'], lca: '4', done: ALL_DONE_DEMO, note: '返回 4（235：自上而下）' },
  ],
  'bst-insert': [
    { hot: ['8'], note: '插入 5：5 < 8 → 左' },
    { hot: ['4'], done: ['8'], note: '5 > 4 → 右' },
    { hot: ['6'], done: ['8', '4'], note: '5 < 6 → 作为 4 的右孩子（示意）' },
    { hot: ['6'], done: ALL_DONE_DEMO, note: '插入完成' },
  ],
  'bst-delete': [
    { hot: ['8'], note: '删除目标在 BST 中定位' },
    { hot: ['4', '12'], done: ['8'], note: '若为叶/单子：直接替换' },
    { hot: ['6'], note: '若为双子女：用中序后继替换' },
    { hot: ['4'], done: ALL_DONE_DEMO, note: '删除完成' },
  ],
  'bst-trim': [
    { hot: ['8'], note: '根在 [low,high] 内则保留' },
    { hot: ['4', '12'], note: '递归修剪左右子树' },
    { hot: ['2', '6'], note: '去掉 <low 或 >high 的子树' },
    { hot: ['4'], done: ALL_DONE_DEMO, note: '修剪后的 BST' },
  ],
  'sorted-array-to-bst': [
    { hot: ['8'], arrays: [{ title: 'nums', items: ['-10', '-3', '0', '5', '9'], hotIdx: [2] }], note: '取中点作根' },
    { hot: ['4', '2'], done: ['8'], note: '左半递归建左子树' },
    { hot: ['12', '6'], done: ['8', '4', '2'], note: '右半递归建右子树' },
    { hot: ['8'], done: ALL_DONE_DEMO, note: '平衡 BST 构造完成' },
  ],
  'bst-to-greater-sum': [
    { hot: ['12'], note: '反序中序：先右子树' },
    { hot: ['8'], done: ['12'], labels: { '8': '+12' }, note: '再根，累加 greater' },
    { hot: ['6'], done: ['12', '8'], labels: { '6': '+20' }, note: '最后左子树' },
    { hot: ['2'], done: ALL_DONE_DEMO, labels: { '2': '+26' }, note: '每个结点加上右侧所有结点之和' },
  ],
}

export function treeKindForSection(sectionId: string): TreeKind {
  const bst = new Set([
    'bst-search',
    'validate-bst',
    'bst-min-diff',
    'bst-modes',
    'bst-lca',
    'bst-insert',
    'bst-delete',
    'bst-trim',
    'sorted-array-to-bst',
    'bst-to-greater-sum',
  ])
  return bst.has(sectionId) ? 'bst' : 'demo'
}

export function maxStepForSection(id: string): number {
  const frames = SECTION_FRAMES[id]
  if (frames?.length) return Math.max(0, frames.length - 1)
  if (id === 'invert-tree') return 3
  const summary = new Set(['summary', 'checkpoint-1', 'checkpoint-2', 'checkpoint-3', 'checkpoint-4'])
  if (summary.has(id)) return 0
  return 2
}

export function frameForSection(sectionId: string, step: number): AnimFrame | null {
  const frames = SECTION_FRAMES[sectionId]
  if (!frames?.length) return null
  return frames[Math.min(step, frames.length - 1)] ?? frames[0]
}

export function nodeRole(
  id: string,
  frame: AnimFrame,
): 'hot' | 'done' | 'dim' | 'p' | 'q' | 'lca' | 'path' | 'default' {
  if (frame.lca === id) return 'lca'
  if (frame.p === id) return 'p'
  if (frame.q === id) return 'q'
  if (frame.path?.includes(id)) return 'path'
  if (frame.hot.includes(id)) return 'hot'
  if (frame.done?.includes(id)) return 'done'
  if (frame.dim?.includes(id)) return 'dim'
  return 'default'
}
