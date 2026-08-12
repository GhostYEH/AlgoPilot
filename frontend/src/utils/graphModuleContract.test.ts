/**
 * 概念知识图谱与算法模块目录的一致性契约测试。
 *
 * 运行：npm run test:graph-module
 *
 * 覆盖：
 *  - validateConceptGraph() 无结构问题
 *  - 每个 concept 的 module_key 在 ALGORITHM_MODULES 中存在
 *  - 每个 problem 的 module_key 在 ALGORITHM_MODULES 中存在
 *  - 每个 problem 的 concept_ids 指向真实存在的 concept
 *  - 每个 concept 的 prerequisites 指向真实存在的 concept
 *  - ALGORITHM_MODULES 中 available=true 的模块至少有一个 concept
 *  - 拓扑排序覆盖所有 concept 节点
 */
import assert from 'node:assert/strict'

import { ALGORITHM_MODULES } from '@/constants/modules'
import {
  getConceptCatalog,
  getProblemCatalog,
  getConceptsForModule,
  validateConceptGraph,
  buildConceptGraphNodes,
  buildConceptGraphEdges,
  topoSortConceptIds,
} from '@/constants/conceptGraph'

let passed = 0
function check(name: string, fn: () => void) {
  fn()
  passed++
  console.log(`  ✓ ${name}`)
}

console.log('graphModule 概念图谱契约测试')

const moduleKeys = new Set(ALGORITHM_MODULES.map((m) => m.key))
const concepts = getConceptCatalog()
const problems = getProblemCatalog()
const conceptIds = new Set(concepts.map((c) => c.id))

check('validateConceptGraph 无结构问题', () => {
  const issues = validateConceptGraph()
  assert.deepEqual(issues, [], `期望无问题，实际：${JSON.stringify(issues)}`)
})

check('每个 concept 的 module_key 在 ALGORITHM_MODULES 中存在', () => {
  for (const c of concepts) {
    assert.ok(moduleKeys.has(c.module_key), `concept ${c.id} 的 module_key="${c.module_key}" 不在模块目录中`)
  }
})

check('每个 problem 的 module_key 在 ALGORITHM_MODULES 中存在', () => {
  for (const p of problems) {
    assert.ok(moduleKeys.has(p.module_key), `problem ${p.id} 的 module_key="${p.module_key}" 不在模块目录中`)
  }
})

check('每个 problem 的 concept_ids 指向真实存在的 concept', () => {
  for (const p of problems) {
    for (const cid of p.concept_ids) {
      assert.ok(conceptIds.has(cid), `problem ${p.id} 引用了不存在的 concept "${cid}"`)
    }
  }
})

check('每个 concept 的 prerequisites 指向真实存在的 concept', () => {
  for (const c of concepts) {
    for (const pre of c.prerequisites) {
      assert.ok(conceptIds.has(pre), `concept ${c.id} 的 prerequisite "${pre}" 不存在`)
    }
  }
})

check('available=true 的模块至少有一个 concept', () => {
  for (const m of ALGORITHM_MODULES) {
    if (!m.available) continue
    const cs = getConceptsForModule(m.key)
    assert.ok(cs.length > 0, `模块 ${m.key} 标记为 available 但无 concept`)
  }
})

check('buildConceptGraphNodes 覆盖所有 concept', () => {
  const nodes = buildConceptGraphNodes({})
  const nodeIds = new Set(nodes.map((n) => n.id))
  for (const c of concepts) {
    assert.ok(nodeIds.has(c.id), `节点缺失 concept ${c.id}`)
  }
})

check('buildConceptGraphEdges 的端点都在节点集中', () => {
  const nodes = buildConceptGraphNodes({})
  const nodeIds = new Set(nodes.map((n) => n.id))
  const edges = buildConceptGraphEdges(nodes)
  for (const e of edges) {
    assert.ok(nodeIds.has(e.source), `边的 source "${e.source}" 不是合法节点`)
    assert.ok(nodeIds.has(e.target), `边的 target "${e.target}" 不是合法节点`)
  }
})

check('topoSortConceptIds 覆盖所有节点且无重复', () => {
  const nodes = buildConceptGraphNodes({})
  const sorted = topoSortConceptIds(nodes)
  assert.equal(sorted.length, nodes.length, '拓扑排序长度应等于节点数')
  assert.equal(new Set(sorted).size, sorted.length, '拓扑排序不应有重复')
})

check('concept id 唯一', () => {
  assert.equal(conceptIds.size, concepts.length, 'concept id 不唯一')
})

check('problem id 唯一', () => {
  const ids = new Set(problems.map((p) => p.id))
  assert.equal(ids.size, problems.length, 'problem id 不唯一')
})

console.log(`\n全部通过：${passed} 项`)