/**
 * 二叉树各节加厚内容（overview + topicBlocks），合并进 binaryTreeCurriculum
 */
import type { LearnSection } from '@/modules/shared/learningTypes'
import { mergeEnrichment, type SectionEnrichment } from '@/modules/shared/sectionEnrichment'

export type { SectionEnrichment }

export const BINARY_TREE_ENRICHMENT: Record<string, SectionEnrichment> = {
  'traversal-recursive': {
    overview:
      '对应《二叉树的递归遍历》。很多人「一看就会，一写就废」，根因是没形成递归方法论。本节用「递归三部曲」固定前/中/后序写法，并对应力扣 144、94、145；建议先看 B 站公开课再手敲三遍模板。',
    estMinutes: 55,
    topicBlocks: [
      {
        title: '递归三部曲（每道题先填这三项再写代码）',
        points: [
          '① 确定递归函数的参数和返回值：要收集遍历结果则传 vector/int[]& 或返回 void；需要子树信息则返回 int/bool/TreeNode*。',
          '② 确定终止条件：当前结点为空则 return；空树是合法输入，别漏。',
          '③ 确定单层递归逻辑：本层先做什么，再递归左、再递归右（顺序随前/中/后序调整）。',
        ],
      },
      {
        title: '三种 DFS 顺序：只差「根」何时被访问',
        points: [
          '前序 144：中 → 左 → 右。先 push_back 根值，适合复制树、输出前缀表达式、构造题定根。',
          '中序 94：左 → 中 → 右。BST 上得到升序数组，验证/众数/最值都靠它。',
          '后序 145：左 → 右 → 中。先知道左右子树结果再处理根，求高度、删树、LCA 常用。',
          '同一棵树三种序列，把 visit 根的三行代码在左、右递归之间移动即可。',
        ],
      },
      {
        title: '拓展与练习',
        points: [
          '掌握二叉树后可做 N 叉树 589（前序）、590（后序），把 left/right 换成 children 循环。',
          'JavaScript 可用展开运算符写函数式前序，但面试仍建议掌握显式递归模板。',
        ],
      },
    ],
    summaryPoints: ['写递归：参数/终止/单层，三步缺一不可。'],
    extraPitfalls: ['递归函数有返回值却写成 `search(left)` 而不 `return search(left)`（搜索题常见）。'],
    extraChecklist: ['对同一棵 5 结点树，能口述三种遍历序列。'],
  },
  'traversal-iterative': {
    overview:
      '用栈模拟系统递归栈，实现 144/94/145 的非递归版本。核心记忆：递归 = 进栈保存现场，回溯 = 弹栈；前序最好写，中序要「一路向左再弹栈」，后序可用双栈或「根右左 + reverse」。',
    estMinutes: 55,
    topicBlocks: [
      {
        title: '为什么栈能写遍历',
        intro: '每次递归调用会把局部变量、返回地址压入系统栈；用显式 stack 可复现该过程。',
        points: [
          '前序：结点入栈后立刻 visit（弹栈即访问），再按「先右后左」压孩子，保证先走左子树。',
          '中序：不能弹栈就 visit；须 cur 一路向左入栈，弹栈 visit 后 cur=cur->right。',
          '后序：可先得到「根→右→左」序列再 reverse；或记录 lastVisited 避免重复进入右子树。',
        ],
      },
      {
        title: '前序两种写法（空结点是否入栈）',
        points: [
          '空结点入栈：弹栈时 if(node) visit else continue，再压右、压左（可含 null）。',
          '非空孩子入栈：仅 node->left/right 非空时压栈，逻辑更清晰，与动画一致。',
          '两者等价；面试写一种即可，但要能解释压栈顺序。',
        ],
      },
      {
        title: '递归 vs 迭代（周末总结常考）',
        points: [
          '时间复杂度均为 O(n)；递归多函数调用开销，极端深树可能栈溢出。',
          '工程里深递归要慎用；面试手写递归通常可接受，但可能被追问「能否写迭代」。',
        ],
      },
    ],
    extraChecklist: ['能手写中序迭代；能口述前序为何先压右再压左。'],
  },
  'unified-traversal': {
    overview:
      '用「空指针标记」把前/中/后序迭代统一成一套栈逻辑：弹到真实结点时按固定模式压回 null 与子树，只调整「中」在压栈顺序中的位置。不必日常全用，但有助于理解栈与 visit 的对应关系。',
    estMinutes: 45,
    topicBlocks: [
      {
        title: '统一法的核心',
        points: [
          '弹栈元素为 TreeNode*：若为真实结点，按「右-中-左」或变体压回栈（含 NULL 标记）；若为 NULL，则 visit 上一个刚处理过的结点。',
          '前序：中在最先被处理；中序：中在左子树标记之后；后序：中在左右子树标记之后。',
          '理解后，看到迭代模板不再死记三套代码。',
        ],
      },
      {
        title: '何时需要掌握',
        points: [
          '刷题：掌握前序 + 中序两套迭代往往够用；后序用双栈或递归亦可。',
          '面试：能流畅写递归后，准备一种迭代（中序最常考）。',
        ],
      },
    ],
    extraPitfalls: ['把 NULL 标记与真实结点弹栈顺序搞反，导致重复 visit 或漏 visit。'],
  },
  'level-order': {
    overview:
      '层序 = BFS：队列先进先出，一层一层扩展。模板固定，变形题（102/107/199/637/515/429）只改「单层逻辑」。建议 102 后一口气刷多道层序变形。',
    estMinutes: 50,
    topicBlocks: [
      {
        title: '标准模板（必背）',
        points: [
          'if (!root) return; queue.push(root);',
          'while (!q.empty()) { int sz = q.size(); 本层结果清空;',
          '  for (i=0; i<sz; i++) { 取队头 visit; 非空左入队; 非空右入队; }',
          '  把本层结果加入答案; }',
          '关键：sz = q.size() 固定当前层界，不能在 for 里用动态 size 混层。',
        ],
      },
      {
        title: '常见变形思路',
        points: [
          '102：二维数组收集每层。',
          '107：每层 push 到结果，最后 reverse(ans)。',
          '199：每层最后一个出队的值（右视图）。',
          '637：每层求平均；515：每层 max。',
          '429：N 叉树层序，孩子用 for 循环入队。',
        ],
      },
    ],
    extraPitfalls: ['未判空就 push 孩子导致队列混入 null。'],
  },
  'invert-tree': {
    overview:
      '226 翻转二叉树：交换每个结点的左右孩子指针。最简单是前序（或层序）——先 swap 再递归子树。注意：朴素递归「中序」会对同一结点 swap 两次，等于没翻。',
    estMinutes: 40,
    topicBlocks: [
      {
        title: '推荐写法',
        points: [
          '递归前序：if (!root) return; swap(left,right); invert(left); invert(right);',
          '层序：出队结点时 swap 其左右孩子，再把非空孩子入队。',
          '后序也可：先递归左右再 swap，逻辑仍正确。',
        ],
      },
      {
        title: '为何「递归中序」容易错',
        points: [
          '中序先左 → swap → 再左（此时左已是原右子树）→ 再 swap 一次，部分结点被翻两次。',
          '用栈模拟的中序统一迭代可以，因为处理时机不同；不要死记「中序=翻转」.',
        ],
      },
    ],
  },
  'checkpoint-1': {
    overview: '第一周复盘：遍历体系（递归/迭代/统一/层序）+ 翻转。结合本节周末总结，补漏答疑中的易混点。',
    topicBlocks: [
      {
        title: '周一～周三',
        points: [
          '周一：红黑树是平衡 BST；TreeNode 构造函数；Morris O(1) 空间了解即可。',
          '周二：递归三部曲；144/94/145 后做 589/590。',
          '周三：迭代前序空结点入栈两种写法；递归易懂、迭代省系统栈；工程防栈溢出。',
        ],
      },
      {
        title: '周四～周六',
        points: [
          '周四：统一迭代不强制日常用，面试可能追问迭代。',
          '周五：层序 = BFS；102 后刷 107/199/637/515。',
          '周六：翻转用前序；递归中序会双 swap；栈统一中序可翻。',
        ],
      },
    ],
  },
  'symmetric-tree': {
    overview:
      '101 对称二叉树：判断左子树与右子树是否镜像。不是比较根的左右指针，而是「两棵子树」外侧与内侧成对比较。掌握后可改序得到 100、572。',
    estMinutes: 45,
    topicBlocks: [
      {
        title: '递归：compare(L, R)',
        points: [
          '终止：都空 → true；一空 → false；值不等 → false。',
          '递归：compare(L.left, R.right) && compare(L.right, R.left)（外侧 + 内侧）。',
          '入口：isSymmetric(root) = compare(root->left, root->right)。',
        ],
      },
      {
        title: '迭代与其它题目',
        points: [
          '队列成对入队要比较的结点；不是普通层序。',
          '100 相同树：compare(L.left,R.left) && compare(L.right,R.right)。',
          '572 子树：在 root 上套 isSameTree(root, subRoot) 逻辑。',
        ],
      },
    ],
    extraPitfalls: ['只判断 root->left->val == root->right->val，未递归子树。'],
  },
  'max-depth': {
    overview:
      '104 求最大深度（力扣按结点计，根深度为 1）。后序求高度 +1 最常用；前序带 depth 回溯体现「向下走再回退」；层序数层数亦可。',
    estMinutes: 40,
    topicBlocks: [
      {
        title: '后序（推荐）',
        points: [
          'int depth(node): 空返回 0；return 1 + max(depth(left), depth(right))。',
          '根的高度 = 树的最大深度。',
        ],
      },
      {
        title: '前序回溯（理解深度）',
        points: [
          '进入结点 depth++，更新全局 max；到叶 return；回溯 depth--。',
          '体现「深度」是路径上结点计数，不是后序的「自底高度」直觉，但都对 104 有效。',
        ],
      },
      {
        title: '深度 vs 高度',
        points: [
          '深度：根到该结点；高度：结点到叶。力扣 104 要的是深度。',
          '110 平衡树用后序「高度」；不要混用术语。',
        ],
      },
    ],
  },
  'min-depth': {
    overview:
      '111 最小深度：根到最近叶子的结点个数。叶子 = 左右都空。与 104 差别在「必须到叶子」——单子树时不能取 min(左深,右深) 当 0+1。',
    estMinutes: 45,
    topicBlocks: [
      {
        title: '后序分情况',
        points: [
          '空树 0；仅根 1。',
          '左空右非空：1 + minDepth(right)，不能走左。',
          '右空左非空：1 + minDepth(left)。',
          '左右都有：1 + min(左深, 右深)。',
        ],
      },
      {
        title: '其它写法',
        points: [
          '层序：第一次遇到叶子时的层数即答案（常比递归直观）。',
          '前序带 depth 亦可，到叶更新 min。',
        ],
      },
    ],
    extraPitfalls: ['直接 return 1+min(左,右) 当一侧为空会得到 1，错。'],
  },
  'count-nodes': {
    overview:
      '222 完全二叉树结点个数：朴素 O(n) 遍历；利用完全性可 O(log²n)——比较左子树最左深度与右子树最左深度。',
    estMinutes: 50,
    topicBlocks: [
      {
        title: 'O(n) 基础',
        points: ['后序：return 1 + count(left) + count(right)。', '222 数据范围下通常先写会 O(n)。'],
      },
      {
        title: '完全树优化',
        points: [
          'getDepthMostLeft：沿左孩子走到底的深度。',
          '若 root 左子最左深 == 右子最左深：左子满，规模 2^h-1 + count(right)。',
          '否则递归左子，return count(left) + 1 + ...。',
        ],
      },
    ],
    extraChecklist: ['能口述「左满则公式，否则递归左」的分支。'],
  },
  'balanced-tree': {
    overview:
      '110 平衡二叉树：任意结点 |左高−右高|≤1。朴素每结点算高 O(n²)；后序一次遍历返回高度，不平衡返回 -1 哨兵。',
    estMinutes: 45,
    topicBlocks: [
      {
        title: '后序 + 哨兵',
        points: [
          'getHeight：空返回 0；左高 -1 则 return -1；右高 -1 则 return -1。',
          '|左高−右高|>1 则 return -1；否则 return 1+max(左,右)。',
          'isBalanced = getHeight(root) != -1。',
        ],
      },
      {
        title: '栈还是队列',
        points: [
          '模拟前中后序用栈；层序用队列。',
          '本题用迭代模拟回溯效率差，面试写后序递归即可。',
        ],
      },
    ],
  },
  'all-paths': {
    overview:
      '257 收集根到叶所有路径。前序 + 回溯；精简写法里回溯藏在 `dfs(left, path+"->")`——函数返回后 path 未变，即回溯。',
    estMinutes: 50,
    topicBlocks: [
      {
        title: '展开版（建议先写）',
        points: [
          'path.push_back(val)；到叶则 ans.push_back(join(path))；',
          '递归左；递归右；path.pop_back() 显式回溯。',
        ],
      },
      {
        title: '精简版与回溯',
        points: [
          'dfs(node, path+"->", ans)：传值产生新字符串，兄弟分支互不影响，等价回溯。',
          '若 tmp=path+"->"; dfs(left,tmp) 且 path 可变共享，则失去回溯。',
        ],
      },
    ],
    extraChecklist: ['能画图说明 path 在递归栈上的变化。'],
  },
  'checkpoint-2': {
    overview: '第二周复盘：属性题（对称、深度、平衡、路径）。强调深度/高度、257 回溯、100/572 迁移。',
    topicBlocks: [
      {
        title: '属性题要点',
        points: [
          '101/100：成对比较两棵子树；队列成对入队。',
          '104 后序 vs 111 叶子；110 -1 哨兵。',
          '257：先展开版再精简；path 传值的回溯本质。',
          '属性题先定「返回值表示什么」再写代码。',
        ],
      },
    ],
  },
  'sum-left-leaves': {
    overview:
      '404 左叶子之和：左叶子 = 父的左孩子，且该孩子为叶。不能在本结点判断「我是左叶子」，须由父结点看左孩子是否叶。',
    estMinutes: 45,
    topicBlocks: [
      {
        title: '判定与反例',
        points: [
          '条件：root->left && !root->left->left && !root->left->right。',
          '只有右链的树：无左叶子，和为 0（不是最左结点值）。',
          '仅有左孩子但该左孩子还有孩子：不是左叶子。',
        ],
      },
      {
        title: '遍历顺序',
        points: [
          '后序：左子树贡献 + 右子树贡献 + 当前层判断左叶子取值。',
          '迭代前序/层序：在弹出父结点时检查其左孩子。',
        ],
      },
    ],
  },
  'find-bottom-left': {
    overview:
      '513 找最深层最左侧结点值。层序记录每层第一个最省事；DFS 先左后右维护 maxDepth 与答案。',
    estMinutes: 40,
    topicBlocks: [
      {
        title: '层序',
        points: ['每层 for 循环第一个出队的即该层最左；循环结束后 last 即为答案。'],
      },
      {
        title: 'DFS',
        points: [
          '先递归左再右；到叶且 depth>maxDepth 时更新 ans。',
          '需要回溯 depth-- 时，写法与 104 前序类似。',
        ],
      },
    ],
  },
  'path-sum': {
    overview:
      '112 是否存在根到叶路径和 = target；113 收集所有满足路径。重点：何时递归返回 bool（搜一条边）vs void（搜整棵或收集多条）。',
    estMinutes: 55,
    topicBlocks: [
      {
        title: '112：bool 返回值',
        points: [
          'target -= node->val；到叶且 target==0 返回 true。',
          'return hasPath(left) || hasPath(right)；找到一侧即可向上传递。',
        ],
      },
      {
        title: '113：收集 + 回溯',
        points: [
          'path 记录当前；到叶且和满足 push 副本；回溯 pop。',
        ],
      },
      {
        title: '返回值设计（全章通用）',
        points: [
          '搜一条符合条件的路径：bool，找到可 early return 一侧。',
          '需要整棵树信息（LCA、平衡）：左右都递归，用返回值在中层合并。',
          '后序属性：int/TreeNode* 表示子树状态。',
        ],
      },
    ],
    extraChecklist: ['能对比 112 与 236 在「是否遍历整棵树」上的差别。'],
  },
  'build-tree-in-post': {
    overview:
      '106 中序+后序构造二叉树；105 前序+中序同套路。后序尾元素为根；中序定位根后分左右段。无中序则无法唯一确定树。',
    estMinutes: 65,
    topicBlocks: [
      {
        title: '四步流程',
        points: [
          '1. 若区间为空 return nullptr。',
          '2. 后序最后元素 = 根；中序找根下标 mid（哈希 O(1)）。',
          '3. 左子树：中序 [l,mid)，后序左段长度 = mid-l。',
          '4. 右子树：中序 (mid,r)，后序对应右段；递归构建。',
        ],
      },
      {
        title: '区间不变量',
        points: [
          '全程坚持左闭右开或左闭右闭一种；mid 分割时勿重复用根下标。',
          '前序+中序：前序首为根，其余同切法。',
        ],
      },
    ],
    extraPitfalls: ['后序/前序中根元素被切进左右两次。', '左子树规模算错导致数组越界。'],
  },
  'maximum-binary-tree': {
    overview:
      '654 最大二叉树：区间最大值作根，左半建左子树，右半建右子树。构造题思维 = 前序（先根后子树）。用下标在原数组切分，避免每次 vector 拷贝 TLE。',
    estMinutes: 55,
    topicBlocks: [
      {
        title: '基础版 vs 优化版',
        points: [
          '基础：找 max 下标，new 根，vector 拷贝左右递归——易 TLE。',
          '优化：build(nums, l, r) 左闭右开，l>=r 返回空；mid 为区间最大下标。',
        ],
      },
      {
        title: '空指针是否进递归',
        points: [
          '不让空进递归：if (l>=r) return null；左右 if 边界再递归。',
          '让空进递归：少写 if，终止 left>=right；风格二选一即可。',
        ],
      },
    ],
  },
  'checkpoint-3': {
    overview: '第三周：回溯、左叶子、路径和、构造树、返回值语义、654 分治。',
    topicBlocks: [
      {
        title: '复盘清单',
        points: [
          '257 path 传值 = 回溯；404 父判左叶；513 层序最左。',
          '112 bool vs 236 整树后序；106 区间切割；654 下标分治。',
          '构造题：找根 → 切左 → 切右，前序思维。',
        ],
      },
    ],
  },
  'merge-trees': {
    overview:
      '617 合并两棵二叉树：同步遍历 t1、t2，对应结点值相加，空树规则合并。与 101 一样属于「同时操作两棵树」。',
    estMinutes: 40,
    topicBlocks: [
      {
        title: '递归',
        points: [
          '皆空 return null；t1 空 return t2；t2 空 return t1。',
          't1->val += t2->val；t1->left = merge(left1,left2)；t1->right 同理；return t1。',
        ],
      },
      {
        title: '迭代',
        points: ['队列同时 push t1、t2 对应结点；出队时合并并 push 非空孩子成对。'],
      },
    ],
  },
  'bst-search': {
    overview:
      '700 在 BST 中搜索：利用有序性，小于根走左、大于走右，O(h)。迭代无需栈；递归必须 return 子树搜索结果。',
    estMinutes: 35,
    topicBlocks: [
      {
        title: '定向搜索',
        points: [
          '无需回溯，路径由比较唯一确定。',
          '递归：if (!root||root->val==val) return root; return val<root->val ? search(left):search(right);',
          '迭代：while(root) 比较后 root=left/right。',
        ],
      },
      {
        title: '常见错误',
        points: [
          '写 search(left) 不接 return，子树找到的结果丢失。',
          '普通二叉树那样左右都搜——浪费且错用 BST 性质。',
        ],
      },
    ],
  },
  'validate-bst': {
    overview:
      '98 验证 BST：不能只比较父子；须保证整棵左子树 < 根 < 整棵右子树。中序严格递增，或递归传 (min,max) 开区间。',
    estMinutes: 50,
    topicBlocks: [
      {
        title: '陷阱 1：只比相邻结点',
        points: [
          '反例：根 5，左子 1，左子的右孩子 6——父左子合法，但 6 在左子树却 > 根。',
          '解决：valid(node, lo, hi)，左 (lo, node->val)，右 (node->val, hi)。',
        ],
      },
      {
        title: '陷阱 2：边界',
        points: [
          '用 long 或 null 初始化 pre；INT_MIN 作初值可能错。',
          '中序：if (pre!=null && cur->val <= pre) false。',
        ],
      },
    ],
  },
  'bst-min-diff': {
    overview:
      '530 最小绝对差：BST 中序 = 有序数组，答案 = 相邻元素最小差。双指针 pre，勿用全局 min/max 扫两遍。',
    estMinutes: 40,
    topicBlocks: [
      {
        title: '中序一遍',
        points: [
          'inorder(left)；若 pre 非空 ans=min(ans, cur-pre)；pre=cur；inorder(right)。',
          '可先收集 vector 再扫，但 O(1) 空间更优。',
        ],
      },
      {
        title: '与有序数组题的联系',
        points: ['把树想成数组，双指针技巧完全复用。'],
      },
    ],
  },
  'bst-modes': {
    overview:
      '501 众数：中序一遍，count 与 maxCount；当 count>maxCount 时清空结果集再 push，实现「一趟求众数」。',
    estMinutes: 40,
    topicBlocks: [
      {
        title: '中序统计',
        points: [
          'cur->val == pre->val：count++；否则 count=1。',
          'count>maxCount：maxCount=count；清空 ans；push cur。',
          'count==maxCount：push cur。',
        ],
      },
      {
        title: '技巧',
        points: ['适时清空 ans 是「一遍求众数」的关键，与哈希两遍不同。'],
      },
    ],
  },
  'lowest-common-ancestor': {
    overview:
      '236 普通二叉树 LCA：后序自底向上，左右子树各找到 p/q 则当前为 LCA。必须遍历整棵树，用 left/right 接返回值在中层处理，不能搜到就停。',
    estMinutes: 65,
    topicBlocks: [
      {
        title: '后序逻辑',
        points: [
          'if (!root||root==p||root==q) return root;',
          'left=LCA(left)；right=LCA(right)；',
          'left&&right → return root；否则 return left?left:right。',
        ],
      },
      {
        title: '为何要遍历整棵',
        points: [
          '搜一条边：if(recur(left)) return; —— 找到就停。',
          '搜整棵：left=recur(left); right=recur(right); 再处理中——LCA 需要两侧信息。',
          'p 是 q 祖先时，返回 p 已覆盖「结点可为自身祖先」。',
        ],
      },
    ],
    extraChecklist: ['能手画示例中返回值如何从底传到根。'],
  },
  'checkpoint-4': {
    overview: '第四周：BST 专题、合并、LCA。辨析 map/堆/BST；98/530/501 中序族；235 vs 236。',
    topicBlocks: [
      {
        title: 'BST 周要点',
        points: [
          '700 定向；98 区间/中序；530/501/538 中序+pre。',
          '236 后序整树；235 区间向下 O(h)。',
          '617 双树同步；堆≠平衡 BST，map≠unordered_map。',
        ],
      },
    ],
  },
  'bst-lca': {
    overview:
      '235 BST 的 LCA：p、q 与根比较，同侧继续，分叉处即为答案。第一次落在 [p,q] 区间内最近。比 236 简单得多。',
    estMinutes: 40,
    topicBlocks: [
      {
        title: '自上而下',
        points: [
          'root->val > p && > q → 左子树；都小于 → 右子树；否则 return root。',
          '可递归「搜一条边」立即 return；迭代 while 向下。',
        ],
      },
      {
        title: '与 236 对比',
        points: ['236 无序树必须后序；235 用 BST 有序性 O(h)。'],
      },
    ],
  },
  'bst-insert': {
    overview:
      '701 插入：按 BST 性质走到空位 new 结点。递归用返回值挂到父：root->left = insert(left)。',
    estMinutes: 40,
    topicBlocks: [
      {
        title: '递归',
        points: [
          'if (!root) return new TreeNode(val);',
          'val<root->val → left=insert(left)；else right=insert(right)；return root;',
        ],
      },
      {
        title: '迭代',
        points: ['parent 指针；走到 null 后挂到 parent 的左或右。'],
      },
    ],
  },
  'bst-delete': {
    overview:
      '450 删除 BST 结点：叶直接删；单子用子替换；双子用左子树最大或右子树最小接位再删重复。全程依赖递归返回值改父指针。',
    estMinutes: 65,
    topicBlocks: [
      {
        title: '三种情况',
        points: [
          '找不到：return root。',
          '找到且叶：return null。',
          '单子：return 非空子。',
          '双子：找左子最右（或右子最左）换值，再递归删该结点。',
        ],
      },
      {
        title: '实现要点',
        points: [
          '删除后 return 的新根可能变化，上层要接住。',
          '与 701、669 同一套「递归返回值改树」思维。',
        ],
      },
    ],
  },
  'bst-trim': {
    overview:
      '669 修剪到 [low,high]：不能根越界就 return null 一刀切。根<low 整棵换 trim(right)；根>high 换 trim(left)；否则递归左右。',
    estMinutes: 50,
    topicBlocks: [
      {
        title: '错误 vs 正确',
        points: [
          '错：if (root<low||root>high) return null —— 可能删掉合法子树（如根0右2，区间[1,3]）。',
          '对：根<low return trim(right)；根>high return trim(left)；再 trim 左右子并 return root。',
        ],
      },
      {
        title: '理解 return trim(right)',
        points: [
          '根0小于1时，左子无效，右子2可能合法，故用右子树接替当前位置。',
          '返回值把新子树根连到父，完成「删除」越界结点。',
        ],
      },
    ],
  },
  'sorted-array-to-bst': {
    overview:
      '108 有序数组转高度平衡 BST：中点作根，左半建左子树，右半建右子树。与 106/654 同属分治构造，天然平衡。',
    estMinutes: 45,
    topicBlocks: [
      {
        title: '分治模板',
        points: [
          'build(l,r) 左闭右闭；l>r return null；',
          'mid = l + (r-l)/2 防溢出；root=nums[mid]；',
          'left=build(l,mid-1)；right=build(mid+1,r)。',
        ],
      },
      {
        title: '细节',
        points: ['偶数长度取左中或右中均可，答案不唯一。', '强调平衡：中点分保证左右规模差≤1。'],
      },
    ],
  },
  'bst-to-greater-sum': {
    overview:
      '538 累加树：每个结点新值 = 原值 + 所有更大结点之和。有序数组从后往前前缀和；树上 = 反序中序（右→中→左）+ pre 累加。',
    estMinutes: 45,
    topicBlocks: [
      {
        title: '反序中序',
        points: [
          'dfs(right)；node->val += pre；pre=node->val；dfs(left)。',
          '与 530/501 同属「中序族 + pre 指针」。',
        ],
      },
      {
        title: '迭代',
        points: ['栈：一路向右入栈，弹栈累加，再转左。'],
      },
    ],
  },
  summary: {
    overview:
      '二叉树篇总复盘：按题型选遍历与返回值。配合四篇周末总结与下方表格，查漏补缺 30+ 题。建议打印或收藏题型地图，刷题前 10 秒对号入座。',
    estMinutes: 45,
    topicBlocks: [
      {
        title: '选型口诀',
        points: [
          '构造/合并/数组建树 → 前序，先根再分左右（106/105/108/654/617）。',
          '普通树属性（深、平衡、节点数）→ 后序，子树结果汇总（104/110/222）。',
          'BST 属性 → 中序当有序数组（98/530/501/538）。',
          '路径/回溯 → 前序 + path，注意 bool 还是 void（257/112/113）。',
          'LCA：236 后序整棵；235 BST 向下 O(h)。',
          '层序变形 → BFS 模板改单层逻辑（102 系）。',
        ],
      },
      {
        title: '学习建议',
        points: [
          '每节先本节要点 + 本站分主题，再手敲主刷题。',
          '周末总结四篇按周复盘答疑。',
          '迭代至少精通中序；递归必须熟练三部曲。',
        ],
      },
    ],
  },
}

export function applyBinaryTreeEnrichment(sections: LearnSection[]): LearnSection[] {
  return mergeEnrichment(sections, BINARY_TREE_ENRICHMENT)
}
