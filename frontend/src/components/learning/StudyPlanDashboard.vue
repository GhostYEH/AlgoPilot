<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowRight, Calendar, Check, Download, Document, EditPen, Files,
  VideoPlay, Trophy, UserFilled,
} from '@element-plus/icons-vue'
import LearningDimensionRadar from './LearningDimensionRadar.vue'
import { ALGORITHM_MODULES, MODULE_ROUTE_NAMES } from '@/constants/modules'
import { buildLearningOverview } from '@/utils/learningOverview'

const router = useRouter()
const overview = computed(() => buildLearningOverview())
const expandedPhase = ref(1)

const radarDimensions = computed(() => [
  { key: 'structure', label: '数据结构', score: Math.max(58, overview.value.overallPercent) },
  { key: 'design', label: '算法设计', score: 60 },
  { key: 'dp', label: '动态规划', score: 55 },
  { key: 'graph', label: '图论', score: 48 },
  { key: 'math', label: '数学基础', score: 65 },
  { key: 'code', label: '编程能力', score: 80 },
])

const phases = [
  { title: '基础巩固阶段', weeks: '第1–2周', status: '进行中', goal: '巩固基础数据结构与常用算法思想，提升代码实现能力。', topics: ['数组与链表', '栈与队列', '二分查找', '排序算法'] },
  { title: '专项提升阶段', weeks: '第3–4周', status: '未开始', goal: '掌握动态规划与图论的核心方法，解决中等难度问题。', topics: ['动态规划入门', '背包问题', '最短路', '最小生成树'] },
  { title: '综合应用阶段', weeks: '第5周', status: '未开始', goal: '综合运用所学知识解决复杂问题，提升算法设计能力。', topics: ['贪心算法', '搜索与回溯', '区间问题', '经典综合题'] },
  { title: '冲刺强化阶段', weeks: '第6周', status: '未开始', goal: '通过高强度训练提升解题速度与准确率，适应比赛节奏。', topics: ['高频考点复习', '模拟比赛', '错题复盘', '策略优化'] },
]

const resources = [
  { icon: Document, tone: 'blue', name: '动态规划入门讲义（定制版）', meta: 'PDF · 1.2 MB', action: '下载' },
  { icon: EditPen, tone: 'green', name: '背包问题专题笔记', meta: 'Markdown · 8.6 KB', action: '下载' },
  { icon: VideoPlay, tone: 'orange', name: '图论最短路可视化讲解', meta: 'MP4 · 24.5 MB', action: '观看' },
  { icon: Files, tone: 'blue', name: '算法模板代码库（C++）', meta: 'ZIP · 48.3 KB', action: '下载' },
]

const practices = [
  { name: '背包问题（01背包）', source: '洛谷 P1048', match: 92, key: 'dp' },
  { name: '最小路径和', source: '力扣 64', match: 88, key: 'dp' },
  { name: '最短路（Dijkstra）', source: '洛谷 P3371', match: 85, key: 'graph' },
  { name: '区间合并', source: '力扣 56', match: 80, key: 'greedy' },
]

function openModule(key: string) {
  const name = MODULE_ROUTE_NAMES[key]
  if (name) void router.push({ name })
}
</script>

<template>
  <section class="plan-dashboard" aria-label="个性化学习路径规划">
    <header class="plan-toolbar">
      <div>
        <p class="toolbar-kicker">学习规划</p>
        <h1>个性化路径规划</h1>
      </div>
      <div class="plan-period"><el-icon><Calendar /></el-icon><span>学习计划：6 周</span><button type="button">2026-07-13 至 2026-08-23</button></div>
    </header>

    <div class="dashboard-columns">
      <aside class="profile-column">
        <div class="profile-summary">
          <div class="avatar"><el-icon><UserFilled /></el-icon></div>
          <div><h2>学习者</h2><span class="level-tag">进阶阶段</span><p>当前总进度 {{ overview.overallPercent }}%</p></div>
        </div>
        <dl class="profile-meta"><div><dt>算法基础</dt><dd>中等</dd></div><div><dt>学习目标</dt><dd>提升算法能力，备战竞赛</dd></div></dl>
        <div class="section-rule" />
        <div class="subhead"><h3>能力画像</h3><span>动态更新</span></div>
        <LearningDimensionRadar :dimensions="radarDimensions" />
        <div class="radar-legend"><span><i class="current" />当前水平</span><span><i class="target" />目标水平</span></div>
        <div class="insight"><strong>能力解读</strong><p>你的编程能力较强，但在图论和动态规划方面相对薄弱，建议在接下来的学习中加强练习，逐步提升综合算法能力。</p></div>
      </aside>

      <main class="path-column">
        <div class="column-head"><h2>个性化学习路径</h2><div><span>总计划时长：6周</span><button type="button"><el-icon><EditPen /></el-icon>调整计划</button></div></div>
        <div class="phase-list">
          <article v-for="(phase, index) in phases" :key="phase.title" class="phase-item" :class="{ active: expandedPhase === index }" @click="expandedPhase = index">
            <div class="phase-marker">{{ index + 1 }}</div>
            <div class="phase-card">
              <div class="phase-title"><h3>{{ phase.title }} <small>（{{ phase.weeks }}）</small></h3><span :class="{ running: index === 0 }">{{ phase.status }}</span></div>
              <div v-show="expandedPhase === index || index === 0" class="phase-details"><strong>阶段目标</strong><p>{{ phase.goal }}</p><strong>核心内容</strong><div class="topic-list"><button v-for="(topic, i) in phase.topics" :key="topic" type="button" @click.stop="openModule(ALGORITHM_MODULES[(index * 3 + i) % ALGORITHM_MODULES.length].key)">{{ topic }}</button></div></div>
            </div>
          </article>
        </div>
        <p class="path-note">根据你的学习进度和效果，路径将智能调整。</p>
      </main>

      <aside class="support-column">
        <section class="support-section"><div class="column-head"><h2>资源生成</h2><button type="button">查看更多 <el-icon><ArrowRight /></el-icon></button></div><div class="resource-list"><article v-for="item in resources" :key="item.name"><div class="resource-icon" :class="item.tone"><el-icon><component :is="item.icon" /></el-icon></div><div><strong>{{ item.name }}</strong><span>{{ item.meta }}</span></div><button type="button"><el-icon><Download v-if="item.action === '下载'" /></el-icon>{{ item.action }}</button></article></div></section>
        <section class="support-section"><div class="column-head"><h2>练习建议</h2><button type="button">查看更多 <el-icon><ArrowRight /></el-icon></button></div><div class="practice-list"><button v-for="(item, index) in practices" :key="item.name" type="button" @click="openModule(item.key)"><b>{{ String(index + 1).padStart(2, '0') }}</b><span><strong>{{ item.name }}</strong><small>{{ item.source }}</small></span><em>匹配度 {{ item.match }}%</em></button></div></section>
        <section class="reason"><div class="reason-title"><el-icon><Trophy /></el-icon><h2>推荐理由</h2></div><p>基于你的能力画像、学习目标和历史表现，推荐以上内容：</p><ul><li><el-icon><Check /></el-icon>动态规划能力得分偏低，需要系统性强化训练</li><li><el-icon><Check /></el-icon>当前阶段内容与目标匹配度高，适合短期提升</li><li><el-icon><Check /></el-icon>题目覆盖核心考点，难度梯度合理</li></ul></section>
      </aside>
    </div>
  </section>
</template>

<style scoped>
.plan-dashboard{margin:-1px -1px 24px;background:var(--alp-bg-surface-solid);border:1px solid var(--alp-color-border);color:var(--alp-color-text)}
.plan-toolbar{min-height:68px;padding:12px 20px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--alp-color-border)}
.toolbar-kicker{margin:0 0 2px;color:var(--alp-color-primary);font-size:12px}.plan-toolbar h1{margin:0;font-size:20px;letter-spacing:-.02em}.plan-period{display:flex;align-items:center;gap:8px;font-size:13px}.plan-period button,.column-head button{border:0;background:transparent;color:var(--alp-color-primary);cursor:pointer;font:inherit}.dashboard-columns{display:grid;grid-template-columns:minmax(260px,30%) minmax(430px,1fr) minmax(330px,38%)}
.profile-column,.path-column,.support-column{min-width:0}.profile-column,.path-column{padding:24px;border-right:1px solid var(--alp-color-border)}.support-column{padding:0}.profile-summary{display:flex;gap:14px;align-items:center}.avatar{width:72px;height:72px;border-radius:50%;display:grid;place-items:center;background:var(--alp-bg-soft-block);color:var(--alp-color-primary);font-size:34px}.profile-summary h2{margin:0 0 6px;font-size:18px}.profile-summary p{margin:7px 0 0;font-size:12px;color:var(--alp-color-muted)}.level-tag{padding:3px 8px;border-radius:4px;background:var(--alp-color-primary-soft);color:var(--alp-color-primary);font-size:12px}.profile-meta{margin:20px 0;display:grid;gap:10px;font-size:13px}.profile-meta div{display:flex}.profile-meta dt{width:76px;color:var(--alp-color-muted)}.profile-meta dd{margin:0}.section-rule{border-top:1px solid var(--alp-color-border);margin:22px 0}.subhead,.column-head{display:flex;align-items:center;justify-content:space-between;gap:12px}.subhead h3,.column-head h2{margin:0;font-size:16px}.subhead span,.column-head span{font-size:12px;color:var(--alp-color-muted)}.radar-legend{display:flex;justify-content:center;gap:24px;font-size:12px;color:var(--alp-color-muted)}.radar-legend i{display:inline-block;width:18px;margin-right:6px;border-top:2px solid var(--alp-color-primary);vertical-align:middle}.radar-legend .target{border-top-style:dashed;border-color:#94a3b8}.insight{margin-top:24px;padding:14px;background:var(--alp-bg-soft-block);border-radius:8px;font-size:13px}.insight p{margin:8px 0 0;line-height:1.75;color:var(--alp-color-text-secondary)}
.column-head>div{display:flex;align-items:center;gap:12px}.phase-list{margin-top:20px}.phase-item{position:relative;display:grid;grid-template-columns:34px 1fr;gap:12px;padding-bottom:16px;cursor:pointer}.phase-item:not(:last-child)::before{content:"";position:absolute;left:16px;top:34px;bottom:-2px;width:1px;background:var(--alp-color-border-strong)}.phase-marker{width:32px;height:32px;border-radius:50%;display:grid;place-items:center;background:#8793a0;color:#fff;font-size:13px;z-index:1}.phase-item.active .phase-marker{background:var(--alp-color-primary)}.phase-card{border:1px solid var(--alp-color-border);border-radius:7px;padding:14px;background:var(--alp-bg-surface)}.phase-title{display:flex;justify-content:space-between;gap:12px}.phase-title h3{margin:0;font-size:15px}.phase-title small{font-weight:400;color:var(--alp-color-muted)}.phase-title span{padding:3px 7px;border-radius:4px;background:var(--alp-bg-soft-block);font-size:11px;color:var(--alp-color-muted)}.phase-title .running{color:var(--alp-color-primary);background:var(--alp-color-primary-soft)}.phase-details{margin-top:16px;font-size:12px}.phase-details p{margin:6px 0 14px;color:var(--alp-color-text-secondary);line-height:1.6}.topic-list{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}.topic-list button{border:1px solid var(--alp-color-border);border-radius:5px;background:var(--alp-bg-soft-block);color:var(--alp-color-text-secondary);padding:5px 9px;cursor:pointer}.topic-list button:hover{border-color:var(--alp-color-primary);color:var(--alp-color-primary)}.path-note{margin:0 0 0 46px;color:var(--alp-color-muted);font-size:12px}
.support-section{padding:20px;border-bottom:1px solid var(--alp-color-border)}.resource-list{margin-top:14px;border:1px solid var(--alp-color-border);border-radius:7px;overflow:hidden}.resource-list article{display:grid;grid-template-columns:36px 1fr auto;gap:10px;align-items:center;padding:11px;border-bottom:1px solid var(--alp-color-border)}.resource-list article:last-child{border-bottom:0}.resource-icon{width:32px;height:38px;border-radius:4px;display:grid;place-items:center;color:#fff;background:#3b82f6}.resource-icon.green{background:#20a568}.resource-icon.orange{background:#f08a24}.resource-list strong{display:block;font-size:12px}.resource-list span{display:block;margin-top:4px;font-size:11px;color:var(--alp-color-muted)}.resource-list article>button{padding:6px 10px;border:1px solid var(--alp-color-border);border-radius:5px;background:transparent;color:var(--alp-color-primary);cursor:pointer}.practice-list{margin-top:14px;border:1px solid var(--alp-color-border);border-radius:7px;overflow:hidden}.practice-list>button{width:100%;display:grid;grid-template-columns:24px 1fr auto;gap:8px;align-items:center;padding:10px;border:0;border-bottom:1px solid var(--alp-color-border);background:transparent;color:inherit;text-align:left;cursor:pointer}.practice-list>button:last-child{border-bottom:0}.practice-list>button:hover{background:var(--alp-bg-soft-block)}.practice-list span strong,.practice-list span small{display:block;font-size:12px}.practice-list span small{margin-top:4px;color:var(--alp-color-muted)}.practice-list em{font-style:normal;font-size:11px;padding:5px 7px;border-radius:4px;background:var(--alp-color-primary-soft);color:var(--alp-color-primary)}.reason{margin:16px 20px 20px;padding:14px;border:1px solid var(--alp-color-border);border-radius:7px}.reason-title{display:flex;gap:8px;align-items:center}.reason-title h2{margin:0;font-size:15px}.reason-title .el-icon{color:var(--alp-color-primary)}.reason p,.reason li{font-size:12px;line-height:1.6;color:var(--alp-color-text-secondary)}.reason ul{padding:0;margin:8px 0 0;list-style:none}.reason li{display:flex;gap:6px;margin:5px 0}.reason li .el-icon{color:var(--alp-color-primary);margin-top:3px;flex:none}
@media(max-width:1250px){.dashboard-columns{grid-template-columns:300px 1fr}.support-column{grid-column:1/-1;display:grid;grid-template-columns:1fr 1fr}.support-column .reason{grid-column:1/-1}.path-column{border-right:0}.profile-column{border-right:1px solid var(--alp-color-border)}}
@media(max-width:780px){.plan-toolbar{align-items:flex-start;gap:14px;flex-direction:column}.plan-period{flex-wrap:wrap}.dashboard-columns{display:block}.profile-column,.path-column{padding:18px;border-right:0;border-bottom:1px solid var(--alp-color-border)}.support-column{display:block}.phase-item{grid-template-columns:30px 1fr}.support-section{padding:18px}.practice-list em{display:none}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
</style>
