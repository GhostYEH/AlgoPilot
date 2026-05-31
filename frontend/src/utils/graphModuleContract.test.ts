/**
 * graph 模块前后端契约轻量校验（Node + tsx）。
 */
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { ALGORITHM_MODULES, MODULE_ROUTE_NAMES } from '@/constants/modules'
import { MODULE_LEARN_CONFIGS } from '@/modules/shared/moduleRegistry'

function runTests() {
  const graph = ALGORITHM_MODULES.find((m) => m.key === 'graph')
  assert.ok(graph, 'ALGORITHM_MODULES 应包含 graph')
  assert.equal(graph.available, true, 'graph.available 应为 true')

  assert.equal(MODULE_ROUTE_NAMES.graph, 'learn-graph')

  const cfg = MODULE_LEARN_CONFIGS.graph
  assert.ok(cfg, 'moduleRegistry 应注册 graph 学习配置')
  assert.equal(cfg.routeName, 'learn-graph')
  assert.equal(cfg.key, 'graph')
  assert.ok(cfg.sections.length >= 1, 'graph 应有学习小节')
  assert.ok(cfg.animationComponent, '应配置 GraphSectionAnimation 懒加载')

  const curriculumPath = resolve(
    import.meta.dirname,
    '../modules/graph/graphCurriculum.ts',
  )
  const curriculumSrc = readFileSync(curriculumPath, 'utf8')
  assert.ok(curriculumSrc.includes('ch06-graph'))
  assert.ok(curriculumSrc.includes('graph-bfs-dfs'))
  assert.ok(curriculumSrc.includes('BFS'))

  const animPath = resolve(
    import.meta.dirname,
    '../modules/graph/components/GraphSectionAnimation.vue',
  )
  assert.ok(readFileSync(animPath, 'utf8').includes('BFS'))

  console.log('graphModuleContract.test.ts: all passed')
}

runTests()
