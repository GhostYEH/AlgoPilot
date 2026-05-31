/**
 * 轻量单测：可在 Node 下用 `npx tsx` 运行，不依赖 Vitest。
 * npm run build 仍为主要验收。
 */
import assert from 'node:assert/strict'
import {
  getConsecutiveFailures,
  isFailVerdict,
  markOjStruggleTriggered,
  OJ_STRUGGLE_THRESHOLD,
  recordOjVerdictForStruggle,
  resetOjStruggleSession,
  shouldAutoTriggerOjStruggle,
} from './ojStruggleSession'

function runTests() {
  resetOjStruggleSession()
  const slug = 'test-problem'

  assert.equal(isFailVerdict('WA'), true)
  assert.equal(isFailVerdict('AC'), false)
  assert.equal(isFailVerdict('OK'), false)

  recordOjVerdictForStruggle(slug, 'WA')
  recordOjVerdictForStruggle(slug, 'RE')
  assert.equal(getConsecutiveFailures(slug), 2)
  assert.equal(shouldAutoTriggerOjStruggle(slug), false)

  recordOjVerdictForStruggle(slug, 'TLE')
  assert.equal(getConsecutiveFailures(slug), 3)
  assert.equal(shouldAutoTriggerOjStruggle(slug), true)

  markOjStruggleTriggered(slug)
  assert.equal(shouldAutoTriggerOjStruggle(slug), false)

  recordOjVerdictForStruggle(slug, 'WA')
  assert.equal(shouldAutoTriggerOjStruggle(slug), false)

  recordOjVerdictForStruggle(slug, 'AC')
  assert.equal(getConsecutiveFailures(slug), 0)
  assert.equal(shouldAutoTriggerOjStruggle(slug), false)

  recordOjVerdictForStruggle(slug, 'CE')
  recordOjVerdictForStruggle(slug, 'CE')
  recordOjVerdictForStruggle(slug, 'CE')
  assert.equal(getConsecutiveFailures(slug), 3)
  assert.equal(OJ_STRUGGLE_THRESHOLD, 3)

  resetOjStruggleSession(slug)
  assert.equal(getConsecutiveFailures(slug), 0)

  console.log('ojStruggleSession.test.ts: all passed')
}

runTests()
