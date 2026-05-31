/**
 * 轻量单测：PathReplanDiff 核心逻辑（Node + tsx，不依赖 Vitest）。
 */
import assert from 'node:assert/strict'
import type { LearningPathPlan, PathStepItem } from '@/api/orchestrator'
import { computePathReplanDiff } from './pathReplanDiff'

function makePlan(
  keys: string[],
  opts?: { remediationKey?: string; summary?: string },
): LearningPathPlan {
  const steps: PathStepItem[] = keys.map((module_key, i) => ({
    module_key,
    rank: i + 1,
    reason: module_key === opts?.remediationKey ? '降级：巩固先修' : '匹配学习目标',
    phase: 'foundation',
    is_remediation: module_key === opts?.remediationKey,
  }))
  return {
    agent_name: 'PlannerAgent',
    summary: opts?.summary ?? '路径已更新',
    rationale: '已用拓扑排序保证先修关系；优先薄弱模块。',
    ordered_keys: keys,
    steps,
    remediation_inserted: !!opts?.remediationKey,
  }
}

function runTests() {
  const baseKeys = ['array', 'linked-list', 'stack-queue', 'binary-tree', 'dp', 'graph']

  // 新增节点
  const addedPlan = makePlan([...baseKeys, 'backtracking'])
  const addedDiff = computePathReplanDiff(baseKeys, addedPlan, {
    context: { trigger: 'mastery', evidence: ['掌握度 38：动态规划薄弱'] },
  })
  const addedItem = addedDiff.items.find((i) => i.moduleKey === 'backtracking')
  assert.equal(addedItem?.status, 'added')
  assert.equal(addedItem?.beforeRank, null)
  assert.ok(addedItem?.afterRank)
  assert.equal(addedDiff.hasChanges, true)

  // 节点提前
  const movedUpBefore = ['array', 'linked-list', 'stack-queue', 'binary-tree', 'dp', 'graph']
  const movedUpAfter = makePlan(['array', 'dp', 'linked-list', 'stack-queue', 'binary-tree', 'graph'])
  const upDiff = computePathReplanDiff(movedUpBefore, movedUpAfter)
  const dpUp = upDiff.items.find((i) => i.moduleKey === 'dp')
  assert.equal(dpUp?.status, 'moved_up')
  assert.ok(dpUp && dpUp.beforeRank != null && dpUp.afterRank != null)
  assert.ok(dpUp.rankDelta < 0)

  // 节点延后
  const movedDownBefore = ['array', 'dp', 'linked-list', 'stack-queue', 'binary-tree', 'graph']
  const movedDownAfter = makePlan(['array', 'linked-list', 'stack-queue', 'binary-tree', 'dp', 'graph'])
  const downDiff = computePathReplanDiff(movedDownBefore, movedDownAfter)
  const dpDown = downDiff.items.find((i) => i.moduleKey === 'dp')
  assert.equal(dpDown?.status, 'moved_down')
  assert.ok(dpDown && dpDown.rankDelta > 0)

  // 完全不变
  const samePlan = makePlan(baseKeys)
  const sameDiff = computePathReplanDiff(baseKeys, samePlan)
  assert.equal(sameDiff.hasChanges, false)
  assert.ok(sameDiff.items.every((i) => i.status === 'unchanged'))
  assert.equal(sameDiff.explanation, '本次评估后路径无需调整。')

  // 巩固节点
  const remedPlan = makePlan(['array', 'linked-list', 'stack-queue', 'binary-tree', 'dp', 'graph'], {
    remediationKey: 'array',
    summary: '学情自适应：已插入「数组基础巩固」巩固关卡',
  })
  const remedDiff = computePathReplanDiff(baseKeys, remedPlan, {
    context: { trigger: 'oj_struggle' },
  })
  const remedItem = remedDiff.items.find((i) => i.moduleKey === 'array')
  assert.equal(remedItem?.status, 'remediation')
  assert.equal(remedDiff.remediationInserted, true)
  assert.ok(remedDiff.triggerLabel.includes('OJ') || remedDiff.trigger === 'oj_struggle')

  console.log('pathReplanDiff.test.ts: all passed')
}

runTests()
