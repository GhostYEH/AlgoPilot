<script setup lang="ts">
import * as d3 from 'd3'
import {
  computed,
  defineAsyncComponent,
  nextTick,
  onMounted,
  onUnmounted,
  ref,
  shallowRef,
  watch,
  type Component,
} from 'vue'
import { useRouter } from 'vue-router'
import {
  Close,
  FullScreen,
  ZoomIn,
  ZoomOut,
  Aim,
  ArrowRight,
  Document,
  MagicStick,
  Search,
  Guide,
  Warning,
  Timer,
  TrendCharts,
  Reading,
  ChatDotRound,
} from '@element-plus/icons-vue'
import { ALGORITHM_MODULES, MODULE_PHASE_LABELS } from '@/constants/modules'
import { MODULE_PATH_HINTS } from '@/constants/modulePathHints'
import {
  fetchPersonaProfile,
  fetchRecommendedResources,
  PROFILE_DIMENSION_LABELS,
  RESOURCE_TYPE_META,
  type GeneratedResource,
  type PersonaProfile,
} from '@/api/orchestrator'
import { buildLearningOverview } from '@/utils/learningOverview'
import { layoutUniverseDag } from '@/utils/universeDagLayout'
import { useLearningPathPlan } from '@/composables/useLearningPathPlan'
import { useModuleNavigation } from '@/composables/useModuleNavigation'
import { isLoggedIn } from '@/stores/auth'
import { useUniverseGraphEnhancements } from '@/composables/useUniverseGraphEnhancements'
import { getModuleLearnConfig } from '@/modules/shared/moduleRegistry'
import AiTutorPanel from '@/components/learning/AiTutorPanel.vue'
import { ARRAY_CURRICULUM_INTRO } from '@/modules/array/arrayCurriculum'
import { HASH_TABLE_CURRICULUM_INTRO } from '@/modules/hashTable/hashTableCurriculum'
import { STRING_CURRICULUM_INTRO } from '@/modules/string/stringCurriculum'
import { TWO_POINTERS_CURRICULUM_INTRO } from '@/modules/twoPointers/twoPointersCurriculum'
import type { LearnSection } from '@/modules/shared/learningTypes'

/** 模块 key → 画像维度 */
const MODULE_DIMENSION: Record<string, keyof PersonaProfile['dimensions']> = {
  array: 'knowledge_base',
  'linked-list': 'knowledge_base',
  'hash-table': 'knowledge_base',
  string: 'knowledge_base',
  'two-pointers': 'cognitive_style',
  'stack-queue': 'cognitive_style',
  'binary-tree': 'coding_ability',
  backtracking: 'coding_ability',
  greedy: 'coding_ability',
  dp: 'coding_ability',
  'monotonic-stack': 'error_preference',
  graph: 'learning_goals',
}

const PERSONALIZED_SLOTS = [
  { type: 'document', label: '自适应学案', icon: '📘' },
  { type: 'mindmap', label: '思维导图', icon: '🧠' },
  { type: 'code_case', label: '互动沙盒', icon: '🎮' },
  { type: 'trace_animation', label: '轨迹动画', icon: '✨' },
] as const

/** 独立学习页模块（不在 registry 中）的概述与动画组件加载器 */
const INDEPENDENT_MODULE_INTROS: Record<string, string> = {
  array: ARRAY_CURRICULUM_INTRO,
  'hash-table': HASH_TABLE_CURRICULUM_INTRO,
  string: STRING_CURRICULUM_INTRO,
  'two-pointers': TWO_POINTERS_CURRICULUM_INTRO,
}

const INDEPENDENT_MODULE_ANIMATIONS: Partial<Record<string, () => Promise<Component>>> = {
  array: () => import('@/modules/array/components/ArrayConceptAnimations.vue'),
  'hash-table': () => import('@/modules/hashTable/components/HashTableSectionAnimation.vue'),
  string: () => import('@/modules/string/components/StringSectionAnimation.vue'),
  'two-pointers': () => import('@/modules/twoPointers/components/TwoPointersSectionAnimation.vue'),
}

export type UniverseNodeStatus = 'mastered' | 'active' | 'progress' | 'locked' | 'remediation' | 'next'

export interface UniverseGraphNode {
  id: string
  label: string
  accent: string
  weight: number
  radius: number
  score: number
  percent: number
  available: boolean
  status: UniverseNodeStatus
  isRemediation?: boolean
  isNext?: boolean
  rank?: number
  reason?: string
  x?: number
  y?: number
  fx?: number | null
  fy?: number | null
}

const props = defineProps<{
  highlightKey?: string
  /** 画像完成后自动开启导览 */
  autoStartTour?: boolean
}>()

const emit = defineEmits<{
  select: [key: string]
  replan: []
}>()

const router = useRouter()
const { goModule } = useModuleNavigation()
const { plan, hasPlan, stepMap, recommendedNext, loadPlan, replan, loading } =
  useLearningPathPlan()

const containerRef = ref<HTMLDivElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const svgRef = ref<SVGSVGElement | null>(null)
const gRef = ref<SVGGElement | null>(null)

const overview = computed(() => buildLearningOverview())
const personaScores = ref<Record<string, number>>({})
const hoveredNode = ref<UniverseGraphNode | null>(null)
const tooltipPos = ref({ x: 0, y: 0 })
const selectedKey = ref(props.highlightKey ?? 'array')
const drawerNode = ref<UniverseGraphNode | null>(null)
const drawerVisible = ref(false)
const drawerResources = ref<GeneratedResource[]>([])
const drawerLoading = ref(false)

let simulation: d3.Simulation<UniverseGraphNode, d3.SimulationLinkDatum<UniverseGraphNode>> | null =
  null
let zoomBehavior: d3.ZoomBehavior<SVGSVGElement, unknown> | null = null
let chargeForce: d3.ForceManyBody<UniverseGraphNode> | null = null
let nodeSelection: d3.Selection<SVGGElement, UniverseGraphNode, SVGGElement, unknown> | null = null
let linkSelection: d3.Selection<SVGLineElement, unknown, SVGGElement, unknown> | null = null
let focusReleaseTimer: number | undefined
const focusedNodeId = ref<string | null>(null)
let starsAnimId = 0
let renderToken = 0
const graphNodes = shallowRef<UniverseGraphNode[]>([])
const graphLinks = shallowRef<Array<{ source: string; target: string }>>([])

function motionDuration(ms: number): number {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : ms
}

function scoreForModule(key: string): number {
  const dim = MODULE_DIMENSION[key]
  if (dim && personaScores.value[dim] != null) return personaScores.value[dim]
  const row = overview.value.rows.find((r) => r.key === key)
  if (row?.percent != null) return Math.max(2, Math.round(row.percent / 10))
  return 5
}

function nodeStatusFor(
  key: string,
  available: boolean,
  percent: number,
  isRemediation: boolean,
  isNext: boolean,
): UniverseNodeStatus {
  if (isRemediation) return 'remediation'
  if (isNext) return 'next'
  if (!available) return 'locked'
  if (percent >= 100) return 'mastered'
  if (key === selectedKey.value) return 'active'
  if (percent > 0) return 'progress'
  return 'progress'
}

const universeNodes = computed((): UniverseGraphNode[] => {
  const steps = plan.value?.steps ?? []
  const keys =
    steps.length > 0
      ? steps.map((s) => s.module_key)
      : overview.value.rows.filter((r) => r.available).map((r) => r.key)

  const uniqueKeys = [...new Set([...keys, ...ALGORITHM_MODULES.map((m) => m.key)])]

  return uniqueKeys.map((key) => {
    const mod = ALGORITHM_MODULES.find((m) => m.key === key)
    const row = overview.value.rows.find((r) => r.key === key)
    const step = stepMap.value.get(key)
    const score = scoreForModule(key)
    const percent = row?.percent ?? 0
    const available = row?.available ?? mod?.available ?? false
    const isRemediation = !!step?.is_remediation
    const isNext = key === plan.value?.next_module_key
    const weight = score + percent / 15 + (step?.rank ? 12 - step.rank * 0.3 : 0)
    const radius = Math.max(14, Math.min(36, 16 + weight * 1.1))

    return {
      id: key,
      label: row?.label ?? mod?.label ?? key,
      accent: row?.accent ?? mod?.accent ?? '#3d8a7e',
      weight,
      radius,
      score,
      percent,
      available,
      status: nodeStatusFor(key, available, percent, isRemediation, isNext),
      isRemediation,
      isNext,
      rank: step?.rank,
      reason: step?.reason,
    }
  })
})

const universeEdges = computed(() => {
  const edges: Array<{ source: string; target: string }> = []
  const ids = new Set(universeNodes.value.map((n) => n.id))
  for (const s of plan.value?.steps ?? []) {
    for (const dep of s.prerequisites ?? []) {
      if (ids.has(dep) && ids.has(s.module_key)) {
        edges.push({ source: dep, target: s.module_key })
      }
    }
  }
  if (!edges.length) {
    const ordered = plan.value?.ordered_keys?.length
      ? plan.value.ordered_keys.filter((k) => ids.has(k))
      : universeNodes.value.filter((n) => n.available).map((n) => n.id)
    for (let i = 0; i < ordered.length - 1; i++) {
      edges.push({ source: ordered[i], target: ordered[i + 1] })
    }
  }
  return edges
})

const enhancements = useUniverseGraphEnhancements(
  plan,
  personaScores,
  universeNodes,
  universeEdges,
  selectedKey,
)

const {
  graphView,
  searchQuery,
  searchLoading,
  searchResults,
  uiSettings,
  impact,
  tour,
  displayNodes,
  displayEdges,
  selectedConceptDetail,
  selectedModuleConcepts,
  runSearch: runEnhancementSearch,
  clearSearch,
  applySearchHit: applyEnhancementSearchHit,
} = enhancements

const tourActive = computed(() => tour.active.value)
const tourCurrentStep = computed(() => tour.currentStep.value)
const tourStepsLen = computed(() => tour.steps.value.length)
const tourStepIndex = computed(() => tour.stepIndex.value)
const tourIsFirst = computed(() => tour.isFirst.value)
const tourIsLast = computed(() => tour.isLast.value)
const struggleRippleNodes = computed(() => impact.struggleRipple.value)
const pathDiffData = computed(() => impact.pathDiff.value)
const showPathDiffFlag = computed(() => impact.showPathDiff.value)

const tooltipDimensions = computed(() => {
  const node = hoveredNode.value
  if (!node) return []
  const scores = personaScores.value
  return (Object.keys(PROFILE_DIMENSION_LABELS) as Array<keyof typeof PROFILE_DIMENSION_LABELS>).map(
    (key) => ({
      key,
      label: PROFILE_DIMENSION_LABELS[key].slice(0, 4),
      score: Math.round(((scores[key] ?? node.score) / 10) * 100),
      highlight: MODULE_DIMENSION[node.id] === key,
    }),
  )
})

const selectedNode = computed(() =>
  drawerNode.value ?? displayNodes.value.find((n) => n.id === selectedKey.value),
)

/** 抽屉中展示的知识点概述与动画配置（照搬学习界面源码） */
const drawerModulePreview = computed(() => {
  const key = selectedNode.value?.id
  if (!key) return null
  const cfg = getModuleLearnConfig(key)
  if (cfg) {
    return {
      intro: cfg.intro,
      animLoader: cfg.animationComponent,
      firstSectionId: cfg.sections[0]?.id ?? 'theory',
      firstSection: cfg.sections[0] ?? null,
      chapterTag: cfg.chapterTag,
    }
  }
  const intro = INDEPENDENT_MODULE_INTROS[key]
  const animLoader = INDEPENDENT_MODULE_ANIMATIONS[key]
  if (intro && animLoader) {
    return {
      intro,
      animLoader,
      firstSectionId: 'theory',
      firstSection: null,
      chapterTag: `${selectedNode.value?.label ?? key}篇`,
    }
  }
  return null
})

const drawerAnimCache = new Map<string, Component>()
const drawerAnimComponent = computed(() => {
  const key = selectedNode.value?.id
  if (!key) return null
  const preview = drawerModulePreview.value
  if (!preview) return null
  let comp = drawerAnimCache.get(key)
  if (!comp) {
    comp = defineAsyncComponent(preview.animLoader)
    drawerAnimCache.set(key, comp)
  }
  return comp
})

const drawerSlots = computed(() => {
  const byType = new Map(drawerResources.value.map((r) => [r.resource_type, r]))
  return PERSONALIZED_SLOTS.map((slot) => ({
    ...slot,
    resource: byType.get(slot.type),
    meta: RESOURCE_TYPE_META[slot.type],
  }))
})

/** 抽屉中算法详细信息：阶段 / 学习目标 / 推荐时长 / 模块元信息 */
const drawerModuleInfo = computed(() => {
  const key = selectedNode.value?.id
  if (!key) return null
  const mod = ALGORITHM_MODULES.find((m) => m.key === key)
  const hint = MODULE_PATH_HINTS[key]
  if (!mod || !hint) return null
  return {
    key,
    label: mod.label,
    phaseLabel: MODULE_PHASE_LABELS[mod.phase] ?? mod.phase,
    accent: mod.accent,
    summary: hint.summary,
    goals: hint.goals,
    estHours: hint.estHours,
    available: mod.available,
  }
})

/** 复用学习页 AI 助教；独立模块没有统一章节类型时，用节点目标构造等价上下文。 */
const drawerAiSection = computed<LearnSection | null>(() => {
  if (drawerModulePreview.value?.firstSection) return drawerModulePreview.value.firstSection
  const info = drawerModuleInfo.value
  if (!info) return null
  return {
    id: 'universe-overview',
    title: `${info.label}核心概念`,
    subtitle: '知识宇宙节点概览',
    difficulty: '入门',
    estMinutes: Math.max(15, Math.round(info.estHours * 60)),
    keywords: info.goals,
    overview: info.summary,
    points: info.goals,
    pitfalls: [],
    checklist: info.goals,
  }
})

watch(
  () => props.highlightKey,
  (k) => {
    if (k) selectedKey.value = k
  },
)

watch(recommendedNext, (mod) => {
  if (!props.highlightKey && mod?.key) selectedKey.value = mod.key
})

watch([displayNodes, displayEdges, graphView], () => void nextTick().then(initGraph), { deep: true })

function drawStars() {
  const canvas = canvasRef.value
  const container = containerRef.value
  if (!canvas || !container) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const w = container.clientWidth
  const h = container.clientHeight
  canvas.width = w
  canvas.height = h

  const stars = Array.from({ length: Math.floor((w * h) / 9000) }, () => ({
    x: Math.random() * w,
    y: Math.random() * h,
    r: Math.random() * 1.4 + 0.2,
    a: Math.random(),
    speed: 0.002 + Math.random() * 0.004,
  }))

  const tick = () => {
    ctx.fillStyle = '#020617'
    ctx.fillRect(0, 0, w, h)
    const grad = ctx.createRadialGradient(w * 0.5, h * 0.35, 0, w * 0.5, h * 0.35, w * 0.65)
    grad.addColorStop(0, 'rgba(61, 138, 126, 0.08)')
    grad.addColorStop(1, 'transparent')
    ctx.fillStyle = grad
    ctx.fillRect(0, 0, w, h)

    for (const s of stars) {
      s.a += s.speed
      const pulse = 0.35 + Math.sin(s.a * Math.PI * 2) * 0.25
      ctx.beginPath()
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(148, 163, 184, ${pulse})`
      ctx.fill()
    }
    starsAnimId = requestAnimationFrame(tick)
  }
  cancelAnimationFrame(starsAnimId)
  tick()
}

function nodeFill(n: UniverseGraphNode): string {
  if (n.status === 'locked') return '#1e293b'
  if (n.status === 'remediation') return '#7c2d12'
  if (n.status === 'mastered') return `color-mix(in srgb, ${n.accent} 55%, #0c4a6e)`
  return `color-mix(in srgb, ${n.accent} 35%, #0f172a)`
}

function nodeStroke(n: UniverseGraphNode): string {
  if (n.status === 'locked') return '#475569'
  if (n.status === 'remediation') return '#a87a52'
  if (n.status === 'mastered') return '#6aa878'
  if (n.status === 'next') return '#3d8a7e'
  return n.accent
}

function linkNode(
  end: string | UniverseGraphNode,
): UniverseGraphNode | undefined {
  return typeof end === 'string' ? graphNodes.value.find((n) => n.id === end) : end
}

function fitGraphToView(nodes: UniverseGraphNode[], width: number, height: number) {
  const svgEl = svgRef.value
  if (!svgEl || !zoomBehavior || !nodes.length) return

  let minX = Infinity
  let maxX = -Infinity
  let minY = Infinity
  let maxY = -Infinity
  for (const n of nodes) {
    const r = (n.radius ?? 20) + 20
    const x = n.x ?? width / 2
    const y = n.y ?? height / 2
    minX = Math.min(minX, x - r)
    maxX = Math.max(maxX, x + r)
    minY = Math.min(minY, y - r)
    maxY = Math.max(maxY, y + r)
  }
  const dx = Math.max(maxX - minX, 80)
  const dy = Math.max(maxY - minY, 80)
  const midX = (minX + maxX) / 2
  const midY = (minY + maxY) / 2
  const scale = Math.min(1.8, 0.88 / Math.max(dx / width, dy / height, 0.05))
  const tx = width / 2 - scale * midX
  const ty = height / 2 - scale * midY

  d3.select(svgEl)
    .transition()
    .duration(500)
    .call(zoomBehavior.transform, d3.zoomIdentity.translate(tx, ty).scale(scale))
}

function getLinkedNodeIds(nodeId: string): Set<string> {
  const ids = new Set<string>([nodeId])
  for (const l of graphLinks.value) {
    const s = typeof l.source === 'string' ? l.source : (l.source as UniverseGraphNode).id
    const t = typeof l.target === 'string' ? l.target : (l.target as UniverseGraphNode).id
    if (s === nodeId) ids.add(t)
    if (t === nodeId) ids.add(s)
  }
  return ids
}

function applyFocusStyles(focusId: string | null) {
  if (!nodeSelection || !linkSelection) return
  const linked = focusId ? getLinkedNodeIds(focusId) : null

  nodeSelection
    .classed('universe-node--focused', (d) => d.id === focusId)
    .classed('universe-node--dimmed', (d) => !!focusId && !linked!.has(d.id))

  nodeSelection
    .select<SVGCircleElement>('.node-core')
    .transition()
    .duration(motionDuration(320))
    .attr('r', (d) => (d.id === focusId ? d.radius * 1.28 : d.radius))

  linkSelection
    .transition()
    .duration(motionDuration(320))
    .attr('stroke-opacity', (d) => {
      if (!focusId) return 0.6
      const link = d as { source: string | UniverseGraphNode; target: string | UniverseGraphNode }
      const s = linkNode(link.source)?.id
      const t = linkNode(link.target)?.id
      return s && t && linked!.has(s) && linked!.has(t) ? 0.95 : 0.1
    })
    .attr('stroke-width', (d) => {
      if (!focusId) return 1.5
      const link = d as { source: string | UniverseGraphNode; target: string | UniverseGraphNode }
      const s = linkNode(link.source)?.id
      const t = linkNode(link.target)?.id
      return s && t && linked!.has(s) && linked!.has(t) ? 2.5 : 1
    })
}

function focusNodeSpread(node: UniverseGraphNode) {
  const container = containerRef.value
  if (!container || !simulation || !chargeForce) return

  if (focusReleaseTimer) window.clearTimeout(focusReleaseTimer)

  focusedNodeId.value = node.id
  const width = container.clientWidth
  const height = container.clientHeight
  const cx = width / 2
  const cy = height / 2

  panToNode(node.id)

  const gn = graphNodes.value.find((n) => n.id === node.id)
  if (gn) {
    gn.fx = cx
    gn.fy = cy
  }

  chargeForce.strength(-960)
  applyFocusStyles(node.id)
  simulation.alpha(0.9).restart()

  focusReleaseTimer = window.setTimeout(() => {
    chargeForce?.strength(-380)
    if (gn) {
      gn.fx = null
      gn.fy = null
    }
    focusedNodeId.value = null
    applyFocusStyles(null)
    simulation?.alpha(0.35).restart()
    focusReleaseTimer = undefined
  }, motionDuration(1500))
}

function clearNodeFocus() {
  if (focusReleaseTimer) {
    window.clearTimeout(focusReleaseTimer)
    focusReleaseTimer = undefined
  }
  focusedNodeId.value = null
  chargeForce?.strength(-380)
  for (const n of graphNodes.value) {
    n.fx = null
    n.fy = null
  }
  applyFocusStyles(null)
  simulation?.alpha(0.25).restart()
}

function panToNode(nodeId: string) {
  const node = graphNodes.value.find((n) => n.id === nodeId)
  const svgEl = svgRef.value
  const container = containerRef.value
  if (!node || !svgEl || !zoomBehavior || !container) return
  const width = container.clientWidth
  const height = container.clientHeight
  const scale = 1.4
  const tx = width / 2 - scale * (node.x ?? width / 2)
  const ty = height / 2 - scale * (node.y ?? height / 2)
  d3.select(svgEl)
    .transition()
    .duration(motionDuration(450))
    .call(zoomBehavior.transform, d3.zoomIdentity.translate(tx, ty).scale(scale))
}

function initGraph() {
  const svgEl = svgRef.value
  const gEl = gRef.value
  const container = containerRef.value
  if (!svgEl || !gEl || !container) return

  if (focusReleaseTimer) {
    window.clearTimeout(focusReleaseTimer)
    focusReleaseTimer = undefined
  }
  focusedNodeId.value = null
  nodeSelection = null
  linkSelection = null

  const token = ++renderToken
  const width = container.clientWidth
  const height = container.clientHeight

  const nodes: UniverseGraphNode[] = displayNodes.value.map((n) => ({ ...n }))
  const links = displayEdges.value.map((e) => ({ ...e }))

  const layoutPos = layoutUniverseDag(
    nodes.map((n) => ({ id: n.id, rank: n.rank, radius: n.radius })),
    links,
    width,
    height,
  )
  for (const n of nodes) {
    const p = layoutPos.get(n.id)
    if (p) {
      n.x = p.x
      n.y = p.y
    }
  }

  graphNodes.value = nodes
  graphLinks.value = links

  if (simulation) simulation.stop()

  const svg = d3.select(svgEl)
  svg.attr('width', width).attr('height', height)
  const g = d3.select(gEl)
  g.selectAll('*').remove()

  if (!zoomBehavior) {
    zoomBehavior = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.15, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })
    svg.call(zoomBehavior)
  }

  const linkG = g.append('g').attr('class', 'universe-links')
  const nodeG = g.append('g').attr('class', 'universe-nodes')

  const linkForce = d3
    .forceLink<UniverseGraphNode, { source: string; target: string }>(links)
    .id((d) => d.id)
    .distance(140)
    .strength(0.55)

  const linkSel = linkG
    .selectAll<SVGLineElement, { source: string | UniverseGraphNode; target: string | UniverseGraphNode }>(
      'line',
    )
    .data(links)
    .join('line')
    .attr('stroke', 'rgba(61, 138, 126, 0.35)')
    .attr('stroke-width', 1.5)
    .attr('stroke-opacity', 0.6)

  linkSelection = linkSel as d3.Selection<SVGLineElement, unknown, SVGGElement, unknown>

  const nodeSel = nodeG
    .selectAll<SVGGElement, UniverseGraphNode>('g')
    .data(nodes, (d) => d.id)
    .join('g')
    .attr('class', (d) => {
      const classes = ['universe-node', `universe-node--${d.status}`]
      if (d.isNext) classes.push('universe-node--next')
      if (d.isRemediation || d.status === 'remediation') classes.push('universe-node--remediation')
      if (d.status === 'mastered') classes.push('universe-node--mastered-glow')
      return classes.join(' ')
    })
    .style('cursor', 'pointer')
    .call(
      d3
        .drag<SVGGElement, UniverseGraphNode>()
        .on('start', (event, d) => {
          if (!event.active) simulation?.alphaTarget(0.3).restart()
          d.fx = d.x
          d.fy = d.y
        })
        .on('drag', (event, d) => {
          d.fx = event.x
          d.fy = event.y
        })
        .on('end', (event, d) => {
          if (!event.active) simulation?.alphaTarget(0)
          d.fx = null
          d.fy = null
        }),
    )

  nodeSel
    .filter((d) => d.isRemediation || d.status === 'remediation')
    .append('circle')
    .attr('class', 'remediation-halo')
    .attr('r', (d) => d.radius + 10)
    .attr('fill', 'none')
    .attr('stroke', '#a87a52')
    .attr('stroke-width', 2)
    .attr('pointer-events', 'none')

  nodeSel
    .append('circle')
    .attr('class', 'node-core')
    .attr('r', (d) => d.radius)
    .attr('fill', (d) => nodeFill(d))
    .attr('stroke', (d) => nodeStroke(d))
    .attr('stroke-width', (d) => (d.isNext || d.isRemediation ? 3 : 2))

  nodeSel
    .append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '0.35em')
    .attr('fill', (d) => (d.status === 'locked' ? '#64748b' : '#e2e8f0'))
    .attr('font-size', (d) => Math.max(9, Math.min(12, d.radius * 0.45)))
    .attr('pointer-events', 'none')
    .text((d) => (d.label.length > 5 ? d.label.slice(0, 4) + '…' : d.label))

  nodeSel
    .filter((d) => !!d.rank)
    .append('text')
    .attr('y', (d) => -d.radius - 6)
    .attr('text-anchor', 'middle')
    .attr('fill', '#3d8a7e')
    .attr('font-size', 9)
    .attr('pointer-events', 'none')
    .text((d) => `#${d.rank}`)

  nodeSel
    .on('mouseenter', (event, d) => {
      hoveredNode.value = d
      tooltipPos.value = { x: event.clientX, y: event.clientY }
    })
    .on('mousemove', (event) => {
      tooltipPos.value = { x: event.clientX, y: event.clientY }
    })
    .on('mouseleave', () => {
      hoveredNode.value = null
    })
    .on('click', (_, d) => {
      void onNodeClick(d)
    })

  nodeSelection = nodeSel

  chargeForce = d3.forceManyBody<UniverseGraphNode>().strength(-380)

  simulation = d3
    .forceSimulation(nodes)
    .force('link', linkForce)
    .force('charge', chargeForce)
    .force('center', d3.forceCenter(width / 2, height / 2).strength(0.05))
    .force(
      'x',
      d3
        .forceX<UniverseGraphNode>((d) => layoutPos.get(d.id)?.x ?? width / 2)
        .strength(0.18),
    )
    .force(
      'y',
      d3
        .forceY<UniverseGraphNode>((d) => layoutPos.get(d.id)?.y ?? height / 2)
        .strength(0.18),
    )
    .force(
      'collision',
      d3.forceCollide<UniverseGraphNode>().radius((d) => d.radius + 16),
    )
    .alpha(0.9)
    .alphaDecay(0.035)
    .on('tick', () => {
      linkSel
        .attr('x1', (d) => linkNode(d.source)?.x ?? 0)
        .attr('y1', (d) => linkNode(d.source)?.y ?? 0)
        .attr('x2', (d) => linkNode(d.target)?.x ?? 0)
        .attr('y2', (d) => linkNode(d.target)?.y ?? 0)

      nodeSel.attr('transform', (d) => `translate(${d.x ?? 0},${d.y ?? 0})`)
    })
    .on('end', () => {
      if (token === renderToken) fitGraphToView(nodes, width, height)
      if (tour.active.value && tour.currentStep.value) {
        panToNode(tour.currentStep.value.id)
      }
    })

  if (token !== renderToken) return
}

function zoomBy(factor: number) {
  const svgEl = svgRef.value
  if (!svgEl || !zoomBehavior) return
  d3.select(svgEl).transition().duration(300).call(zoomBehavior.scaleBy, factor)
}

function resetView() {
  const svgEl = svgRef.value
  if (!svgEl || !zoomBehavior) return
  clearNodeFocus()
  d3.select(svgEl).transition().duration(400).call(zoomBehavior.transform, d3.zoomIdentity)
}

async function onNodeClick(node: UniverseGraphNode) {
  hoveredNode.value = null
  drawerNode.value = { ...node }
  selectedKey.value = node.id
  focusNodeSpread(node)
  emit('select', node.id)
  drawerVisible.value = true
  drawerLoading.value = true
  try {
    drawerResources.value = isLoggedIn.value
      ? await fetchRecommendedResources({
          module_key:
            enhancements.conceptNodesRaw.value.find((concept) => concept.id === node.id)?.moduleKey ?? node.id,
          limit: 8,
        })
      : []
  } catch {
    drawerResources.value = []
  } finally {
    drawerLoading.value = false
  }
}

async function animateSearchHit(hit: import('@/api/search').SemanticSearchResult, openDrawer = false) {
  hoveredNode.value = null
  applyEnhancementSearchHit(hit)
  await nextTick()
  await new Promise<void>((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve())))
  const targetId = hit.concept_ids[0] || hit.module_key || hit.node_ids[0] || hit.id
  const node = graphNodes.value.find((item) => item.id === targetId)
  if (!node) return
  focusNodeSpread(node)
  if (openDrawer) void onNodeClick(node)
}

async function runSearch() {
  await runEnhancementSearch()
  if (searchResults.value[0]) await animateSearchHit(searchResults.value[0])
}

function onSearchHit(hit: import('@/api/search').SemanticSearchResult) {
  searchResults.value = []
  void animateSearchHit(hit, true)
}

function openResource(r: GeneratedResource) {
  router.push({ name: 'resources', query: { highlight: String(r.id) } })
}

async function onReplan() {
  emit('replan')
  await replan({ trigger: 'universe', triggerLabel: '宇宙图路径规划' })
}

function renderMiniRadar(svgRoot: SVGSVGElement, dims: Array<{ label: string; score: number; highlight?: boolean }>) {
  const size = 120
  const radius = 42
  const n = dims.length
  if (!n) return

  const svg = d3.select(svgRoot)
  svg.selectAll('*').remove()
  svg.attr('width', size).attr('height', size)
  const g = svg.append('g').attr('transform', `translate(${size / 2},${size / 2})`)
  const angleSlice = (Math.PI * 2) / n
  const rScale = d3.scaleLinear().domain([0, 100]).range([0, radius])

  ;[25, 50, 75, 100].forEach((lvl) => {
    g.append('circle')
      .attr('r', rScale(lvl))
      .attr('fill', 'none')
      .attr('stroke', 'rgba(61, 138, 126, 0.2)')
      .attr('stroke-dasharray', '2,2')
  })

  dims.forEach((d, i) => {
    const angle = angleSlice * i - Math.PI / 2
    g.append('line')
      .attr('x2', radius * Math.cos(angle))
      .attr('y2', radius * Math.sin(angle))
      .attr('stroke', d.highlight ? 'rgba(74,126,148,0.6)' : 'rgba(71,85,105,0.5)')
  })

  const area = d3
    .areaRadial<{ score: number }>()
    .radius((d) => rScale(d.score))
    .angle((_, i) => i * angleSlice)
    .curve(d3.curveLinearClosed)

  g.append('path')
    .datum(dims.map((d) => ({ score: d.score })))
    .attr('fill', 'rgba(61, 138, 126, 0.25)')
    .attr('stroke', '#3d8a7e')
    .attr('stroke-width', 1.5)
    .attr('d', area)
}

const miniRadarRef = ref<SVGSVGElement | null>(null)
watch([hoveredNode, tooltipDimensions], async () => {
  await nextTick()
  if (miniRadarRef.value && hoveredNode.value) {
    renderMiniRadar(miniRadarRef.value, tooltipDimensions.value)
  }
})

onMounted(async () => {
  if (isLoggedIn.value) {
    try {
      const p = await fetchPersonaProfile()
      personaScores.value = p.dimension_scores ?? {}
    } catch {
      personaScores.value = {}
    }
  }
  await loadPlan()
  if (plan.value?.next_module_key) {
    selectedKey.value = props.highlightKey ?? plan.value.next_module_key
  }
  if (props.autoStartTour && hasPlan.value) {
    tour.start()
  }
  drawStars()
  await nextTick()
  initGraph()
  window.addEventListener('resize', onResize)
})

function onResize() {
  drawStars()
  void nextTick().then(initGraph)
}

onUnmounted(() => {
  renderToken += 1
  if (focusReleaseTimer) window.clearTimeout(focusReleaseTimer)
  simulation?.stop()
  cancelAnimationFrame(starsAnimId)
  window.removeEventListener('resize', onResize)
  if (svgRef.value) d3.select(svgRef.value).on('.zoom', null)
})
</script>

<template>
  <div class="universe">
    <el-alert
      v-if="hasPlan"
      type="success"
      :closable="false"
      show-icon
      class="universe-banner"
    >
      <template #title>算法知识宇宙已同步</template>
      <p class="banner-text">{{ plan?.summary }}</p>
    </el-alert>

    <el-alert v-if="isLoggedIn && !hasPlan" type="info" :closable="false" show-icon class="universe-banner">
      <template #title>个性化宇宙待生成</template>
      完成画像访谈或点击下方按钮，生成千人千面 DAG 星图。
      <el-button type="primary" size="small" :loading="loading" class="banner-btn" @click="onReplan">
        生成个性化宇宙
      </el-button>
    </el-alert>

    <div ref="containerRef" class="universe-canvas">
      <canvas ref="canvasRef" class="stars-layer" aria-hidden="true" />
      <svg ref="svgRef" class="graph-layer" role="img" aria-label="算法知识宇宙力导向图">
        <g ref="gRef" />
      </svg>

      <div class="universe-hud">
        <span class="hud-title"><el-icon><FullScreen /></el-icon> 算法知识宇宙</span>
        <el-radio-group v-model="graphView" size="small" class="hud-view-toggle">
          <el-radio-button value="module">模块</el-radio-button>
          <el-radio-button value="concept">概念</el-radio-button>
        </el-radio-group>
        <div class="hud-actions">
          <el-button size="small" :icon="Guide" @click="tour.start()">导览</el-button>
          <el-button size="small" :icon="Warning" @click="impact.togglePathDiff()">路径 Diff</el-button>
          <el-button circle size="small" :icon="ZoomIn" title="放大" @click="zoomBy(1.25)" />
          <el-button circle size="small" :icon="ZoomOut" title="缩小" @click="zoomBy(0.8)" />
          <el-button circle size="small" :icon="Aim" title="复位视图" @click="resetView" />
        </div>
      </div>

      <div class="universe-search">
        <el-input
          v-model="searchQuery"
          placeholder="语义搜索：如「单调栈 medium 入门题」"
          clearable
          size="small"
          @keyup.enter="runSearch"
          @clear="clearSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
          <template #append>
            <el-button :loading="searchLoading" @click="runSearch">搜索</el-button>
          </template>
        </el-input>
        <ul v-if="searchResults.length" class="search-results">
          <li
            v-for="hit in searchResults"
            :key="`${hit.kind}-${hit.id}`"
            role="button"
            tabindex="0"
            @click="onSearchHit(hit)"
            @keyup.enter="onSearchHit(hit)"
          >
            <span class="hit-kind">{{ hit.kind }}</span>
            <strong>{{ hit.title }}</strong>
            <span class="hit-snippet">{{ hit.snippet }}</span>
          </li>
        </ul>
      </div>

      <aside v-if="tourActive && tourCurrentStep" class="tour-panel">
        <header class="tour-head">
          <span>Guided Tour · {{ tourStepIndex + 1 }}/{{ tourStepsLen }}</span>
          <el-button link type="primary" @click="tour.stop()">退出</el-button>
        </header>
        <h4>{{ tourCurrentStep.title }}</h4>
        <p>{{ tourCurrentStep.summary }}</p>
        <p v-if="uiSettings.encouragementLevel === 'high'" class="tour-encourage">一步一步来，你已经很棒了！</p>
        <div class="tour-actions">
          <el-button size="small" :disabled="tourIsFirst" @click="tour.prev()">上一步</el-button>
          <el-button type="primary" size="small" @click="tour.next()">
            {{ tourIsLast ? '完成' : '下一步' }}
          </el-button>
        </div>
      </aside>

      <div v-if="struggleRippleNodes.length" class="impact-ripple">
        <span class="impact-label">受挫波及先修：</span>
        <el-tag
          v-for="n in struggleRippleNodes"
          :key="n.id"
          type="danger"
          size="small"
          effect="plain"
        >
          {{ n.label }}
        </el-tag>
      </div>

      <div v-if="showPathDiffFlag && (pathDiffData.added.length || pathDiffData.removed.length)" class="impact-diff">
        <span v-if="pathDiffData.added.length">新增：{{ pathDiffData.added.join('、') }}</span>
        <span v-if="pathDiffData.removed.length">移除：{{ pathDiffData.removed.join('、') }}</span>
      </div>

      <div class="universe-legend">
        <span><i class="dot dot--mastered" /> 已掌握</span>
        <span><i class="dot dot--next" /> 推荐下一步</span>
        <span><i class="dot dot--locked" /> 未解锁</span>
        <span><i class="dot dot--remediation" /> 巩固 Remediation</span>
      </div>

      <div class="universe-stats">
        <span>总进度 {{ overview.overallPercent }}%</span>
        <span>·</span>
        <span>已跟踪 {{ overview.trackedModules }} 模块</span>
      </div>
    </div>

    <Teleport to="body">
      <div
        v-if="hoveredNode"
        class="universe-tooltip"
        :style="{ left: `${tooltipPos.x + 16}px`, top: `${tooltipPos.y + 16}px` }"
      >
        <div class="tooltip-head">
          <span class="tooltip-title">{{ hoveredNode.label }}</span>
          <el-tag size="small" effect="dark" :type="hoveredNode.status === 'remediation' ? 'warning' : 'info'">
            {{ hoveredNode.percent }}% 熟练
          </el-tag>
        </div>
        <p v-if="hoveredNode.reason" class="tooltip-reason">{{ hoveredNode.reason }}</p>
        <div class="tooltip-radar-wrap">
          <svg ref="miniRadarRef" class="tooltip-radar" role="img" aria-label="节点熟练度雷达" />
          <ul class="tooltip-dims">
            <li
              v-for="d in tooltipDimensions.slice(0, 4)"
              :key="d.key"
              :class="{ 'is-highlight': d.highlight }"
            >
              {{ d.label }} <strong>{{ d.score }}</strong>
            </li>
          </ul>
        </div>
        <p class="tooltip-hint">单击节点 · 展开个性化资源抽屉</p>
      </div>
    </Teleport>

    <el-drawer
      v-model="drawerVisible"
      direction="rtl"
      size="min(520px, 94vw)"
      class="universe-drawer"
      modal-class="universe-drawer-overlay"
      append-to-body
      destroy-on-close
    >
      <template #header>
        <div class="drawer-titlebar">
          <span class="drawer-title-kicker">算法知识宇宙</span>
          <strong>{{ selectedNode?.label ?? '知识点详情' }}</strong>
        </div>
      </template>

      <div v-if="selectedNode" class="drawer-content">
        <div class="drawer-head">
          <div
            class="drawer-node-preview"
            :class="`drawer-node-preview--${selectedNode.status}`"
            :style="{ '--node-accent': selectedNode.accent }"
          >
            <span class="preview-label">{{ selectedNode.label }}</span>
            <span class="preview-pct">{{ selectedNode.percent }}%</span>
          </div>
          <p v-if="selectedNode.reason" class="drawer-reason">
            {{ selectedNode.reason }}
          </p>

          <!-- 直达学习页按钮：置顶突出 -->
          <div class="drawer-cta">
            <el-button
              v-if="selectedNode.available"
              type="primary"
              size="large"
              class="cta-learn-btn"
              @click="goModule(selectedNode.id)"
            >
              <el-icon><Reading /></el-icon>
              深入学习「{{ selectedNode.label }}」
              <el-icon class="el-icon--right"><ArrowRight /></el-icon>
            </el-button>
            <el-button v-else disabled size="large" class="cta-learn-btn">
              内容规划中
            </el-button>
          </div>
        </div>

        <!-- 算法详细信息卡片 -->
        <section v-if="drawerModuleInfo" class="drawer-info-card">
          <h4 class="drawer-section-title">
            <el-icon><TrendCharts /></el-icon>
            算法详细信息
          </h4>
          <div class="info-meta-row">
            <el-tag size="small" effect="plain" :style="{ borderColor: drawerModuleInfo.accent, color: drawerModuleInfo.accent }">
              {{ drawerModuleInfo.phaseLabel }}
            </el-tag>
            <span class="info-meta-item">
              <el-icon><Timer /></el-icon>
              推荐 {{ drawerModuleInfo.estHours }} 小时
            </span>
            <span class="info-meta-item">
              <el-icon><Aim /></el-icon>
              熟练度 {{ selectedNode.percent }}%
            </span>
          </div>
          <p class="info-summary">{{ drawerModuleInfo.summary }}</p>
          <div class="info-goals">
            <span class="info-goals-label">学习目标</span>
            <ul class="info-goals-list">
              <li v-for="(g, i) in drawerModuleInfo.goals" :key="i">{{ g }}</li>
            </ul>
          </div>
          <div v-if="selectedModuleConcepts.length" class="drawer-concepts">
            <span class="drawer-concepts-label">概念子图</span>
            <el-tag
              v-for="c in selectedModuleConcepts"
              :key="c.id"
              size="small"
              effect="plain"
              class="concept-chip"
              @click="graphView = 'concept'; selectedKey = c.id"
            >
              {{ c.label }}
            </el-tag>
          </div>
          <div v-if="selectedConceptDetail" class="drawer-problems">
            <span class="drawer-concepts-label">关联 OJ</span>
            <el-button
              v-for="p in selectedConceptDetail.problems"
              :key="p.slug"
              link
              type="primary"
              @click="router.push({ name: 'practice-slug', params: { slug: p.slug } })"
            >
              {{ p.label }}
            </el-button>
          </div>
        </section>

        <template v-if="drawerModulePreview">
          <h4 class="drawer-section-title">
            <el-icon><MagicStick /></el-icon>
            知识点概述
          </h4>
          <p class="drawer-overview-text">{{ drawerModulePreview.intro }}</p>

          <h4 class="drawer-section-title">
            <el-icon><MagicStick /></el-icon>
            动画演示
          </h4>
          <div class="drawer-anim-stage">
            <component
              v-if="drawerAnimComponent"
              :is="drawerAnimComponent"
              :key="selectedNode.id"
              :section-id="drawerModulePreview.firstSectionId"
            />
          </div>

          <h4 class="drawer-section-title drawer-section-title--ai">
            <el-icon><ChatDotRound /></el-icon>
            向 AI 助教提问
          </h4>
          <AiTutorPanel
            v-if="drawerAiSection"
            :key="`universe-tutor-${selectedNode.id}`"
            :module-key="selectedNode.id"
            :module-title="selectedNode.label"
            :chapter-tag="drawerModulePreview.chapterTag"
            :module-intro="drawerModulePreview.intro"
            :section="drawerAiSection"
          />
        </template>

        <h4 class="drawer-section-title">
          <el-icon><MagicStick /></el-icon>
          五种个性化学习资源
        </h4>

        <el-skeleton v-if="drawerLoading" :rows="4" animated />

        <div v-else class="resource-grid">
          <article
            v-for="slot in drawerSlots"
            :key="slot.type"
            class="resource-card"
            :class="{ 'resource-card--filled': !!slot.resource }"
            role="button"
            tabindex="0"
            @click="slot.resource && openResource(slot.resource)"
            @keyup.enter="slot.resource && openResource(slot.resource)"
          >
            <span class="resource-icon">{{ slot.icon }}</span>
            <div class="resource-body">
              <div class="resource-type">{{ slot.label }}</div>
              <div v-if="slot.resource" class="resource-title">{{ slot.resource.title }}</div>
              <div v-else class="resource-placeholder">
                {{ isLoggedIn ? '登录后可在资源库一键生成' : '登录解锁' }}
              </div>
              <div v-if="slot.meta" class="resource-agent">{{ slot.meta.agentName }}</div>
            </div>
            <el-icon v-if="slot.resource" class="resource-arrow"><Document /></el-icon>
          </article>
        </div>

        <div class="drawer-actions">
          <el-button
            v-if="selectedNode.available"
            type="primary"
            @click="goModule(selectedNode.id)"
          >
            深入学习
            <el-icon class="el-icon--right"><ArrowRight /></el-icon>
          </el-button>
          <el-button v-else disabled>内容规划中</el-button>
          <el-button @click="router.push({ name: 'resources' })">资源库</el-button>
        </div>
      </div>

      <el-empty v-else description="未找到该知识节点的详情，请重新选择图谱节点" />

      <template #footer>
        <el-button :icon="Close" @click="drawerVisible = false">关闭</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<style scoped>
.universe {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.universe-banner {
  margin: 0;
}

.banner-text {
  margin: 4px 0 0;
  font-size: 13px;
  line-height: 1.5;
}

.banner-btn {
  margin-top: 8px;
}

.universe-canvas {
  position: relative;
  width: 100%;
  min-height: min(72vh, 720px);
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--alp-color-primary-glow);
  box-shadow:
    0 0 60px rgba(var(--alp-color-primary-rgb), 0.08),
    inset 0 0 80px rgba(2, 6, 23, 0.9);
}

.stars-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.graph-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  cursor: grab;
}

.graph-layer:active {
  cursor: grabbing;
}

.graph-layer :deep(.universe-node--remediation .remediation-halo) {
  animation: remediation-halo-pulse 1s ease-in-out infinite;
}

.graph-layer :deep(.universe-node--remediation .node-core) {
  filter: drop-shadow(0 0 16px rgba(168, 122, 82,0.95));
  animation: warn-pulse 1.1s ease-in-out infinite;
}

.graph-layer :deep(.universe-node--mastered-glow .node-core) {
  filter: drop-shadow(0 0 14px rgba(106, 168, 120,0.85));
  animation: breathe-glow 2.8s ease-in-out infinite;
}

.graph-layer :deep(.universe-node--next .node-core) {
  filter: drop-shadow(0 0 14px rgba(var(--alp-color-primary-rgb), 0.85));
}

.graph-layer :deep(.universe-node--locked .node-core) {
  opacity: 0.55;
}

.graph-layer :deep(.universe-node--dimmed) {
  opacity: 0.28;
  transition: opacity 0.35s ease;
}

.graph-layer :deep(.universe-node--dimmed .node-core) {
  filter: none;
}

.graph-layer :deep(.universe-node--focused .node-core) {
  filter: drop-shadow(0 0 22px rgba(var(--alp-color-primary-rgb), 1));
  animation: focus-pulse 1.2s ease-in-out infinite;
}

@keyframes focus-pulse {
  0%,
  100% {
    filter: drop-shadow(0 0 18px rgba(var(--alp-color-primary-rgb), 0.85));
  }
  50% {
    filter: drop-shadow(0 0 28px rgba(var(--alp-color-accent-rgb), 0.95));
  }
}

@keyframes remediation-halo-pulse {
  0%,
  100% {
    stroke-opacity: 0.35;
    stroke: #a87a52;
  }
  50% {
    stroke-opacity: 1;
    stroke: #9e5a5a;
  }
}

@keyframes breathe-glow {
  0%,
  100% {
    filter: drop-shadow(0 0 8px rgba(106, 168, 120,0.5));
  }
  50% {
    filter: drop-shadow(0 0 18px rgba(var(--alp-color-primary-rgb), 0.85));
  }
}

@keyframes warn-pulse {
  0%,
  100% {
    stroke-width: 2;
    filter: drop-shadow(0 0 8px rgba(158, 90, 90,0.6));
  }
  50% {
    stroke-width: 3.5;
    filter: drop-shadow(0 0 22px rgba(168, 122, 82,1));
  }
}

.universe-hud {
  position: absolute;
  top: 12px;
  left: 14px;
  right: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  pointer-events: none;
  z-index: 2;
}

.hud-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #e2e8f0;
  text-shadow: 0 0 12px rgba(var(--alp-color-primary-rgb), 0.5);
  pointer-events: auto;
}

.hud-actions {
  display: flex;
  gap: 6px;
  pointer-events: auto;
}

.hud-actions :deep(.el-button) {
  background: rgba(15, 23, 42, 0.75);
  border-color: var(--alp-color-primary-glow);
  color: #e2e8f0;
}

.universe-legend {
  position: absolute;
  bottom: 12px;
  left: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 11px;
  color: #94a3b8;
  z-index: 2;
}

.dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 4px;
  vertical-align: middle;
}

.dot--mastered {
  background: #6aa878;
  box-shadow: 0 0 8px #6aa878;
}

.dot--next {
  background: var(--alp-color-primary);
  box-shadow: 0 0 8px var(--alp-color-primary-glow);
}

.dot--locked {
  background: #475569;
}

.dot--remediation {
  background: #a87a52;
  animation: warn-pulse 1.1s ease-in-out infinite;
}

.universe-stats {
  position: absolute;
  bottom: 12px;
  right: 14px;
  font-size: 11px;
  color: #64748b;
  z-index: 2;
}

.universe-tooltip {
  position: fixed;
  z-index: 3000;
  min-width: 220px;
  max-width: 280px;
  padding: 12px 14px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.96);
  border: 1px solid var(--alp-color-primary-glow);
  box-shadow:
    0 0 24px rgba(var(--alp-color-primary-rgb), 0.2),
    0 8px 32px rgba(0, 0, 0, 0.5);
  pointer-events: none;
  backdrop-filter: blur(8px);
}

.tooltip-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.tooltip-title {
  font-weight: 600;
  color: #f1f5f9;
  font-size: 14px;
}

.tooltip-reason {
  margin: 0 0 8px;
  font-size: 11px;
  color: #94a3b8;
  line-height: 1.4;
}

.tooltip-radar-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tooltip-radar {
  flex-shrink: 0;
}

.tooltip-dims {
  list-style: none;
  margin: 0;
  padding: 0;
  font-size: 10px;
  color: #94a3b8;
  line-height: 1.6;
}

.tooltip-dims li.is-highlight {
  color: var(--alp-color-primary);
}

.tooltip-dims strong {
  color: #e2e8f0;
  font-variant-numeric: tabular-nums;
}

.tooltip-hint {
  margin: 8px 0 0;
  font-size: 10px;
  color: #64748b;
}

.drawer-head {
  margin-bottom: 16px;
}

.drawer-node-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.9);
  border: 1px solid color-mix(in srgb, var(--node-accent) 40%, transparent);
  margin-bottom: 12px;
}

.drawer-node-preview--remediation {
  border-color: #a87a52;
  box-shadow: 0 0 20px rgba(168, 122, 82,0.25);
  animation: warn-pulse 1.2s ease-in-out infinite;
}

.drawer-node-preview--mastered {
  box-shadow: 0 0 20px rgba(106, 168, 120,0.2);
}

.preview-label {
  font-size: 18px;
  font-weight: 600;
  color: var(--node-accent);
}

.preview-pct {
  font-size: 22px;
  font-weight: 700;
  color: #e2e8f0;
}

.drawer-reason {
  margin: 0 0 8px;
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(var(--alp-color-primary-rgb), 0.1);
  font-size: 12px;
  line-height: 1.5;
}

.drawer-summary {
  margin: 0;
  font-size: 13px;
  color: var(--alp-color-muted);
  line-height: 1.6;
}

.drawer-section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
}

.drawer-overview-text {
  margin: 0 0 16px;
  font-size: 13px;
  color: var(--alp-color-text);
  line-height: 1.7;
  padding: 12px 14px;
  border-radius: 10px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.drawer-anim-stage {
  margin-bottom: 18px;
  padding: 12px;
  border-radius: 10px;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
  min-height: 200px;
  overflow: hidden;
}

.drawer-anim-stage :deep(.anim-stage),
.drawer-anim-stage :deep(.section-animation),
.drawer-anim-stage :deep(.concept-animations) {
  min-height: 200px;
}

.resource-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.resource-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px dashed var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
}

.resource-card--filled {
  border-style: solid;
  cursor: pointer;
}

.resource-card--filled:hover {
  border-color: var(--alp-color-primary);
  box-shadow: 0 4px 16px rgba(var(--alp-color-primary-rgb), 0.12);
}

.resource-icon {
  font-size: 22px;
  line-height: 1;
}

.resource-type {
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-primary);
}

.resource-title {
  font-size: 13px;
  color: var(--alp-color-text);
  margin-top: 2px;
}

.resource-placeholder {
  font-size: 12px;
  color: var(--alp-color-muted);
  margin-top: 2px;
}

.resource-agent {
  font-size: 10px;
  color: var(--alp-color-muted);
  margin-top: 4px;
}

.resource-arrow {
  margin-left: auto;
  color: var(--alp-color-muted);
}

.drawer-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.hud-view-toggle {
  margin: 0 8px;
}

.universe-search {
  position: absolute;
  top: 52px;
  left: 12px;
  right: 12px;
  z-index: 4;
  max-width: 420px;
}

.search-results {
  list-style: none;
  margin: 6px 0 0;
  padding: 0;
  max-height: 160px;
  overflow: auto;
  background: rgba(15, 23, 42, 0.92);
  border: 1px solid var(--alp-color-primary-glow);
  border-radius: 8px;
}

.search-results li {
  padding: 8px 10px;
  cursor: pointer;
  border-bottom: 1px solid rgba(51, 65, 85, 0.5);
  font-size: 12px;
}

.search-results li:hover {
  background: rgba(var(--alp-color-primary-rgb), 0.1);
}

.hit-kind {
  font-size: 10px;
  color: #64748b;
  margin-right: 6px;
}

.hit-snippet {
  display: block;
  color: #94a3b8;
  margin-top: 2px;
}

.tour-panel {
  position: absolute;
  right: 12px;
  top: 52px;
  width: min(280px, 42vw);
  z-index: 5;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.94);
  border: 1px solid var(--alp-color-primary-glow);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.tour-panel h4 {
  margin: 8px 0 4px;
  font-size: 14px;
  color: #e2e8f0;
}

.tour-panel p {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  color: #94a3b8;
}

.tour-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: #64748b;
}

.tour-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.tour-encourage {
  margin-top: 6px !important;
  color: #9c8540 !important;
}

.impact-ripple,
.impact-diff {
  position: absolute;
  bottom: 48px;
  left: 12px;
  right: 12px;
  z-index: 4;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  font-size: 11px;
  color: #fca5a5;
}

.impact-label {
  color: #94a3b8;
}

.drawer-concepts,
.drawer-problems {
  margin-top: 10px;
}

.drawer-concepts-label {
  display: block;
  font-size: 11px;
  color: var(--alp-color-muted);
  margin-bottom: 6px;
}

.concept-chip {
  margin: 0 6px 6px 0;
  cursor: pointer;
}

/* ===== 直达学习页 CTA 按钮 ===== */
.drawer-cta {
  margin-top: 12px;
}

.cta-learn-btn {
  width: 100%;
  font-weight: 600;
}

/* ===== 算法详细信息卡片 ===== */
.drawer-info-card {
  margin: 16px 0;
  padding: 14px 16px;
  border-radius: 10px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.info-meta-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin: 10px 0 12px;
  font-size: 12px;
  color: var(--alp-color-text-secondary);
}

.info-meta-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.info-meta-item :deep(.el-icon) {
  font-size: 14px;
  color: var(--alp-color-primary);
}

.info-summary {
  margin: 0 0 12px;
  font-size: 13px;
  line-height: 1.65;
  color: var(--alp-color-text);
}

.info-goals {
  margin-bottom: 4px;
}

.info-goals-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-text);
  margin-bottom: 6px;
}

.info-goals-list {
  margin: 0;
  padding-left: 18px;
  font-size: 12.5px;
  line-height: 1.7;
  color: var(--alp-color-text-secondary);
}

.info-goals-list li {
  list-style: disc;
}

/* ===== AI 智能解释卡片（对齐 OJ 助教双卡风格） ===== */
.drawer-ai-card {
  margin: 16px 0;
  padding: 14px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-aside-gradient);
  border: 1px solid var(--alp-color-border);
  box-shadow: var(--alp-shadow-card);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ai-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.ai-card-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.ai-card-title :deep(.el-icon) {
  font-size: 18px;
  color: var(--alp-color-accent);
}

.ai-stream-badge {
  font-size: 12px;
  color: var(--el-color-primary);
  background: color-mix(in srgb, var(--el-color-primary) 14%, transparent);
  padding: 2px 8px;
  border-radius: 10px;
  animation: ai-stream-pulse 1.2s ease-in-out infinite;
}

@keyframes ai-stream-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.ai-card-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ai-card-desc {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--alp-color-muted);
}

.ai-card-body {
  flex: 1;
  min-height: 120px;
  overflow-y: auto;
  border-radius: 8px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  padding: 10px 12px;
  scrollbar-width: thin;
}

.ai-card-reply {
  font-size: 13px;
  line-height: 1.6;
  color: var(--alp-color-text);
}

.ai-card-reply :deep(.ai-md-h) {
  font-size: 0.92em;
  margin: 0.75em 0 0.35em;
  color: var(--alp-color-primary);
}

.ai-card-reply :deep(.ai-md-p) {
  margin: 0 0 0.5em;
  font-size: 13px;
  line-height: 1.6;
}

.ai-card-reply :deep(.ai-md-ul),
.ai-card-reply :deep(.ai-md-ol) {
  margin: 0.35em 0 0.5em;
  padding-left: 1.15em;
  font-size: 13px;
  line-height: 1.55;
}

.ai-card-reply :deep(.ai-md-code) {
  font-size: 0.88em;
  padding: 0.1em 0.35em;
  font-family: ui-monospace, Consolas, monospace;
  background: var(--alp-bg-code-ish);
  border-radius: 4px;
  color: #6a9eb0;
}

/* 模糊遮罩 + 占位预览 */
.ai-card-body.is-blurred {
  position: relative;
  overflow: hidden;
  padding: 0;
  border-color: transparent;
  background: transparent;
}

.ai-blur-preview {
  padding: 14px 16px;
  font-size: 13px;
  line-height: 1.65;
  color: var(--alp-color-text);
  filter: blur(5px);
  user-select: none;
  pointer-events: none;
  opacity: 0.85;
}

.ai-blur-preview .ai-md-h {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--alp-color-primary);
}

.ai-blur-preview .ai-md-p {
  margin: 0 0 8px;
}

.ai-blur-preview .ai-md-ul {
  margin: 4px 0 8px;
  padding-left: 1.25em;
}

.ai-blur-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 18px;
  text-align: center;
  background: color-mix(in srgb, var(--alp-bg-surface) 78%, transparent);
  backdrop-filter: blur(2px);
  -webkit-backdrop-filter: blur(2px);
  cursor: pointer;
  transition: background 0.2s ease;
  z-index: 2;
}

.ai-blur-overlay:hover {
  background: color-mix(in srgb, var(--alp-color-primary) 12%, transparent);
}

.ai-blur-icon {
  font-size: 26px;
  color: var(--alp-color-primary);
}

.ai-blur-tip {
  font-size: 14px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.ai-blur-sub {
  font-size: 12px;
  color: var(--alp-color-muted);
  line-height: 1.5;
  max-width: 26em;
}

/* 流式输出区域 */
.ai-stream-area {
  flex: 1;
  min-height: 120px;
  overflow-y: auto;
  border-radius: 8px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  padding: 10px 12px;
  scrollbar-width: thin;
}

.ai-stream-text {
  font-size: 13px;
  line-height: 1.65;
  color: var(--alp-color-text);
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
}

.ai-stream-cursor {
  display: inline-block;
  width: 7px;
  height: 14px;
  margin-left: 1px;
  vertical-align: text-bottom;
  background: var(--alp-color-primary);
  animation: ai-cursor-blink 1s steps(2) infinite;
}

@keyframes ai-cursor-blink {
  0%, 50% { opacity: 1; }
  50.01%, 100% { opacity: 0; }
}

.drawer-content {
  display: flex;
  flex-direction: column;
  min-width: 0;
  color: var(--alp-color-text);
}

.drawer-titlebar {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
  color: var(--alp-color-text);
}

.drawer-titlebar strong {
  overflow: hidden;
  font-size: 17px;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.drawer-title-kicker {
  color: var(--alp-color-primary);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
}

.drawer-section-title--ai {
  margin-top: 20px;
}

.drawer-content :deep(.ai-tutor-card) {
  max-height: none;
}

.drawer-content :deep(.ai-tutor-messages) {
  min-height: 160px;
  max-height: 320px;
}
</style>

<style>
.universe-drawer.el-drawer {
  height: 100%;
  max-height: 100vh;
  box-sizing: border-box;
  background: var(--alp-bg-surface);
}

.universe-drawer .el-drawer__header {
  margin-bottom: 0;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--alp-color-border);
}

.universe-drawer .el-drawer__body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 18px 20px 24px;
  background: var(--alp-bg-surface);
  color: var(--alp-color-text);
}

.universe-drawer .el-drawer__footer {
  border-top: 1px solid var(--alp-color-border);
}

.universe-drawer-overlay.el-overlay {
  position: fixed;
  inset: 0;
  height: 100vh;
}
</style>
