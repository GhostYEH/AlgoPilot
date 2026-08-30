<script setup lang="ts">
import { Collection, DataAnalysis, MagicStick, Search, UserFilled } from '@element-plus/icons-vue'

withDefaults(defineProps<{ moduleLabel: string; serviceReady?: boolean }>(), { serviceReady: false })
const emit = defineEmits<{ openWorkbench: []; openResources: [] }>()

const phases = [
  { index: '1', label: '学习上下文', agent: 'ProfilingAgent', detail: '学习画像分析', icon: UserFilled, state: 'ready' },
  { index: '2', label: '知识检索', agent: 'KnowledgeAgent', detail: '课程知识检索', icon: Search, state: 'ready' },
  { index: '3', label: '生成资源', agent: 'Generation Agents', detail: '讲解、图谱与练习', icon: MagicStick, state: 'active' },
  { index: '4', label: '校验回流', agent: 'VerifierAgent', detail: '内容依据校验', icon: Collection, state: 'waiting' },
  { index: '5', label: '效果评估', agent: 'EvaluationAgent', detail: '学习效果评估', icon: DataAnalysis, state: 'waiting' },
]
</script>

<template>
  <section class="home-ai" aria-labelledby="home-ai-title">
    <header class="home-ai__head">
      <div><h2 id="home-ai-title">AI 资源生成中心</h2><p>围绕「{{ moduleLabel }}」组织学习上下文、课程知识与可校验资源。</p></div>
      <button type="button" @click="emit('openResources')">资源库 <span aria-hidden="true">›</span></button>
    </header>

    <div class="home-ai__track">
      <article v-for="(phase, index) in phases" :key="phase.index" :class="`is-${phase.state}`">
        <header><span>{{ phase.index }}</span><strong>{{ phase.label }}</strong><small>{{ phase.state === 'ready' ? '已就绪' : phase.state === 'active' ? '可启动' : '等待中' }}</small></header>
        <div><span class="home-ai__icon"><el-icon><component :is="phase.icon" /></el-icon></span><p><strong>{{ phase.agent }}</strong><small>{{ phase.detail }}</small></p></div>
        <span v-if="index < phases.length - 1" class="home-ai__arrow" aria-hidden="true">→</span>
      </article>
    </div>

    <footer>
      <div class="home-ai__progress"><span>流程准备度</span><div><i :style="{ width: serviceReady ? '40%' : '20%' }" /></div><small>{{ serviceReady ? '2 / 5 个阶段就绪' : '本地学习上下文可用' }}</small></div>
      <button type="button" @click="emit('openWorkbench')">打开生成中心</button>
    </footer>
  </section>
</template>

<style scoped>
.home-ai { margin-top: 16px; padding: 20px 22px 18px; border: 1px solid var(--color-border); border-radius: 14px; background: var(--color-bg-surface); box-shadow: 0 8px 26px rgba(27,80,81,.035); }
.home-ai__head { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; }
.home-ai__head h2 { margin: 0; color: #102b31; font-size: 18px; }
.home-ai__head p { margin: 5px 0 0; color: var(--color-text-muted); font-size: 11px; }
.home-ai__head button { padding: 7px 10px; color: var(--color-brand); font: inherit; font-size: 11px; font-weight: 700; border: 1px solid #bedfdd; border-radius: 8px; background: transparent; cursor: pointer; }
.home-ai__track { display: grid; grid-template-columns: .86fr .86fr 1.08fr .86fr .86fr; gap: 20px; margin-top: 18px; }
.home-ai__track article { position: relative; min-width: 0; min-height: 126px; padding: 13px; border: 1px solid var(--color-border); border-radius: 11px; background: linear-gradient(180deg,#fff,#f5faf9); }
.home-ai__track article.is-active { border-color: #68c5c0; box-shadow: 0 0 0 2px rgba(35,157,157,.06); }
.home-ai__track article > header { display: grid; grid-template-columns: 22px minmax(0,1fr) auto; align-items: center; gap: 7px; }
.home-ai__track article > header > span { display: grid; width: 21px; height: 21px; place-items: center; color: var(--color-brand); font-size: 10px; font-weight: 800; border-radius: 7px; background: #e7f7f5; }
.home-ai__track article > header strong { overflow: hidden; font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.home-ai__track article > header small { color: #36a96f; font-size: 9px; }
.home-ai__track article.is-active > header small { color: #258cd7; } .home-ai__track article.is-waiting > header small { color: var(--color-text-muted); }
.home-ai__track article > div { display: grid; grid-template-columns: 28px minmax(0,1fr); align-items: center; gap: 9px; margin-top: 22px; padding: 11px 9px; border: 1px solid #e4eeee; border-radius: 8px; background: #fff; }
.home-ai__icon { display: grid; width: 26px; height: 26px; place-items: center; color: var(--color-brand); border-radius: 50%; background: #e9f7f6; }
.home-ai__track p { display: flex; min-width: 0; flex-direction: column; margin: 0; }
.home-ai__track p strong,.home-ai__track p small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; } .home-ai__track p strong { font-size: 10px; } .home-ai__track p small { margin-top: 3px; color: var(--color-text-muted); font-size: 9px; }
.home-ai__arrow { position: absolute; top: 50%; right: -17px; z-index: 2; color: var(--color-brand); font-size: 16px; font-weight: 800; transform: translateY(-50%); }
.home-ai > footer { display: grid; grid-template-columns: minmax(0,1fr) auto; align-items: end; gap: 24px; margin-top: 16px; padding: 14px 16px; border-radius: 10px; background: #f2f8f7; }
.home-ai__progress { display: grid; grid-template-columns: auto minmax(180px,1fr) auto; align-items: center; gap: 11px; }
.home-ai__progress > span,.home-ai__progress > small { color: var(--color-text-muted); font-size: 10px; white-space: nowrap; }
.home-ai__progress > div { height: 5px; overflow: hidden; border-radius: 99px; background: #dce9e8; } .home-ai__progress i { display: block; height: 100%; border-radius: inherit; background: var(--color-brand); }
.home-ai > footer > button { min-height: 36px; padding: 0 15px; color: #fff; font: inherit; font-size: 11px; font-weight: 700; border: 0; border-radius: 8px; background: var(--color-brand); cursor: pointer; }
.home-ai button:hover { filter: brightness(.97); }
@media (max-width: 1020px) { .home-ai__track { grid-template-columns: repeat(5,minmax(170px,1fr)); overflow-x: auto; padding-bottom: 8px; } }
@media (max-width: 620px) { .home-ai { padding-inline: 14px; } .home-ai__head { align-items: flex-start; } .home-ai__track { margin-top: 14px; } .home-ai > footer { grid-template-columns: 1fr; } .home-ai__progress { grid-template-columns: auto 1fr; } .home-ai__progress > small { grid-column: 1/-1; } .home-ai > footer > button { width: 100%; } }
</style>
