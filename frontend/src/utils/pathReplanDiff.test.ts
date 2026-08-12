/**
 * 学习路径重排 Diff 计算契约测试。
 *
 * 运行：npm run test:path-replan-diff
 *
 * 覆盖：
 *  - 模块顺序变化（前移/后移/新增/移除）
 *  - 巩固节点（remediation）识别
 *  - hasChanges 判定
 *  - evidence 收集与去重
 *  - trigger 默认标签
 *  - 无变化时的 explanation
 */
import assert from 'node:assert/strict'

import { computePathReplanDiff } from './pathReplanDiff'
import type { LearningPathPlan, PathStepItem } from '@/api/orchestrator'

let passed = 0
function check(name: string, fn: () => void) {
  fn()
  passed++
  console.log(`  ✓ ${name}`)
}

function makePlan(
  orderedKeys: string[],
  steps: PathStepItem[] = [],
  extra: Partial<LearningPathPlan> = {},
): LearningPathPlan {
  return {
    ordered_keys: orderedKeys,
    steps,
    summary: extra.summary ?? '',
    rationale: extra.rationale ?? '',
    remediation_inserted: extra.remediation_inserted ?? false,
    ...extra,
  } as LearningPathPlan
}

function step(moduleKey: string, reason = '', isRemediation = false): PathStepItem {
  return { module_key: moduleKey, reason, is_remediation: isRemediation } as PathStepItem
}

console.log('pathReplanDiff 契约测试')

check('完全相同的路径无变化', () => {
  const before = ['array', 'linked-list', 'hash-table']
  const plan = makePlan(before)
  const diff = computePathReplanDiff(before, plan)
  assert.equal(diff.hasChanges, false)
  assert.equal(diff.items.length, 3)
  assert.equal(diff.items.every((i) => i.status === 'unchanged'), true)
  assert.equal(diff.explanation, '本次评估后路径无需调整。')
})

check('模块前移', () => {
  const before = ['array', 'linked-list', 'hash-table']
  const after = ['linked-list', 'array', 'hash-table']
  const diff = computePathReplanDiff(before, makePlan(after))
  assert.equal(diff.hasChanges, true)
  const linkedList = diff.items.find((i) => i.moduleKey === 'linked-list')!
  const array = diff.items.find((i) => i.moduleKey === 'array')!
  assert.equal(linkedList.status, 'moved_up')
  assert.equal(array.status, 'moved_down')
  assert.equal(linkedList.rankDelta, -1)
  assert.equal(array.rankDelta, 1)
})

check('新增模块', () => {
  const before = ['array', 'linked-list']
  const after = ['array', 'linked-list', 'hash-table']
  const diff = computePathReplanDiff(before, makePlan(after))
  const ht = diff.items.find((i) => i.moduleKey === 'hash-table')!
  assert.equal(ht.status, 'added')
  assert.equal(ht.beforeRank, null)
  assert.equal(ht.afterRank, 3)
})

check('移除模块', () => {
  const before = ['array', 'linked-list', 'hash-table']
  const after = ['array', 'linked-list']
  const diff = computePathReplanDiff(before, makePlan(after))
  const ht = diff.items.find((i) => i.moduleKey === 'hash-table')!
  assert.equal(ht.status, 'removed')
  assert.equal(ht.beforeRank, 3)
  assert.equal(ht.afterRank, null)
})

check('巩固节点识别', () => {
  const before = ['array', 'linked-list']
  const after = ['array', 'linked-list', 'two-pointers']
  const steps = [
    step('array'),
    step('linked-list'),
    step('two-pointers', '巩固双指针基础', true),
  ]
  const diff = computePathReplanDiff(before, makePlan(after, steps, { remediation_inserted: true }))
  const tp = diff.items.find((i) => i.moduleKey === 'two-pointers')!
  assert.equal(tp.status, 'remediation')
  assert.equal(diff.remediationInserted, true)
  assert.equal(diff.hasChanges, true)
})

check('trigger 默认标签', () => {
  const diff = computePathReplanDiff(['array'], makePlan(['array']), {
    context: { trigger: 'oj_struggle' },
  })
  assert.equal(diff.trigger, 'oj_struggle')
  assert.equal(diff.triggerLabel, 'OJ 连续受挫触发')
})

check('evidence 收集 rationale 与 summary 去重', () => {
  const plan = makePlan(['array'], [step('array', '基础模块')], {
    rationale: '根据画像调整',
    summary: '根据画像调整',
  })
  const diff = computePathReplanDiff(['linked-list'], plan)
  assert.ok(diff.evidence.includes('根据画像调整'))
  const count = diff.evidence.filter((e) => e === '根据画像调整').length
  assert.equal(count, 1, 'rationale 与 summary 相同时只保留一条')
})

check('extraEvidence 注入', () => {
  const diff = computePathReplanDiff(['array'], makePlan(['array']), {
    extraEvidence: ['最近 3 次 WA'],
  })
  assert.ok(diff.evidence.includes('最近 3 次 WA'))
})

check('items 排序按 afterRank', () => {
  const before = ['array', 'linked-list', 'hash-table']
  const after = ['hash-table', 'array', 'linked-list']
  const diff = computePathReplanDiff(before, makePlan(after))
  assert.equal(diff.items[0].moduleKey, 'hash-table')
  assert.equal(diff.items[1].moduleKey, 'array')
  assert.equal(diff.items[2].moduleKey, 'linked-list')
})

check('at 为 ISO 时间字符串', () => {
  const diff = computePathReplanDiff(['array'], makePlan(['array']))
  assert.ok(!Number.isNaN(Date.parse(diff.at)))
})

console.log(`\n全部通过：${passed} 项`)