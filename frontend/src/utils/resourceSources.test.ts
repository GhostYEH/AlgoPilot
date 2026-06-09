import assert from 'node:assert/strict'

import { normalizeResourceSources } from './resourceSources'

const current = normalizeResourceSources({
  sources: [
    {
      chunk_id: 'course:demo:chapter:section',
      module_id: 'graph',
      chapter_title: '图',
      section_title: '核心概念',
      source_path: 'courses/demo.md',
      relevance_score: 0.92,
      excerpt: 'BFS 使用队列。',
    },
  ],
  meta: {},
})
assert.equal(current[0]?.chapter_title, '图')
assert.equal(current[0]?.relevance_score, 0.92)

const legacy = normalizeResourceSources({
  meta: {
    module_key: 'graph',
    knowledge_refs: ['graph-concept'],
  },
})
assert.equal(legacy.length, 1)
assert.equal(legacy[0]?.chunk_id, 'graph-concept')
assert.equal(legacy[0]?.module_id, 'graph')

assert.deepEqual(normalizeResourceSources({ meta: {} }), [])

console.log('resourceSources compatibility tests passed')
