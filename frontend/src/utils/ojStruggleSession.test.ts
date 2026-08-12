/**
 * OJ 连续受挫会话计数器契约测试。
 *
 * 运行：npm run test:oj-struggle
 *
 * 覆盖：
 *  - 失败判题（WA/RE/TLE/CE）累加连续失败计数
 *  - AC 清零当前题目计数并重置触发标记
 *  - 达阈值（默认 3）后 shouldAutoTriggerOjStruggle 返回 true
 *  - 本轮已触发后不再重复触发，直到 AC 或换题重置
 *  - 空 slug 与 undefined verdict 的边界行为
 */
import assert from 'node:assert/strict'

import {
  OJ_STRUGGLE_THRESHOLD,
  isFailVerdict,
  recordOjVerdictForStruggle,
  getConsecutiveFailures,
  shouldAutoTriggerOjStruggle,
  markOjStruggleTriggered,
  resetOjStruggleSession,
} from './ojStruggleSession'

let passed = 0
function check(name: string, fn: () => void) {
  fn()
  passed++
  console.log(`  ✓ ${name}`)
}

console.log('ojStruggleSession 契约测试')

check('阈值常量为 3', () => {
  assert.equal(OJ_STRUGGLE_THRESHOLD, 3)
})

check('isFailVerdict 识别 WA/RE/TLE/CE 为失败', () => {
  assert.equal(isFailVerdict('WA'), true)
  assert.equal(isFailVerdict('RE'), true)
  assert.equal(isFailVerdict('TLE'), true)
  assert.equal(isFailVerdict('CE'), true)
})

check('isFailVerdict 不把 AC/PENDING/undefined 视为失败', () => {
  assert.equal(isFailVerdict('AC'), false)
  assert.equal(isFailVerdict('PENDING' as never), false)
  assert.equal(isFailVerdict(undefined), false)
})

check('连续失败累加计数', () => {
  resetOjStruggleSession('binary-search-bound')
  assert.equal(recordOjVerdictForStruggle('binary-search-bound', 'WA'), 1)
  assert.equal(recordOjVerdictForStruggle('binary-search-bound', 'RE'), 2)
  assert.equal(recordOjVerdictForStruggle('binary-search-bound', 'TLE'), 3)
  assert.equal(getConsecutiveFailures('binary-search-bound'), 3)
})

check('AC 清零计数并重置触发标记', () => {
  resetOjStruggleSession('two-sum')
  recordOjVerdictForStruggle('two-sum', 'WA')
  recordOjVerdictForStruggle('two-sum', 'WA')
  markOjStruggleTriggered('two-sum')
  assert.equal(shouldAutoTriggerOjStruggle('two-sum'), false)
  assert.equal(recordOjVerdictForStruggle('two-sum', 'AC'), 0)
  assert.equal(shouldAutoTriggerOjStruggle('two-sum'), false)
})

check('达阈值后应自动触发，本轮标记后不再重复触发', () => {
  resetOjStruggleSession('reverse-linked-list')
  recordOjVerdictForStruggle('reverse-linked-list', 'WA')
  assert.equal(shouldAutoTriggerOjStruggle('reverse-linked-list'), false)
  recordOjVerdictForStruggle('reverse-linked-list', 'WA')
  assert.equal(shouldAutoTriggerOjStruggle('reverse-linked-list'), false)
  recordOjVerdictForStruggle('reverse-linked-list', 'WA')
  assert.equal(shouldAutoTriggerOjStruggle('reverse-linked-list'), true)
  markOjStruggleTriggered('reverse-linked-list')
  recordOjVerdictForStruggle('reverse-linked-list', 'WA')
  assert.equal(shouldAutoTriggerOjStruggle('reverse-linked-list'), false)
})

check('不同题目计数相互独立', () => {
  resetOjStruggleSession()
  recordOjVerdictForStruggle('a', 'WA')
  recordOjVerdictForStruggle('a', 'WA')
  recordOjVerdictForStruggle('b', 'WA')
  assert.equal(getConsecutiveFailures('a'), 2)
  assert.equal(getConsecutiveFailures('b'), 1)
})

check('空 slug 与 undefined verdict 不影响计数', () => {
  assert.equal(recordOjVerdictForStruggle('', 'WA'), 0)
  assert.equal(recordOjVerdictForStruggle('empty-verdict', undefined), 0)
})

check('resetOjStruggleSession 无参清空全部', () => {
  recordOjVerdictForStruggle('x', 'WA')
  recordOjVerdictForStruggle('y', 'WA')
  resetOjStruggleSession()
  assert.equal(getConsecutiveFailures('x'), 0)
  assert.equal(getConsecutiveFailures('y'), 0)
})

console.log(`\n全部通过：${passed} 项`)