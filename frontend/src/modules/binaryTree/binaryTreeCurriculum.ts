/** 二叉树学习模块 — 34 节 + 4 篇周末总结 */

import type { GuideTableBlock } from '@/modules/shared/moduleRegistry'
import type { LearnSection } from '@/modules/shared/learningTypes'
import { leetcodeCnUrl } from '@/modules/shared/learningTypes'
import { applyBinaryTreeEnrichment } from './binaryTreeEnrichment'

export { leetcodeCnUrl }

export const BINARY_TREE_INTRO =
  '二叉树是面试最高频的结构之一。本章按 34 节顺序：从种类与存储、DFS/BFS 遍历框架入手，再练属性与路径、构造与 BST，最后用四篇周末总结串起来。每节含分主题讲解、对照表、易错点与力扣链接；建议第 1 节先通读打地基，再手敲 144/94/102 等模板题。'

const base = (s: LearnSection): LearnSection => s

const BINARY_TREE_SECTIONS_RAW: LearnSection[] = [
  base({
    id: 'theory',
    title: '1. 二叉树理论基础',
    subtitle: '种类 · 存储 · DFS/BFS 框架 · TreeNode · 与 STL 的关系',
    difficulty: '入门',
    estMinutes: 55,
    keywords: ['满二叉树', '完全二叉树', 'BST', 'AVL', '红黑树', 'DFS', 'BFS', '堆', 'map'],
    overview:
      '本节对应《二叉树理论基础篇》，不重复教科书定义，而是把后面 30+ 道题都依赖的「种类、存储、遍历框架、结点写法」一次讲透。建议配合 B 站公开课《关于二叉树，你该了解这些！》一起看。学完应能：① 判断一棵树属于哪一类；② 说出 DFS/BFS 分别用什么结构实现；③ 白纸写出 TreeNode；④ 知道 map/set 与 unordered_map 的底层差异。',
    topicBlocks: [
      {
        title: '一、二叉树的种类（解题时先想清楚是哪种树）',
        intro: '力扣里常见两类「形状」：满二叉树、完全二叉树；常见两类「有序」：二叉搜索树、平衡二叉搜索树。',
        points: [
          '满二叉树：只有度为 0（叶）和度为 2 的结点，且所有叶在同一层。深度为 k 时结点总数为 2^k − 1（例如深度 3 共 7 个结点）。',
          '完全二叉树：除最底层外每层都满；最底层结点从左到右连续排列，右侧可以缺结点。堆（优先级队列）= 完全二叉树 + 父子之间的大小关系（大根堆/小根堆）。',
          '易混：左右子树「对称」≠ 完全二叉树。完全二叉树看的是最底层是否靠左填满，不是看是否镜像对称。',
          '二叉搜索树（BST）：有数值约束——左子树所有值 < 根 < 右子树所有值，左右子树也分别是 BST。中序遍历得到升序序列，这是后面验证 BST、求最值/众数/累加树的基础。',
          '平衡二叉搜索树（AVL 等）：在 BST 上再加「左右子树高度差绝对值 ≤ 1」。最后一棵「根左右高差 > 1」的树不是平衡 BST。',
          '红黑树：一种平衡二叉搜索树，不是与 AVL 并列的另一种「树种类」。C++ 的 map、set、multimap、multiset 底层是红黑树，增删查 O(log n)。',
          'unordered_map / unordered_set 底层是哈希表，不是二叉搜索树；写算法分析性能时不要和 map/set 混为一谈。',
        ],
      },
      {
        title: '二、存储方式：链式 vs 顺序',
        intro: '力扣默认链式；理解顺序存储有助于理解堆在数组里的下标关系。',
        points: [
          '链式存储：每个结点含 val、left、right 指针，结点地址不必连续——面试与刷题最常见，利于理解递归。',
          '顺序存储：用数组按下标存结点。若父结点下标为 i，则左孩子 2i+1、右孩子 2i+2（下标从 0 起）。',
          '顺序存储适合完全二叉树（堆）；一般二叉树用数组会浪费空间，所以教程与面试更强调链式。',
          '知道「数组也能表示树」即可；实现遍历题时仍以链式 + 递归/栈/队列为思路主线。',
        ],
      },
      {
        title: '三、遍历方式：DFS 与 BFS 两大框架',
        intro: '二叉树题目本质是：选对遍历顺序 + 在「访问结点 / 递归返回」时写什么逻辑。先把框架记住，后面每节只改「单层逻辑」。',
        points: [
          '深度优先（DFS）：先往深处走，到叶再回溯。分为前序、中序、后序——差别只在「根（中）」何时被处理：前序「中左右」、中序「左中右」、后序「左右中」。',
          '广度优先（BFS）：一层一层扫，即层序遍历。实现用队列：根入队，每次处理当前层 size 个结点，再把非空孩子入队。',
          'DFS 在代码里常用递归（系统栈）或显式栈模拟；BFS 用队列。栈与队列的应用场景在这里串起来。',
          '递归写 DFS 时后面会强调「递归三部曲」；迭代写法见第 3～4 节，层序模板见第 5 节。',
          'Morris 遍历：把迭代空间降到 O(1) 的进阶技巧，面试极少考，有时间可了解，不作为主线。',
        ],
      },
      {
        title: '四、结点定义与面试习惯',
        intro: '力扣已给出 TreeNode 时也要能自己写——现场笔试常考。',
        points: [
          '链式结点与链表类似，多一个指向右孩子的指针：val、left、right。',
          'C++ 常写构造函数 `TreeNode(int x) : val(x), left(NULL), right(NULL) {}`，便于 `new TreeNode(9)`；不写构造函数则每次要手动赋值三个字段。',
          'Java / TypeScript / Python 各有标准写法（见下方「实现骨架」）；语言不同，但「两个子指针 + 值」模型一致。',
          'Rust 力扣题为 `Option<Rc<RefCell<TreeNode>>>`，理解概念即可，不必与本节 C++/TS 写法强行统一。',
        ],
      },
      {
        title: '五、与后续章节的衔接',
        points: [
          '第 2～4 节：前/中/后序的递归与迭代（144、94、145）。',
          '第 5 节：层序与一堆变形（102、107、199、637…）。',
          '第 8～17 节：在遍历框架上改「单层逻辑」求深度、路径、对称等。',
          '第 22 节起：BST 专题——务必记住「中序 = 有序数组」。',
          '第 34 节总结篇：按题型选前序/后序/中序/层序的对照表，学完可回去填自检。',
        ],
      },
    ],
    points: [
      '形状：满（叶同层、度 0/2）· 完全（底层靠左，堆的基础）。',
      '有序：BST（中序升序）· 平衡 BST（map/set 底层，O(log n)）。',
      '存储：链式 left/right；顺序 parent i → 左 2i+1、右 2i+2。',
      'DFS 前/中/后 = 根在左中右何处；BFS = 层序 + 队列。',
      '写题先选框架，再写单层逻辑；面试能白纸写 TreeNode。',
    ],
    pitfalls: [
      '把红黑树与 AVL 当成两种互斥的树——红黑树是平衡 BST 的一种实现。',
      '把「对称」或「只有最后一层缺几个结点但不在左侧连续」当成完全二叉树。',
      '用 unordered_map 的性能去类比 map——前者哈希 O(1) 均摊，后者树 O(log n)。',
      '只背前中后序名词，说不清「中」指根结点被访问的时机。',
    ],
    checklist: [
      '能各举一例说明满二叉树、完全二叉树、BST、非平衡 BST 的区别。',
      '能口述：DFS 用栈/递归，BFS 用队列；前中后序分别对应哪种「中」的位置。',
      '能在 1 分钟内白纸写出你所用语言的 TreeNode 定义。',
      '能说明 priority_queue 与 map 分别对应哪种底层结构。',
    ],
    complexityHint:
      '遍历一棵 n 结点树：时间 O(n)，DFS 递归栈 O(h)（h 为高度），BFS 队列 O(w)（w 为最大层宽）。BST 查找平均 O(log n)，退化成链时 O(n)。',
    codeSketch: `// C++（常见风格，面试手写）
struct TreeNode {
    int val;
    TreeNode *left;
    TreeNode *right;
    TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
};

// TypeScript（力扣常见）
class TreeNode {
  val: number
  left: TreeNode | null
  right: TreeNode | null
  constructor(val?: number, left?: TreeNode | null, right?: TreeNode | null) {
    this.val = val ?? 0
    this.left = left ?? null
    this.right = right ?? null
  }
}

// Java
// public class TreeNode {
//   int val; TreeNode left, right;
//   TreeNode() {}
//   TreeNode(int val) { this.val = val; }
//   TreeNode(int val, TreeNode left, TreeNode right) { ... }
// }`,
  }),
  base({
    id: 'traversal-recursive',
    title: '2. 二叉树的递归遍历',
    subtitle: '递归三部曲 · 144 / 94 / 145',
    difficulty: '基础',
    estMinutes: 50,
    keywords: ['144', '94', '145', '递归三部曲', 'DFS'],
    points: [
      '要点：写递归按「三部曲」——① 参数与返回值 ② 终止条件 ③ 单层逻辑；不要靠玄学。',
      '前序 144：中左右，先 visit 根；适合复制树、前缀表达式。',
      '中序 94：左中右；BST 上得有序序列。',
      '后序 145：左右中；适合先处理子树再处理根（高度、删树、LCA 等）。',
      '终止：`if (!cur) return`；空树合法。',
      '同一棵树三种序列只差 visit 根的位置；模板统一为「处理当前 → 左 → 右」调换顺序。',
      '掌握递归后可做 N 叉树 589/590（孩子列表代替 left/right）。',
    ],
    pitfalls: [
      '混用三种顺序的 visit 位置。',
      '终止条件写成 `left==null` 却漏掉 `right==null` 的叶结点情况。',
    ],
    checklist: [
      '能默写递归三部曲并套用到 144。',
      '对同一棵树口述三种遍历序列。',
    ],
    complexityHint: 'O(n) 时间，O(h) 递归栈。',
    related: [
      { id: 144, title: '二叉树的前序遍历', slug: 'binary-tree-preorder-traversal' },
      { id: 94, title: '二叉树的中序遍历', slug: 'binary-tree-inorder-traversal' },
      { id: 145, title: '二叉树的后序遍历', slug: 'binary-tree-postorder-traversal' },
    ],
    codeSketch: `// 前序：void dfs(TreeNode* cur, vector<int>& out) {
//   if (!cur) return;
//   out.push_back(cur->val);      // 中
//   dfs(cur->left, out);          // 左
//   dfs(cur->right, out);         // 右
// }
// 中序：先左 → out.push_back → 右
// 后序：先左 → 右 → out.push_back`,
  }),
  base({
    id: 'traversal-iterative',
    title: '3. 二叉树的迭代遍历',
    subtitle: '栈模拟递归 · 空结点入栈两种写法',
    difficulty: '基础',
    estMinutes: 50,
    keywords: ['栈', '迭代', '144', '94', '145'],
    points: [
      '前序迭代：根入栈；while 非空：pop visit，先压右再压左。',
      '中序迭代：cur 一路向左入栈；pop visit 后 cur=cur.right。',
      '后序：双栈或「根右左」遍历再 reverse；或记录上次访问结点防重复。',
      '前序可「空结点也入栈」或「仅非空孩子入栈」，逻辑等价，后者更清晰。',
      '面试常问：递归 vs 迭代——时间相近，递归多栈开销；工程里深递归要防溢出，面试手写递归通常可接受。',
    ],
    pitfalls: ['前序压栈顺序反了（须先右后左）。', '后序迭代易死循环。'],
    checklist: ['能手写中序迭代。', '能口述前序「空结点入栈」与「非空入栈」差别。'],
    complexityHint: 'O(n) 时间，O(h) 栈空间。',
    related: [
      { id: 144, title: '二叉树的前序遍历', slug: 'binary-tree-preorder-traversal' },
      { id: 94, title: '二叉树的中序遍历', slug: 'binary-tree-inorder-traversal' },
      { id: 145, title: '二叉树的后序遍历', slug: 'binary-tree-postorder-traversal' },
    ],
    codeSketch: `// 前序（非空孩子入栈）
// while (!st.empty()) {
//   auto node = st.top(); st.pop();
//   res.push_back(node->val);
//   if (node->right) st.push(node->right);
//   if (node->left)  st.push(node->left);
// }`,
  }),
  base({
    id: 'unified-traversal',
    title: '4. 二叉树的统一迭代法',
    subtitle: '空指针标记 · 一套栈写法切换前中后序',
    difficulty: '进阶',
    estMinutes: 40,
    keywords: ['统一迭代', '空标记', '栈'],
    points: [
      '弹栈遇到真实结点：按序压回「空标记 + 子树」，通过调整「中」的位置切换前/中/后序。',
      '不必强求日常刷题都用统一法，但面试可能要求「写一种迭代」——至少精通一种。',
      '理解空标记后，能解释栈中结点与 visit 顺序的对应关系。',
    ],
    pitfalls: ['空标记与真实结点处理顺序搞混，导致重复 visit。'],
    checklist: ['能说出统一法中「中」在前序/中序/后序各对应哪种压栈顺序。'],
    complexityHint: 'O(n) 时间，栈可能含空标记，空间 O(n)。',
    codeSketch: `// 中序统一法示意：弹到结点时压 (null, node, right, null, left)
// 弹到 null 时 visit 上一个真实结点`,
  }),
  base({
    id: 'level-order',
    title: '5. 二叉树的层序遍历',
    subtitle: '队列 + size 固定层界 · 102 及变形',
    difficulty: '基础',
    estMinutes: 40,
    keywords: ['102', 'BFS', '层序', '107', '199', '637'],
    points: [
      '模板：根入队；while 队列非空：sz=size，循环 sz 次 pop，记录值，push 非空孩子。',
      '本质是图论 BFS 在树上的应用。',
      '掌握模板后可刷：102 层序、107 自底向上、199 右视图、637 层平均、429 N 叉树层序、515 每层最大值等。',
      '变形只在「单层逻辑」：收集方式、过滤条件、多叉孩子循环。',
    ],
    pitfalls: ['不用 size 界定当前层，导致层序错乱。', 'push 孩子前未判空。'],
    checklist: ['能手写返回二维数组的层序模板。', '能说明 199 右视图与层序的关系。'],
    complexityHint: 'O(n) 时间，O(w) 空间，w 为最大层宽。',
    main: { id: 102, title: '二叉树的层序遍历', slug: 'binary-tree-level-order-traversal' },
    related: [
      { id: 107, title: '二叉树的层序遍历 II', slug: 'binary-tree-level-order-traversal-ii' },
      { id: 199, title: '二叉树的右视图', slug: 'binary-tree-right-side-view' },
      { id: 637, title: '二叉树的层平均值', slug: 'average-of-levels-in-binary-tree' },
    ],
    codeSketch: `// vector<vector<int>> levelOrder(TreeNode* root) {
//   if (!root) return {};
//   queue<TreeNode*> q; q.push(root);
//   vector<vector<int>> ans;
//   while (!q.empty()) {
//     int sz = q.size(); vector<int> layer;
//     for (int i = 0; i < sz; ++i) {
//       auto node = q.front(); q.pop();
//       layer.push_back(node->val);
//       if (node->left)  q.push(node->left);
//       if (node->right) q.push(node->right);
//     }
//     ans.push_back(move(layer));
//   }
//   return ans;
// }`,
  }),
  base({
    id: 'invert-tree',
    title: '6. 翻转二叉树',
    subtitle: '226 · 交换左右孩子 · 前序最直观',
    difficulty: '入门',
    estMinutes: 30,
    keywords: ['226', '镜像', '前序'],
    points: [
      '递归前序：先 swap(left,right)，再递归左右（最直观）。',
      '注意：递归「中序」若写法则会对同一结点 swap 两次，不是真中序翻转；统一迭代的中序栈写法可以。',
      '层序/栈：每结点弹出时交换其孩子指针。',
      '翻转是遍历章节的串联题：任选已学遍历均可实现。',
    ],
    pitfalls: ['用错误的中序递归导致翻转两次还原。'],
    checklist: ['能手写前序递归翻转。', '能解释为何朴素递归中序不合适。'],
    main: { id: 226, title: '翻转二叉树', slug: 'invert-binary-tree' },
    codeSketch: `// TreeNode* invertTree(TreeNode* root) {
//   if (!root) return nullptr;
//   swap(root->left, root->right);
//   invertTree(root->left);
//   invertTree(root->right);
//   return root;
// }`,
  }),
  base({
    id: 'checkpoint-1',
    title: '7. 二叉树周末总结（一）',
    subtitle: '遍历 · 层序 · 翻转 · 周一～周六答疑精华',
    difficulty: '入门',
    estMinutes: 25,
    keywords: ['周末总结', '遍历', '迭代'],
    points: [
      '周一：红黑树属于平衡 BST；TreeNode 构造函数便于 new；Morris 了解即可。',
      '周二：递归三部曲固化；144/94/145 掌握后可做 589/590 N 叉树遍历。',
      '周三：迭代前序空结点入栈 vs 非空入栈均可；递归方便理解，迭代省系统栈但工程深递归要防溢出。',
      '周四：统一迭代不必强求日常都用，但面试可能追问「能否写迭代」。',
      '周五：层序 = BFS 模板，102 后连续刷 107/199/637/515 等变形。',
      '周六：翻转用前序最自然；递归中序翻转会 swap 两次；栈模拟的中序统一法可以。',
      '本周串讲：理论 → DFS 递归/迭代/统一 → BFS 层序 → 226 翻转。',
    ],
    checklist: [
      '能不看资料复述递归三部曲。',
      '能默写层序模板并说出 199 与层序关系。',
    ],
  }),
  base({
    id: 'symmetric-tree',
    title: '8. 对称二叉树',
    subtitle: '101 · 两棵子树镜像比较 · 可推广 100/572',
    difficulty: '基础',
    estMinutes: 35,
    keywords: ['101', '镜像', '100', '572'],
    points: [
      '本质：比较左子树与右子树是否镜像，不是单层「左右指针相等」。',
      '递归：compare(L,R) 比 (L.left,R.right) 与 (L.right,R.left)；两空真，一空假，值不等假。',
      '迭代：队列成对放入要比较的结点（不是普通层序）。',
      '改比较顺序可得 100.相同的树；572.另一棵树的子树 几乎同代码。',
    ],
    pitfalls: ['只比较根的左右孩子，未递归内侧/外侧对。'],
    checklist: ['能手写递归 compare。', '能说明如何改写成 100。'],
    main: { id: 101, title: '对称二叉树', slug: 'symmetric-tree' },
    related: [
      { id: 100, title: '相同的树', slug: 'same-tree' },
      { id: 572, title: '另一棵树的子树', slug: 'subtree-of-another-tree' },
    ],
    codeSketch: `// bool compare(TreeNode* l, TreeNode* r) {
//   if (!l && !r) return true;
//   if (!l || !r || l->val != r->val) return false;
//   return compare(l->left, r->right) && compare(l->right, r->left);
// }`,
  }),
  base({
    id: 'max-depth',
    title: '9. 二叉树的最大深度',
    subtitle: '104 · 后序高度 / 前序深度回溯',
    difficulty: '入门',
    estMinutes: 30,
    keywords: ['104', '深度', '高度', '后序'],
    points: [
      '本题深度 = 结点个数；力扣按结点计，根深度为 1。',
      '后序：return 1 + max(leftDepth, rightDepth)，空返回 0；根的高度即树深。',
      '前序也可：带 depth 参数向下，叶处更新全局 max，回溯时 depth--（真正「求深度」直觉）。',
      '层序：记录层数即可。',
    ],
    pitfalls: ['混淆深度（根到结点）与高度（结点到叶）的定义。'],
    checklist: ['能写后序 O(n) 解法。', '能口述前序回溯版为何算「真深度」。'],
    main: { id: 104, title: '二叉树的最大深度', slug: 'maximum-depth-of-binary-tree' },
    codeSketch: `// 后序
// int depth(TreeNode* node) {
//   if (!node) return 0;
//   return 1 + max(depth(node->left), depth(node->right));
// }`,
  }),
  base({
    id: 'min-depth',
    title: '10. 二叉树的最小深度',
    subtitle: '111 · 到最近叶子 · 单子树分支',
    difficulty: '基础',
    estMinutes: 35,
    keywords: ['111', '最小深度', '叶子'],
    points: [
      '最小深度：根到最近叶子结点的结点个数；叶子 = 左右孩子都空。',
      '若左空右非空：不能只取左深 0，应只走有子的一侧。',
      '后序：左右深度取 min+1，单独处理单子树；或前序/层序找第一层叶子。',
    ],
    pitfalls: ['直接套用最大深度模板，忽略「必须到叶子」。'],
    checklist: ['能画出单子树为何 min 在右侧。'],
    main: { id: 111, title: '二叉树的最小深度', slug: 'minimum-depth-of-binary-tree' },
    codeSketch: `// int minDepth(TreeNode* root) {
//   if (!root) return 0;
//   if (!root->left && !root->right) return 1;
//   if (!root->left) return 1 + minDepth(root->right);
//   if (!root->right) return 1 + minDepth(root->left);
//   return 1 + min(minDepth(root->left), minDepth(root->right));
// }`,
  }),
  base({
    id: 'count-nodes',
    title: '11. 完全二叉树的节点个数',
    subtitle: '222 · 利用完全性 O(log²n)',
    difficulty: '进阶',
    estMinutes: 40,
    keywords: ['222', '完全二叉树'],
    points: [
      '朴素遍历 O(n)。',
      '完全树：算左子树最左深度、右子树最左深度；相等则左子满，节点数 2^h-1 + 右子规模。',
      '不等则递归右子，左规模 + 1 + 右结果。',
    ],
    pitfalls: ['把非完全树当完全树用公式。'],
    checklist: ['能口述优化思路。'],
    main: { id: 222, title: '完全二叉树的节点个数', slug: 'count-complete-tree-nodes' },
  }),
  base({
    id: 'balanced-tree',
    title: '12. 平衡二叉树',
    subtitle: '110 · 后序高度 · -1 哨兵',
    difficulty: '基础',
    estMinutes: 35,
    keywords: ['110', '平衡', '高度差'],
    points: [
      '平衡：任一结点 |左高−右高| ≤ 1。',
      '朴素每结点算高 O(n²)；优化后序返回高度，不平衡返回 -1。',
      '深度 vs 高度：力扣按结点计深度；迭代模拟回溯求平衡效率低。',
      '迭代技巧：模拟前中后序用栈；层序用队列；拿不准先栈后队列试。',
    ],
    pitfalls: ['前序算「深度」与后序算「高度」混用。'],
    checklist: ['能手写 -1 哨兵后序。'],
    main: { id: 110, title: '平衡二叉树', slug: 'balanced-binary-tree' },
    codeSketch: `// int getHeight(TreeNode* node) {
//   if (!node) return 0;
//   int L = getHeight(node->left);
//   if (L == -1) return -1;
//   int R = getHeight(node->right);
//   if (R == -1) return -1;
//   if (abs(L - R) > 1) return -1;
//   return 1 + max(L, R);
// }`,
  }),
  base({
    id: 'all-paths',
    title: '13. 二叉树的所有路径',
    subtitle: '257 · 前序 + 回溯 · 隐藏回溯',
    difficulty: '基础',
    estMinutes: 40,
    keywords: ['257', '回溯', '路径'],
    points: [
      '前序遍历，path 记录当前路径；到叶时加入答案。',
      '回溯：递归返回前 path.pop()；精简写法 `dfs(left, path+"->")` 里 path 未改，函数返回即回溯。',
      '若写成 `tmp=path+"->"; dfs(left,tmp)` 则失去回溯效果——要理解区别。',
      '路径题与回溯相伴；先看懂展开版再记精简版。',
    ],
    pitfalls: ['忘记在回溯时 pop path。', '非叶结点也当终点加入。'],
    checklist: ['能画出 path 在递归栈上的变化。', '能解释 path+"->" 为何等价回溯。'],
    main: { id: 257, title: '二叉树的所有路径', slug: 'binary-tree-paths' },
    codeSketch: `// void dfs(TreeNode* node, string path, vector<string>& ans) {
//   if (!node) return;
//   path += to_string(node->val);
//   if (!node->left && !node->right) { ans.push_back(path); return; }
//   path += "->";
//   dfs(node->left, path, ans);
//   dfs(node->right, path, ans);
// }`,
  }),
  base({
    id: 'checkpoint-2',
    title: '14. 二叉树周末总结（二）',
    subtitle: '属性题 · 深度/高度 · 路径回溯',
    difficulty: '入门',
    estMinutes: 25,
    keywords: ['周末总结', '100', '572'],
    points: [
      '周一：101 比较两棵子树；队列成对比较非层序；改序得 100/572。',
      '周二：104 后序求高=最大深度；前序带 depth 回溯是「真深度」写法。',
      '周三：111 最小深度必须到叶子；单子树只走有子一侧。',
      '周四：222 在会 104/111 后应能快速完成。',
      '周五：110 澄清深度/高度；后序+哨兵；迭代求平衡不推荐。',
      '周六：257 回溯藏在 path 传值；建议先写展开版再精简；简短代码易忘回溯。',
      '属性题先明确递归返回值含义，再写代码。',
    ],
    checklist: ['能复述 257 回溯为何在 path+"->" 中。', '能区分 104 后序 vs 前序写法。'],
  }),
  base({
    id: 'sum-left-leaves',
    title: '15. 左叶子之和',
    subtitle: '404 · 父结点判断左叶子',
    difficulty: '基础',
    estMinutes: 35,
    keywords: ['404', '左叶子', '后序'],
    points: [
      '左叶子定义：父的左孩子，且该孩子左右都空；仅左孩子非空不算。',
      '不能只看「左子树」：例：只有右链的树左叶子和为 0。',
      '须通过父结点判断：`node->left && !node->left->left && !node->left->right`。',
      '后序：左+右+中（中处判断左叶子取值）；迭代前序/层序均可。',
    ],
    pitfalls: ['把「最左结点」当成左叶子。', '在叶结点自身判断自己是左叶子（缺父信息）。'],
    checklist: ['能口述左叶子判定条件。'],
    main: { id: 404, title: '左叶子之和', slug: 'sum-of-left-leaves' },
    codeSketch: `// if (root->left && !root->left->left && !root->left->right)
//   sum += root->left->val;`,
  }),
  base({
    id: 'find-bottom-left',
    title: '16. 找树左下角的值',
    subtitle: '513 · 最深最左 · 层序或 DFS',
    difficulty: '基础',
    estMinutes: 30,
    keywords: ['513', '层序', 'DFS'],
    points: [
      '最后一层最左边结点 = 深度最大的叶子中靠左的。',
      '层序：每层第一个出队，最后记录的值即答案。',
      'DFS：先左后右，维护 maxDepth 与对应值（含回溯）。',
    ],
    pitfalls: ['只找最左未保证最深。'],
    checklist: ['能写层序 O(n) 解。'],
    main: { id: 513, title: '找树左下角的值', slug: 'find-bottom-left-tree-value' },
  }),
  base({
    id: 'path-sum',
    title: '17. 路径总和',
    subtitle: '112 是否存在 · 113 收集路径 · 返回值语义',
    difficulty: '基础',
    estMinutes: 45,
    keywords: ['112', '113', '路径和', 'bool 返回值'],
    points: [
      '112：前序，target -= val，到叶且 target==0 为 true；可用 bool 返回值「搜一条边」。',
      '113：到叶且和满足时收集 path，回溯 pop。',
      '递归返回值：搜整棵树 often void；搜一条符合条件路径用 bool；后序根据左右信息推中节点用 int/TreeNode*。',
      '222/110 等需要子树信息返回值的题，要遍历完整棵树，不能找到就 early return 整棵（除非题目允许）。',
    ],
    pitfalls: ['112 未到叶就返回 true。', '113 忘记回溯 pop。'],
    checklist: ['能说明何时用 bool 返回值。'],
    main: { id: 112, title: '路径总和', slug: 'path-sum' },
    related: [{ id: 113, title: '路径总和 II', slug: 'path-sum-ii' }],
  }),
  base({
    id: 'build-tree-in-post',
    title: '18. 从中序与后序构造二叉树',
    subtitle: '106 · 切区间 · 前序+中序 105',
    difficulty: '进阶',
    estMinutes: 55,
    keywords: ['106', '105', '构造', '区间'],
    points: [
      '后序尾为根；中序定位根，左段为左子树中序，右段为右子树中序。',
      '左子树结点个数决定后序如何切左右段；哈希存中序下标 O(1) 找根。',
      '区间坚持同一套开闭（常用左闭右闭 [left,right]）；前序+中序 105 同套路。',
      '仅有前序+后序无法唯一确定二叉树（缺中序无法分割左右）。',
    ],
    pitfalls: ['区间边界 off-by-one。', '后序/前序根被重复使用。'],
    checklist: ['能手画 106 的区间切分。'],
    main: { id: 106, title: '从中序与后序遍历序列构造二叉树', slug: 'construct-binary-tree-from-inorder-and-postorder-traversal' },
    related: [
      { id: 105, title: '从前序与中序遍历序列构造二叉树', slug: 'construct-binary-tree-from-preorder-and-inorder-traversal' },
    ],
    codeSketch: `// 左闭右闭 [l,r)：根=post[postR-1]；在中序找 mid；
// 左子树：in[l,mid), post[...]；右子树：in[mid+1,r), post[...]`,
  }),
  base({
    id: 'maximum-binary-tree',
    title: '19. 最大二叉树',
    subtitle: '654 · 数组分治 · 下标切分',
    difficulty: '进阶',
    estMinutes: 45,
    keywords: ['654', '分治', '前序'],
    points: [
      '区间最大值作根；左半建左子树，右半建右子树；构造题多用前序思维。',
      '优化：用下标 [left,right) 在原数组上切，避免每次 vector 拷贝。',
      '空区间 return nullptr；允许空指针进递归则少写 if，终止改为 left>=right。',
    ],
    pitfalls: ['每次 split 新数组导致 TLE。'],
    checklist: ['能写下标版递归。'],
    main: { id: 654, title: '最大二叉树', slug: 'maximum-binary-tree' },
    codeSketch: `// TreeNode* build(vector<int>& nums, int l, int r) {
//   if (l >= r) return nullptr;
//   int mid = l, maxV = nums[l];
//   for (int i = l+1; i < r; ++i) if (nums[i] > maxV) { maxV = nums[i]; mid = i; }
//   auto root = new TreeNode(maxV);
//   root->left = build(nums, l, mid);
//   root->right = build(nums, mid+1, r);
//   return root;
// }`,
  }),
  base({
    id: 'checkpoint-3',
    title: '20. 二叉树周末总结（三）',
    subtitle: '回溯 · 左叶子 · 构造 · 返回值',
    difficulty: '入门',
    estMinutes: 25,
    keywords: ['周末总结', '构造'],
    points: [
      '周一：257 回溯在 path 传值；展开版优于死记精简版。',
      '周二：404 须父结点判左叶子，不能只看左子树形态。',
      '周三：513 层序简单；DFS 先左后右+最大深度。',
      '周四：递归何时要返回值——搜一条边用 bool；整棵树属性常 void；后序合并用 int/指针。',
      '周五：106 区间不变量；无中序则无法唯一构造；前序定根、中序分左右。',
      '周六：654 用下标切数组；空指针是否进递归决定 if 写法。',
    ],
    checklist: ['能总结「构造题」三步：找根、切左、切右。'],
  }),
  base({
    id: 'merge-trees',
    title: '21. 合并二叉树',
    subtitle: '617 · 同时遍历两棵树',
    difficulty: '基础',
    estMinutes: 30,
    keywords: ['617', '合并', '前序'],
    points: [
      '同步递归 t1、t2：皆空返回空；一空返回另一棵；皆非空新值=和，递归左右。',
      '与 101 对称树类似，都是同时操作两棵树；迭代可用队列成对入队。',
    ],
    pitfalls: ['只合并根未递归子树。'],
    checklist: ['能手写递归合并。'],
    main: { id: 617, title: '合并二叉树', slug: 'merge-two-binary-trees' },
    codeSketch: `// TreeNode* mergeTrees(TreeNode* t1, TreeNode* t2) {
//   if (!t1) return t2;
//   if (!t2) return t1;
//   t1->val += t2->val;
//   t1->left = mergeTrees(t1->left, t2->left);
//   t1->right = mergeTrees(t1->right, t2->right);
//   return t1;
// }`,
  }),
  base({
    id: 'bst-search',
    title: '22. 二叉搜索树中的搜索',
    subtitle: '700 · 有序性定向查找',
    difficulty: '入门',
    estMinutes: 25,
    keywords: ['700', 'BST', '搜索'],
    points: [
      'BST 有序：小于根走左，大于走右，相等返回；无需回溯。',
      '递归须接住返回值：`result = search(root->left)`，不能忽略返回的指针。',
      '迭代极简：while(root) { if (val<root->val) root=left; else if ... }',
    ],
    pitfalls: ['递归搜索不写 `return search(...)` 导致丢结果。'],
    checklist: ['能手写迭代 O(h)。'],
    main: { id: 700, title: '二叉搜索树中的搜索', slug: 'search-in-a-binary-search-tree' },
    codeSketch: `// TreeNode* searchBST(TreeNode* root, int val) {
//   while (root) {
//     if (val < root->val) root = root->left;
//     else if (val > root->val) root = root->right;
//     else return root;
//   }
//   return nullptr;
// }`,
  }),
  base({
    id: 'validate-bst',
    title: '23. 验证二叉搜索树',
    subtitle: '98 · 中序递增 / 上下界',
    difficulty: '基础',
    estMinutes: 40,
    keywords: ['98', 'BST', '中序'],
    points: [
      '陷阱1：不能只比较父子，须保证整棵左子树 < 根 < 整棵右子树（用 (min,max) 区间传递）。',
      '陷阱2：用 long 或 null 初始化 pre，避免 INT_MIN 边界。',
      '中序应严格递增；中序迭代/递归均可。',
    ],
    pitfalls: ['只比较 node 与左右孩子。', '全局 min 变量求最值而非相邻比较。'],
    checklist: ['能手写中序 pre 指针版。', '能手写 min/max 区间版。'],
    main: { id: 98, title: '验证二叉搜索树', slug: 'validate-binary-search-tree' },
    codeSketch: `// bool valid(TreeNode* node, long lo, long hi) {
//   if (!node) return true;
//   if (node->val <= lo || node->val >= hi) return false;
//   return valid(node->left, lo, node->val)
//       && valid(node->right, node->val, hi);
// }`,
  }),
  base({
    id: 'bst-min-diff',
    title: '24. 二叉搜索树的最小绝对差',
    subtitle: '530 · 中序相邻 · pre 指针',
    difficulty: '基础',
    estMinutes: 30,
    keywords: ['530', '中序', '双指针'],
    points: [
      'BST 中序 = 有序数组；最小差 = 相邻元素差（勿用全局 min/max 扫一遍）。',
      '中序维护 pre：`result = min(result, cur->val - pre)`，再 `pre = cur->val`。',
      '也可先中序进 vector 再扫，但双指针 O(1) 空间更优。',
    ],
    pitfalls: ['忘记 pre 初始化导致首比较错误。'],
    checklist: ['能手写中序 pre 版。'],
    main: { id: 530, title: '二叉搜索树的最小绝对差', slug: 'minimum-absolute-difference-in-bst' },
    codeSketch: `// void inorder(TreeNode* cur) {
//   if (!cur) return;
//   inorder(cur->left);
//   if (pre != nullptr) ans = min(ans, cur->val - pre->val);
//   pre = cur;
//   inorder(cur->right);
// }`,
  }),
  base({
    id: 'bst-modes',
    title: '25. 二叉搜索树中的众数',
    subtitle: '501 · 中序 · 适时清空结果集',
    difficulty: '基础',
    estMinutes: 30,
    keywords: ['501', '中序', '众数'],
    points: [
      '中序统计：相等则 count++；count>maxCount 时清空 ans 并更新 maxCount，再 push。',
      '一趟中序即可，无需哈希。',
      'pre 指针判相邻相等，同 530。',
    ],
    pitfalls: ['发现更大 count 时未清空旧答案。'],
    checklist: ['能手写中序一遍求众数。'],
    main: { id: 501, title: '二叉搜索树中的众数', slug: 'find-mode-in-binary-search-tree' },
  }),
  base({
    id: 'lowest-common-ancestor',
    title: '26. 二叉树的最近公共祖先',
    subtitle: '236 · 后序 · 必须遍历整树',
    difficulty: '进阶',
    estMinutes: 55,
    keywords: ['236', 'LCA', '后序'],
    points: [
      '后序自底向上：左、右递归；若根为 p/q 返回根；左右都非空则当前为 LCA；否则返回非空一侧。',
      '须遍历整棵树：用 left/right 接返回值做中逻辑，不能找到就立即 return 整棵（搜索一条边 vs 整棵树）。',
      'p 是 q 祖先时，返回 p/q 也覆盖「节点可以是自身祖先」。',
      '迭代法不适合模拟此回溯；理解递归返回如何向上传递。',
    ],
    pitfalls: [
      '以为找到 p/q 就可以停止遍历其他分支。',
      '不理解 left 空 right 非空时为何 return right（目标在右子树链上）。',
    ],
    checklist: ['能手画 236 示例的返回传递。', '能区分「搜一条边」与「搜整棵树」。'],
    main: { id: 236, title: '二叉树的最近公共祖先', slug: 'lowest-common-ancestor-of-a-binary-tree' },
    codeSketch: `// TreeNode* lowestCommonAncestor(TreeNode* root, TreeNode* p, TreeNode* q) {
//   if (!root || root == p || root == q) return root;
//   auto left = lowestCommonAncestor(root->left, p, q);
//   auto right = lowestCommonAncestor(root->right, p, q);
//   if (left && right) return root;
//   return left ? left : right;
// }`,
  }),
  base({
    id: 'checkpoint-4',
    title: '27. 二叉树周末总结（四）',
    subtitle: 'BST 专题入门 · 合并 · LCA',
    difficulty: '入门',
    estMinutes: 25,
    keywords: ['周末总结', 'BST', '堆'],
    points: [
      '周一：617 同时遍历两树；队列成对处理最直观。',
      '周二起：BST 题想成有序数组；700 迭代极简。',
      '周三：98 两陷阱——整棵左<根<整棵右；long 边界。',
      '周四：530 相邻差；pre 指针技巧要熟练。',
      '周五：501 一遍中序+适时清空结果集。',
      '周六：236 后序+整树遍历+返回值传递。',
      '辨析：平衡 BST = BST+平衡；完全二叉树≠BST；堆是完全二叉树+堆序，不是平衡 BST。',
    ],
    checklist: ['能说明堆与 map 底层结构差别。'],
  }),
  base({
    id: 'bst-lca',
    title: '28. 二叉搜索树的最近公共祖先',
    subtitle: '235 · 区间分叉 · O(h)',
    difficulty: '基础',
    estMinutes: 30,
    keywords: ['235', 'LCA', 'BST'],
    points: [
      '从上往下：若 p、q 都小于根，LCA 在左；都大于根，在右；否则当前根即为 LCA（落在 [p,q] 区间）。',
      '第一次落在区间内即为最近；比 236 简单，无需后序。',
      '递归可「搜一条边」立即 return；迭代 while 向下。',
    ],
    pitfalls: ['沿用 236 后序写复杂了。'],
    checklist: ['能手写迭代 235。', '能对比 236 与 235。'],
    main: { id: 235, title: '二叉搜索树的最近公共祖先', slug: 'lowest-common-ancestor-of-a-binary-search-tree' },
    codeSketch: `// TreeNode* lowestCommonAncestor(TreeNode* root, TreeNode* p, TreeNode* q) {
//   while (root) {
//     if (root->val > p->val && root->val > q->val) root = root->left;
//     else if (root->val < p->val && root->val < q->val) root = root->right;
//     else return root;
//   }
//   return nullptr;
// }`,
  }),
  base({
    id: 'bst-insert',
    title: '29. 二叉搜索树中的插入操作',
    subtitle: '701 · 递归返回值挂结点',
    difficulty: '基础',
    estMinutes: 30,
    keywords: ['701', '插入'],
    points: [
      '递归：小于走左，大于走右，空位 new 并 return；上层 `root->left = insert(...)` 接住新子树。',
      '迭代：记录 parent，到空位后挂到 parent 的左/右。',
    ],
    pitfalls: ['未 return 新结点导致断链。'],
    checklist: ['能手写递归插入。'],
    main: { id: 701, title: '二叉搜索树中的插入操作', slug: 'insert-into-a-binary-search-tree' },
    codeSketch: `// TreeNode* insertIntoBST(TreeNode* root, int val) {
//   if (!root) return new TreeNode(val);
//   if (val < root->val) root->left = insertIntoBST(root->left, val);
//   else root->right = insertIntoBST(root->right, val);
//   return root;
// }`,
  }),
  base({
    id: 'bst-delete',
    title: '30. 删除二叉搜索树中的节点',
    subtitle: '450 · 零/一/二子 · 前驱后继',
    difficulty: '进阶',
    estMinutes: 55,
    keywords: ['450', '删除', 'BST'],
    points: [
      '先递归定位结点；叶：直接删；单子：用子替换；双子：用左子树最大或右子树最小接位，再删替换结点。',
      '删除后 return 新根（可能变）。',
      '与 701/669 一样依赖递归返回值改父指针。',
    ],
    pitfalls: ['双子只换值未删重复结点。', '找前驱/后继位置错误。'],
    checklist: ['能白板讲三种情况。'],
    main: { id: 450, title: '删除二叉搜索树中的节点', slug: 'delete-node-in-a-bst' },
  }),
  base({
    id: 'bst-trim',
    title: '31. 修剪二叉搜索树',
    subtitle: '669 · 根<low 整棵换右子树',
    difficulty: '基础',
    estMinutes: 40,
    keywords: ['669', '修剪'],
    points: [
      '不能 `if (root<low||root>high) return null` 一刀切——可能误删合法子树（如根0左null右2，区间[1,3]）。',
      '根<low：return trim(root->right)；根>high：return trim(root->left)；否则递归左右并 return root。',
      '返回值把「接替子树」连到父上，完成删除越界结点。',
      '迭代：先移根到区间内，再扫左链删过小、右链删过大。',
    ],
    pitfalls: ['朴素一刀切错误。', '看不懂 return trim(right) 如何删掉根。'],
    checklist: ['能解释示例 [1,0,2] 区间[1,3] 为何不能删整棵。'],
    main: { id: 669, title: '修剪二叉搜索树', slug: 'trim-a-binary-search-tree' },
    codeSketch: `// if (root->val < low) return trimBST(root->right, low, high);
// if (root->val > high) return trimBST(root->left, low, high);
// root->left = trimBST(root->left, low, high);
// root->right = trimBST(root->right, low, high);
// return root;`,
  }),
  base({
    id: 'sorted-array-to-bst',
    title: '32. 将有序数组转换为二叉搜索树',
    subtitle: '108 · 中点分治 · 高度平衡',
    difficulty: '基础',
    estMinutes: 35,
    keywords: ['108', '分治', '平衡'],
    points: [
      '有序数组取中点为根，左半建左子树，右半建右子树，天然平衡 BST。',
      '左闭右闭 [left,right]；mid = left + (right-left)/2 防溢出。',
      '偶数长度取偏左中点，答案不唯一属正常。',
    ],
    pitfalls: ['mid 用 (l+r)/2 溢出。', '区间开闭混乱。'],
    checklist: ['能手写下标递归。'],
    main: { id: 108, title: '将有序数组转换为二叉搜索树', slug: 'convert-sorted-array-to-binary-search-tree' },
    codeSketch: `// TreeNode* build(vector<int>& nums, int l, int r) {
//   if (l > r) return nullptr;
//   int mid = l + (r - l) / 2;
//   auto root = new TreeNode(nums[mid]);
//   root->left = build(nums, l, mid - 1);
//   root->right = build(nums, mid + 1, r);
//   return root;
// }`,
  }),
  base({
    id: 'bst-to-greater-sum',
    title: '33. 把二叉搜索树转换为累加树',
    subtitle: '538 · 反序中序 · pre 累加',
    difficulty: '基础',
    estMinutes: 35,
    keywords: ['538', '累加树', '反序中序'],
    points: [
      '想象有序数组从后往前前缀和；树上 = 反序中序：右 → 根 → 左。',
      '维护 pre：visit 根时 `root->val += pre; pre = root->val`（或先累加再赋值）。',
      '与 530/501 同属中序+pre 技巧族。',
    ],
    pitfalls: ['写成正序中序。', 'pre 更新顺序反了。'],
    checklist: ['能手写反序中序。'],
    main: { id: 538, title: '把二叉搜索树转换为累加树', slug: 'convert-bst-to-greater-tree' },
    codeSketch: `// void dfs(TreeNode* node) {
//   if (!node) return;
//   dfs(node->right);
//   node->val += pre;
//   pre = node->val;
//   dfs(node->left);
// }`,
  }),
  base({
    id: 'summary',
    title: '34. 二叉树总结篇',
    subtitle: '遍历选型 · 题型地图 · 复盘清单',
    difficulty: '入门',
    estMinutes: 35,
    keywords: ['总结', '复习'],
    points: [
      '构造题（含数组建树、合并）：多用前序——先定根再分左右。',
      '普通二叉树属性（深/平衡/节点数）：多用后序，靠子树返回值。',
      'BST 属性（验证/众数/最值/累加）：多用中序，当有序数组思考。',
      '路径/回溯：前序维护路径；注意返回值 bool 还是 void。',
      'LCA：普通树后序整棵遍历；BST 利用大小关系向下 O(h)。',
      '迭代：DFS 用栈，BFS 用队列；统一迭代与专项模板二选一精通即可。',
      '建议按四篇周末总结 + 本篇地图，查漏补缺 30+ 题。',
    ],
    checklist: [
      '能根据题目类型选对遍历与返回值设计。',
      '能独立完成 98/106/236/450 中任意两题讲解。',
      '已刷完本模块力扣主刷题与相关练习。',
    ],
  }),
]

export const BINARY_TREE_SECTIONS = applyBinaryTreeEnrichment(BINARY_TREE_SECTIONS_RAW)

export const BINARY_TREE_COUNT = BINARY_TREE_SECTIONS.length

export const BINARY_TREE_EXTRA: GuideTableBlock[] = [
  {
    sectionId: 'theory',
    title: '二叉树种类速查',
    columns: [
      { prop: 'kind', label: '种类', width: 110 },
      { prop: 'feature', label: '特征', minWidth: 200 },
      { prop: 'note', label: '备注', minWidth: 140 },
    ],
    data: [
      { kind: '满二叉树', feature: '仅度 0 与 2，叶同层', note: '深度 k 共 2^k−1 结点' },
      { kind: '完全二叉树', feature: '除最底层外满，底层靠左连续', note: '堆 = 完全二叉树 + 父子序' },
      { kind: 'BST', feature: '左 < 根 < 右，子树亦 BST', note: '中序 = 升序' },
      { kind: '平衡 BST', feature: '左右高度差 ≤ 1', note: 'AVL；红黑树是其一' },
    ],
  },
  {
    sectionId: 'theory',
    title: '前 / 中 / 后序：只记「根」的位置',
    hint: '「中」= 根结点被访问（处理）的时刻，不是「中间那个结点」的模糊说法。',
    columns: [
      { prop: 'order', label: '遍历', width: 80 },
      { prop: 'sequence', label: '顺序', width: 100 },
      { prop: 'visit', label: '何时处理根', minWidth: 120 },
      { prop: 'use', label: '常见用途', minWidth: 160 },
    ],
    data: [
      { order: '前序', sequence: '中 → 左 → 右', visit: '最先', use: '复制树、构造、路径前缀' },
      { order: '中序', sequence: '左 → 中 → 右', visit: '中间', use: 'BST 得有序序列' },
      { order: '后序', sequence: '左 → 右 → 中', visit: '最后', use: '高度、删结点、LCA、属性汇总' },
      { order: '层序', sequence: '逐层从左到右', visit: '按层', use: 'BFS、最短层、右视图' },
    ],
  },
  {
    sectionId: 'theory',
    title: 'DFS / BFS 实现对照',
    columns: [
      { prop: 'way', label: '方式', width: 90 },
      { prop: 'struct', label: '数据结构', width: 100 },
      { prop: 'orders', label: '包含哪些序', minWidth: 140 },
      { prop: 'impl', label: '实现要点', minWidth: 180 },
    ],
    data: [
      { way: 'DFS', struct: '栈 / 递归', orders: '前、中、后序', impl: '递归 = 系统栈；迭代需手写栈' },
      { way: 'BFS', struct: '队列', orders: '层序', impl: 'for 循环固定一层 size' },
    ],
  },
  {
    sectionId: 'theory',
    title: 'C++ 常用容器底层（写算法分析必知）',
    columns: [
      { prop: 'container', label: '容器', width: 120 },
      { prop: 'underlying', label: '底层', width: 120 },
      { prop: 'complexity', label: '增删查', width: 100 },
      { prop: 'note', label: '说明', minWidth: 160 },
    ],
    data: [
      { container: 'map / set', underlying: '红黑树（平衡 BST）', complexity: 'O(log n)', note: '有序，按 key 排序' },
      { container: 'multimap / multiset', underlying: '红黑树', complexity: 'O(log n)', note: '允许重复 key' },
      { container: 'unordered_map / set', underlying: '哈希表', complexity: '均摊 O(1)', note: '无序，非二叉树' },
      { container: 'priority_queue', underlying: '堆（完全二叉树）', complexity: 'push/pop O(log n)', note: '父子大小关系' },
    ],
  },
  {
    sectionId: 'theory',
    title: '链式 vs 顺序存储',
    columns: [
      { prop: 'mode', label: '方式', width: 90 },
      { prop: 'layout', label: '内存', width: 100 },
      { prop: 'index', label: '下标关系', minWidth: 160 },
      { prop: 'scene', label: '典型场景', minWidth: 140 },
    ],
    data: [
      { mode: '链式', layout: '结点分散，指针连接', index: 'left / right 指针', scene: '力扣、面试手写' },
      { mode: '顺序', layout: '数组连续', index: '父 i，左 2i+1，右 2i+2', scene: '堆、完全二叉树' },
    ],
  },
  {
    sectionId: 'traversal-recursive',
    title: '递归三部曲（写每道递归题前先填）',
    columns: [
      { prop: 'step', label: '步骤', width: 100 },
      { prop: 'question', label: '自问', minWidth: 280 },
    ],
    data: [
      { step: '① 参数/返回', question: '需要哪些参数？返回值类型？' },
      { step: '② 终止', question: '空结点/叶结点/越界时返回什么？' },
      { step: '③ 单层', question: '本层先做什么，再递归哪边？' },
    ],
  },
  {
    sectionId: 'summary',
    title: '遍历与题型选型（总结）',
    hint: '具体问题可灵活调整；路径题有时也用前序带回溯。',
    columns: [
      { prop: 'type', label: '题型', width: 120 },
      { prop: 'order', label: '常用遍历', width: 100 },
      { prop: 'return', label: '返回值', width: 100 },
      { prop: 'example', label: '例题', minWidth: 140 },
    ],
    data: [
      { type: '构造/合并', order: '前序', return: 'TreeNode*', example: '106/617/108/654' },
      { type: '属性（普通树）', order: '后序', return: 'int/bool', example: '104/110/222' },
      { type: 'BST 属性', order: '中序', return: 'void/int', example: '98/530/501/538' },
      { type: '路径/回溯', order: '前序', return: 'void/bool', example: '257/112/113' },
      { type: '层序变形', order: 'BFS', return: 'void', example: '102/199/637' },
      { type: 'LCA 普通', order: '后序', return: 'TreeNode*', example: '236' },
      { type: 'LCA BST', order: '自上而下', return: 'TreeNode*', example: '235' },
    ],
  },
  {
    sectionId: 'bst-search',
    title: 'BST 专题速记',
    columns: [
      { prop: 'topic', label: '主题', width: 100 },
      { prop: 'tip', label: '技巧', minWidth: 260 },
    ],
    data: [
      { topic: '查找/插入', tip: '比根小左、比根大右；递归记得 return 新指针' },
      { topic: '验证', tip: '中序严格递增，或 (min,max) 区间' },
      { topic: '删除', tip: '双子：左最大/右最小接位' },
      { topic: '修剪', tip: '根越界则整棵换一侧子树 return' },
      { topic: '累加/差/众数', tip: '中序 + pre 指针' },
    ],
  },
  {
    sectionId: 'traversal-iterative',
    title: '迭代遍历写法对照',
    columns: [
      { prop: 'order', label: '序', width: 70 },
      { prop: 'stack', label: '栈操作要点', minWidth: 200 },
      { prop: 'visit', label: '何时 visit', minWidth: 140 },
    ],
    data: [
      { order: '前序', stack: '弹栈 visit；先压右再压左', visit: '弹到结点即访问' },
      { order: '中序', stack: '一路向左入栈；弹栈后转右', visit: '弹栈后、走右前' },
      { order: '后序', stack: '双栈或根右左+reverse', visit: '见具体模板' },
    ],
  },
  {
    sectionId: 'level-order',
    title: '层序变形题速查',
    columns: [
      { prop: 'id', label: '题号', width: 70 },
      { prop: 'change', label: '单层逻辑改动', minWidth: 260 },
    ],
    data: [
      { id: '102', change: '每层 push 一个 vector' },
      { id: '107', change: '结果最后 reverse' },
      { id: '199', change: '取每层最后一个出队' },
      { id: '637', change: '每层求和/计数求平均' },
      { id: '515', change: '每层取 max' },
    ],
  },
  {
    sectionId: 'path-sum',
    title: '递归返回值：搜一条边 vs 搜整棵树',
    columns: [
      { prop: 'goal', label: '目标', width: 120 },
      { prop: 'return', label: '返回值', width: 80 },
      { prop: 'pattern', label: '写法', minWidth: 220 },
    ],
    data: [
      { goal: '找一条满足条件的路径', return: 'bool', pattern: 'if (recur(left)) return; 找到即停' },
      { goal: '需要左右子树信息合并', return: 'int/指针', pattern: 'left=recur(); right=recur(); 中处理' },
      { goal: '收集所有路径', return: 'void', pattern: '到叶 push；回溯 pop' },
    ],
  },
  {
    sectionId: 'build-tree-in-post',
    title: '106 构造步骤（后序+中序）',
    columns: [
      { prop: 'step', label: '步', width: 50 },
      { prop: 'action', label: '操作', minWidth: 300 },
    ],
    data: [
      { step: '1', action: '区间空 → return null' },
      { step: '2', action: '后序尾 = 根 val；在中序找 mid' },
      { step: '3', action: '左子树：中序 [l,mid)，后序左段' },
      { step: '4', action: '右子树：中序 (mid,r)，后序右段' },
    ],
  },
  {
    sectionId: 'bst-delete',
    title: '450 删除三种情况',
    columns: [
      { prop: 'case', label: '情况', width: 100 },
      { prop: 'action', label: '处理', minWidth: 240 },
    ],
    data: [
      { case: '叶结点', action: 'return null' },
      { case: '单子', action: 'return 非空子' },
      { case: '双子', action: '左子最大或右子最小接位，再删替换点' },
    ],
  },
  {
    sectionId: 'lowest-common-ancestor',
    title: '236 vs 235',
    columns: [
      { prop: 'item', label: '对比项', width: 90 },
      { prop: 'tree236', label: '236 普通树', minWidth: 160 },
      { prop: 'bst235', label: '235 BST', minWidth: 160 },
    ],
    data: [
      { item: '遍历', tree236: '后序，必须整棵', bst235: '自上而下 O(h)' },
      { item: '判断', tree236: '左右都找到 p/q', bst235: 'p,q 与根分叉' },
      { item: 'early return', tree236: '不能搜到就停', bst235: '可搜一条边' },
    ],
  },
  {
    sectionId: 'validate-bst',
    title: '98 两种正确写法',
    columns: [
      { prop: 'way', label: '方法', width: 100 },
      { prop: 'idea', label: '思路', minWidth: 260 },
    ],
    data: [
      { way: '中序', idea: 'pre 指针，严格递增' },
      { way: '上下界', idea: 'valid(node, lo, hi) 开区间传递' },
    ],
  },
]
