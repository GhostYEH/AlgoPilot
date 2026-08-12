/**
 * 结构化 JSON 解析契约测试。
 *
 * 运行：npm run test:structured-json
 *
 * 覆盖：
 *  - 纯 JSON 对象/数组
 *  - 代码围栏 ```json ... ```
 *  - json 前缀文字
 *  - 模型夹带说明文字（JSON 前后）
 *  - 二次 JSON 编码（字符串里再编码一次）
 *  - 非法输入返回 null
 */
import assert from 'node:assert/strict'

import { parseStructuredJson } from './structuredJson'

let passed = 0
function check(name: string, fn: () => void) {
  fn()
  passed++
  console.log(`  ✓ ${name}`)
}

console.log('structuredJson 契约测试')

check('纯 JSON 对象', () => {
  const r = parseStructuredJson('{"a":1,"b":"x"}')
  assert.deepEqual(r, { a: 1, b: 'x' })
})

check('纯 JSON 数组', () => {
  const r = parseStructuredJson('[1,2,3]')
  assert.deepEqual(r, [1, 2, 3])
})

check('代码围栏 ```json', () => {
  const r = parseStructuredJson('```json\n{"k":true}\n```')
  assert.deepEqual(r, { k: true })
})

check('代码围栏 ``` 无语言标记', () => {
  const r = parseStructuredJson('```\n{"k":42}\n```')
  assert.deepEqual(r, { k: 42 })
})

check('json 前缀文字', () => {
  const r = parseStructuredJson('json {"k":"v"}')
  assert.deepEqual(r, { k: 'v' })
})

check('夹带前导说明文字', () => {
  const r = parseStructuredJson('好的，这是结果：\n{"domain_narrative":"二分查找","code":"bs"}')
  assert.deepEqual(r, { domain_narrative: '二分查找', code: 'bs' })
})

check('夹带尾部说明文字', () => {
  const r = parseStructuredJson('{"a":1}\n以上是分析。')
  assert.deepEqual(r, { a: 1 })
})

check('二次 JSON 编码（字符串内再编码）', () => {
  const inner = JSON.stringify({ domain_narrative: 'dp', code: 'climb' })
  const encoded = JSON.stringify(inner)
  const r = parseStructuredJson(encoded)
  assert.deepEqual(r, { domain_narrative: 'dp', code: 'climb' })
})

check('嵌套对象与数组', () => {
  const r = parseStructuredJson('{"steps":[{"i":1},{"i":2}],"ok":true}')
  assert.deepEqual(r, { steps: [{ i: 1 }, { i: 2 }], ok: true })
})

check('空字符串返回 null', () => {
  assert.equal(parseStructuredJson(''), null)
})

check('纯文字无 JSON 返回 null', () => {
  assert.equal(parseStructuredJson('这不是 JSON'), null)
})

check('null 输入返回 null', () => {
  assert.equal(parseStructuredJson(null as unknown as string), null)
})

check('残缺 JSON 返回 null', () => {
  assert.equal(parseStructuredJson('{"a":1,"b":'), null)
})

console.log(`\n全部通过：${passed} 项`)