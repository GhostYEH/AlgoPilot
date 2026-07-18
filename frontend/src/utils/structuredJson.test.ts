import assert from 'node:assert/strict'
import { parseStructuredJson } from './structuredJson'

const payload = {
  domain_narrative: { headline: '任务' },
  structure_logic: { code_framework: '# TODO' },
}

assert.deepEqual(parseStructuredJson(JSON.stringify(payload)), payload)
assert.deepEqual(parseStructuredJson(JSON.stringify(JSON.stringify(payload))), payload)
assert.deepEqual(
  parseStructuredJson(`json\\n${JSON.stringify(payload).replace(/"/g, '\\"')}`),
  payload,
)
assert.deepEqual(parseStructuredJson(`说明文字\n\`\`\`json\n${JSON.stringify(payload)}\n\`\`\``), payload)
assert.deepEqual(
  parseStructuredJson(
    `${JSON.stringify(payload, null, 2)}\n\n> ⚠️ 内容校验提示：结构化 JSON 格式无效\n\n---\n**依据知识库**：course:test`,
  ),
  payload,
)

console.log('structuredJson tests passed')
