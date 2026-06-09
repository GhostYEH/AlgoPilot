import type { Component } from 'vue'
import type { LearnSection } from './learningTypes'
import {
  STACK_QUEUE_SECTIONS,
  STACK_QUEUE_INTRO,
  STACK_QUEUE_COUNT,
  STACK_QUEUE_EXTRA,
} from '@/modules/stackQueue/stackQueueCurriculum'
import {
  BINARY_TREE_SECTIONS,
  BINARY_TREE_INTRO,
  BINARY_TREE_COUNT,
  BINARY_TREE_EXTRA,
} from '@/modules/binaryTree/binaryTreeCurriculum'
import {
  BACKTRACKING_SECTIONS,
  BACKTRACKING_INTRO,
  BACKTRACKING_COUNT,
  BACKTRACKING_EXTRA,
} from '@/modules/backtracking/backtrackingCurriculum'
import {
  GREEDY_SECTIONS,
  GREEDY_INTRO,
  GREEDY_COUNT,
  GREEDY_EXTRA,
} from '@/modules/greedy/greedyCurriculum'
import { DP_SECTIONS, DP_INTRO, DP_COUNT, DP_EXTRA } from '@/modules/dp/dpCurriculum'
import {
  MONOTONIC_STACK_SECTIONS,
  MONOTONIC_STACK_INTRO,
  MONOTONIC_STACK_COUNT,
  MONOTONIC_STACK_EXTRA,
} from '@/modules/monotonicStack/monotonicStackCurriculum'
import { STACK_QUEUE_SECTION_STORAGE_KEY, stackQueueProgress } from '@/modules/stackQueue/stackQueueProgress'
import { BINARY_TREE_SECTION_STORAGE_KEY, binaryTreeProgress } from '@/modules/binaryTree/binaryTreeProgress'
import {
  BACKTRACKING_SECTION_STORAGE_KEY,
  backtrackingProgress,
} from '@/modules/backtracking/backtrackingProgress'
import { GREEDY_SECTION_STORAGE_KEY, greedyProgress } from '@/modules/greedy/greedyProgress'
import { DP_SECTION_STORAGE_KEY, dpProgress } from '@/modules/dp/dpProgress'
import {
  MONOTONIC_STACK_SECTION_STORAGE_KEY,
  monotonicStackProgress,
} from '@/modules/monotonicStack/monotonicStackProgress'
import {
  GRAPH_SECTIONS,
  GRAPH_INTRO,
  GRAPH_COUNT,
  GRAPH_EXTRA,
} from '@/modules/graph/graphCurriculum'
import { GRAPH_SECTION_STORAGE_KEY, graphProgress } from '@/modules/graph/graphProgress'
import {
  SORTING_SECTIONS,
  SORTING_INTRO,
  SORTING_COUNT,
  SORTING_EXTRA,
} from '@/modules/sorting/sortingCurriculum'
import { SORTING_SECTION_STORAGE_KEY, sortingProgress } from '@/modules/sorting/sortingProgress'
import {
  LINKED_LIST_SECTIONS,
  LINKED_LIST_CURRICULUM_INTRO,
  LINKED_LIST_SECTION_COUNT,
} from '@/modules/linkedList/linkedListCurriculum'
import {
  LINKED_LIST_SECTION_STORAGE_KEY,
  linkedListProgress,
} from '@/modules/linkedList/linkedListProgress'

export interface GuideTableColumn {
  prop: string
  label: string
  width?: number
  minWidth?: number
}

export interface GuideTableBlock {
  sectionId: string
  title: string
  hint?: string
  columns: GuideTableColumn[]
  data: Record<string, string>[]
}

export interface ModuleLearnConfig {
  key: string
  routeName: string
  breadcrumb: string
  heroTitle: string
  chapterTag: string
  intro: string
  sections: LearnSection[]
  sectionCount: number
  storageKey: string
  loadSectionDone: () => Record<string, boolean>
  toggleSectionDone: (id: string, done: boolean, prev: Record<string, boolean>) => Record<string, boolean>
  animationComponent: () => Promise<Component>
  animTransitionClass: string
  extraTables?: GuideTableBlock[]
}

export const MODULE_LEARN_CONFIGS: Record<string, ModuleLearnConfig> = {
  'linked-list': {
    key: 'linked-list',
    routeName: 'learn-linked-list',
    breadcrumb: '链表学习',
    heroTitle: '链表学习模块',
    chapterTag: '链表篇',
    intro: LINKED_LIST_CURRICULUM_INTRO,
    sections: LINKED_LIST_SECTIONS,
    sectionCount: LINKED_LIST_SECTION_COUNT,
    storageKey: LINKED_LIST_SECTION_STORAGE_KEY,
    loadSectionDone: linkedListProgress.loadSectionDone,
    toggleSectionDone: linkedListProgress.toggleSectionDone,
    animationComponent: () =>
      import('@/modules/linkedList/components/LinkedListSectionAnimation.vue'),
    animTransitionClass: 'll-anim-fade',
  },
  'stack-queue': {
    key: 'stack-queue',
    routeName: 'learn-stack-queue',
    breadcrumb: '栈与队列学习',
    heroTitle: '栈与队列学习模块',
    chapterTag: '栈与队列篇',
    intro: STACK_QUEUE_INTRO,
    sections: STACK_QUEUE_SECTIONS,
    sectionCount: STACK_QUEUE_COUNT,
    storageKey: STACK_QUEUE_SECTION_STORAGE_KEY,
    loadSectionDone: stackQueueProgress.loadSectionDone,
    toggleSectionDone: stackQueueProgress.toggleSectionDone,
    animationComponent: () =>
      import('@/modules/stackQueue/components/StackQueueSectionAnimation.vue'),
    animTransitionClass: 'sq-anim-fade',
    extraTables: STACK_QUEUE_EXTRA,
  },
  'binary-tree': {
    key: 'binary-tree',
    routeName: 'learn-binary-tree',
    breadcrumb: '二叉树学习',
    heroTitle: '二叉树学习模块',
    chapterTag: '二叉树篇',
    intro: BINARY_TREE_INTRO,
    sections: BINARY_TREE_SECTIONS,
    sectionCount: BINARY_TREE_COUNT,
    storageKey: BINARY_TREE_SECTION_STORAGE_KEY,
    loadSectionDone: binaryTreeProgress.loadSectionDone,
    toggleSectionDone: binaryTreeProgress.toggleSectionDone,
    animationComponent: () =>
      import('@/modules/binaryTree/components/BinaryTreeSectionAnimation.vue'),
    animTransitionClass: 'bt-anim-fade',
    extraTables: BINARY_TREE_EXTRA,
  },
  backtracking: {
    key: 'backtracking',
    routeName: 'learn-backtracking',
    breadcrumb: '回溯算法学习',
    heroTitle: '回溯算法学习模块',
    chapterTag: '回溯算法篇',
    intro: BACKTRACKING_INTRO,
    sections: BACKTRACKING_SECTIONS,
    sectionCount: BACKTRACKING_COUNT,
    storageKey: BACKTRACKING_SECTION_STORAGE_KEY,
    loadSectionDone: backtrackingProgress.loadSectionDone,
    toggleSectionDone: backtrackingProgress.toggleSectionDone,
    animationComponent: () =>
      import('@/modules/backtracking/components/BacktrackingSectionAnimation.vue'),
    animTransitionClass: 'bk-anim-fade',
    extraTables: BACKTRACKING_EXTRA,
  },
  greedy: {
    key: 'greedy',
    routeName: 'learn-greedy',
    breadcrumb: '贪心算法学习',
    heroTitle: '贪心算法学习模块',
    chapterTag: '贪心算法篇',
    intro: GREEDY_INTRO,
    sections: GREEDY_SECTIONS,
    sectionCount: GREEDY_COUNT,
    storageKey: GREEDY_SECTION_STORAGE_KEY,
    loadSectionDone: greedyProgress.loadSectionDone,
    toggleSectionDone: greedyProgress.toggleSectionDone,
    animationComponent: () => import('@/modules/greedy/components/GreedySectionAnimation.vue'),
    animTransitionClass: 'gr-anim-fade',
    extraTables: GREEDY_EXTRA,
  },
  dp: {
    key: 'dp',
    routeName: 'learn-dp',
    breadcrumb: '动态规划学习',
    heroTitle: '动态规划学习模块',
    chapterTag: '动态规划篇',
    intro: DP_INTRO,
    sections: DP_SECTIONS,
    sectionCount: DP_COUNT,
    storageKey: DP_SECTION_STORAGE_KEY,
    loadSectionDone: dpProgress.loadSectionDone,
    toggleSectionDone: dpProgress.toggleSectionDone,
    animationComponent: () => import('@/modules/dp/components/DpSectionAnimation.vue'),
    animTransitionClass: 'dp-anim-fade',
    extraTables: DP_EXTRA,
  },
  'monotonic-stack': {
    key: 'monotonic-stack',
    routeName: 'learn-monotonic-stack',
    breadcrumb: '单调栈学习',
    heroTitle: '单调栈学习模块',
    chapterTag: '单调栈篇',
    intro: MONOTONIC_STACK_INTRO,
    sections: MONOTONIC_STACK_SECTIONS,
    sectionCount: MONOTONIC_STACK_COUNT,
    storageKey: MONOTONIC_STACK_SECTION_STORAGE_KEY,
    loadSectionDone: monotonicStackProgress.loadSectionDone,
    toggleSectionDone: monotonicStackProgress.toggleSectionDone,
    animationComponent: () =>
      import('@/modules/monotonicStack/components/MonotonicStackSectionAnimation.vue'),
    animTransitionClass: 'ms-anim-fade',
    extraTables: MONOTONIC_STACK_EXTRA,
  },
  graph: {
    key: 'graph',
    routeName: 'learn-graph',
    breadcrumb: '图论学习',
    heroTitle: '图论学习模块',
    chapterTag: '图论篇 · ch06-graph',
    intro: GRAPH_INTRO,
    sections: GRAPH_SECTIONS,
    sectionCount: GRAPH_COUNT,
    storageKey: GRAPH_SECTION_STORAGE_KEY,
    loadSectionDone: graphProgress.loadSectionDone,
    toggleSectionDone: graphProgress.toggleSectionDone,
    animationComponent: () => import('@/modules/graph/components/GraphSectionAnimation.vue'),
    animTransitionClass: 'graph-anim-fade',
    extraTables: GRAPH_EXTRA,
  },
  sorting: {
    key: 'sorting',
    routeName: 'learn-sorting',
    breadcrumb: '排序算法学习',
    heroTitle: '排序算法专题',
    chapterTag: '排序篇 · ch08-sorting',
    intro: SORTING_INTRO,
    sections: SORTING_SECTIONS,
    sectionCount: SORTING_COUNT,
    storageKey: SORTING_SECTION_STORAGE_KEY,
    loadSectionDone: sortingProgress.loadSectionDone,
    toggleSectionDone: sortingProgress.toggleSectionDone,
    animationComponent: () =>
      import('@/modules/sorting/components/SortingSectionAnimation.vue'),
    animTransitionClass: 'sorting-anim-fade',
    extraTables: SORTING_EXTRA,
  },
}

export function getModuleLearnConfig(key: string): ModuleLearnConfig | undefined {
  return MODULE_LEARN_CONFIGS[key]
}
