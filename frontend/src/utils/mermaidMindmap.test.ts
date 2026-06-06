import { normalizeMindmapSource } from './mermaidMindmap'

function assert(condition: unknown, message: string) {
  if (!condition) throw new Error(message)
}

const broken = `mindmap
  root((数据结构与算法))
    课程定位：高校计算机类专业核心课
     1. ch06-graph: 图与BFS/DFS
---
**依据知识库**：course:data_structures_algorithms:syllabus
内容校验通过`

const fixed = normalizeMindmapSource(broken)
assert(fixed.startsWith('mindmap\n  root((数据结构与算法))'), 'keeps a valid mindmap root')
assert(!fixed.includes('---'), 'removes separators')
assert(!fixed.includes('依据知识库'), 'removes knowledge annotations')
assert(!fixed.includes('内容校验'), 'removes verification text')
assert(fixed.includes('高校计算机类专业核'), 'keeps useful labels')
assert(fixed.includes('图与BFSDFS'), 'keeps graph chapter label')

const flowchart = normalizeMindmapSource('flowchart TD\n  root["栈与队列"] --> bfs["BFS 队列"]')
assert(flowchart.startsWith('mindmap\n  root((栈与队列))'), 'converts flowchart to mindmap')
assert(!flowchart.includes('flowchart'), 'removes flowchart syntax')

console.log('mermaidMindmap tests passed')
