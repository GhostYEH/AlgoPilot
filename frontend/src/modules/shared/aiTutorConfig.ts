import type { LearnSection } from './learningTypes'

/** 各模块 AI 助教元数据（与路由 moduleKey 一致） */
export interface AiTutorModuleMeta {
  moduleKey: string
  moduleTitle: string
  chapterTag: string
  /** 按 section.id 覆盖快捷提问（优先于通用规则） */
  sectionQuickQuestions?: Record<string, string[]>
}

export const AI_TUTOR_MODULE_META: Record<string, AiTutorModuleMeta> = {
  array: {
    moduleKey: 'array',
    moduleTitle: '数组学习模块',
    chapterTag: '数组篇',
    sectionQuickQuestions: {
      theory: [
        '数组和链表最核心的区别是什么？',
        '为什么数组按下标访问是 O(1)？',
        '扩容时为什么要「摊还」分析？',
      ],
    },
  },
  'hash-table': {
    moduleKey: 'hash-table',
    moduleTitle: '哈希表学习模块',
    chapterTag: '哈希表篇',
    sectionQuickQuestions: {
      theory: [
        '哈希表为什么平均是 O(1) 查找？',
        '什么时候用 map，什么时候用 set？',
        '两数之和为什么适合用哈希？',
      ],
      summary: [
        '454 和 15/18 的解题套路为什么不一样？',
        '能帮我对比一下哈希和双指针的选用吗？',
      ],
    },
  },
  string: {
    moduleKey: 'string',
    moduleTitle: '字符串学习模块',
    chapterTag: '字符串篇',
    sectionQuickQuestions: {
      theory: ['字符串和字符数组是一回事吗？', '做字符串题最先要检查哪些边界？'],
    },
  },
  'two-pointers': {
    moduleKey: 'two-pointers',
    moduleTitle: '双指针学习模块',
    chapterTag: '双指针篇',
    sectionQuickQuestions: {
      theory: [
        '对撞指针、快慢指针、滑动窗口怎么区分？',
        '什么情况下不该用排序+双指针？',
      ],
      summary: ['哈希和双指针在本章各适合什么题？'],
    },
  },
  'linked-list': {
    moduleKey: 'linked-list',
    moduleTitle: '链表学习模块',
    chapterTag: '链表篇',
    sectionQuickQuestions: {
      theory: [
        'dummy 虚拟头节点解决了什么问题？',
        '单链表、双链表、循环链表各适合什么场景？',
      ],
    },
  },
  'stack-queue': {
    moduleKey: 'stack-queue',
    moduleTitle: '栈与队列学习模块',
    chapterTag: '栈与队列篇',
    sectionQuickQuestions: {
      theory: ['栈和队列分别像生活中的什么例子？', '单调栈到底在维护什么性质？'],
    },
  },
  'binary-tree': {
    moduleKey: 'binary-tree',
    moduleTitle: '二叉树学习模块',
    chapterTag: '二叉树篇',
    sectionQuickQuestions: {
      theory: ['前序、中序、后序遍历各是什么顺序？', 'BST 和普通二叉树有什么区别？'],
    },
  },
  backtracking: {
    moduleKey: 'backtracking',
    moduleTitle: '回溯算法学习模块',
    chapterTag: '回溯算法篇',
    sectionQuickQuestions: {
      theory: ['回溯和暴力 DFS 有什么区别？', '「撤销选择」在代码里长什么样？'],
    },
  },
  greedy: {
    moduleKey: 'greedy',
    moduleTitle: '贪心算法学习模块',
    chapterTag: '贪心算法篇',
    sectionQuickQuestions: {
      theory: ['怎么判断一道题能不能用贪心？', '贪心和动态规划怎么选？'],
    },
  },
  dp: {
    moduleKey: 'dp',
    moduleTitle: '动态规划学习模块',
    chapterTag: '动态规划篇',
    sectionQuickQuestions: {
      theory: ['动态规划的三要素是什么？', '记忆化搜索和递推填表有什么区别？'],
    },
  },
  'monotonic-stack': {
    moduleKey: 'monotonic-stack',
    moduleTitle: '单调栈学习模块',
    chapterTag: '单调栈篇',
    sectionQuickQuestions: {
      theory: ['单调栈里元素是单调增还是减由什么决定？', '「下一个更大元素」为什么用栈？'],
    },
  },
}

export function getAiTutorMeta(moduleKey: string): AiTutorModuleMeta | undefined {
  return AI_TUTOR_MODULE_META[moduleKey]
}

/** 根据模块 + 当前小节生成快捷提问 */
export function suggestQuestionsForModule(moduleKey: string, section: LearnSection): string[] {
  const meta = getAiTutorMeta(moduleKey)
  const custom = meta?.sectionQuickQuestions?.[section.id]
  if (custom?.length) return custom.slice(0, 4)

  const kw = section.keywords?.[0]
  const base = [
    '用通俗的话总结一下本节在讲什么？',
    '本节最容易搞混的点有哪些？',
  ]
  if (kw) {
    base.unshift(`「${kw}」到底是什么？能举个简单例子吗？`)
  }
  if (section.codeSketch) {
    base.push('代码骨架里每一部分分别在干什么？')
  }
  if (section.main) {
    base.push(`做「${section.main.title}」这类题时，思路应该从哪里入手？`)
  }
  return base.slice(0, 4)
}
