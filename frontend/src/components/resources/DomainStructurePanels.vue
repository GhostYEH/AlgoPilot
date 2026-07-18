<script setup lang="ts">
import DomainFlowGraph from '@/components/resources/DomainFlowGraph.vue'
import CodeEditor from '@/components/oj/CodeEditor.vue'
import {
  parseDomainStructureContent,
  renderDomainStoryHtml,
  renderStructureOutlineHtml,
  type DomainStructurePayload,
} from '@/utils/domainStructureContent'

const props = withDefaults(
  defineProps<{
    content: string
    mode?: 'document' | 'scenario'
    editableCode?: boolean
  }>(),
  {
    mode: 'document',
    editableCode: false,
  },
)

const emit = defineEmits<{
  'update:code': [value: string]
}>()

const payload = computed((): DomainStructurePayload | null =>
  parseDomainStructureContent(props.content),
)

const domain = computed(() => payload.value?.domain_narrative ?? null)
const structure = computed(() => payload.value?.structure_logic ?? null)

const storyHtml = computed(() => (domain.value ? renderDomainStoryHtml(domain.value) : ''))

const structureHtml = computed(() =>
  structure.value ? renderStructureOutlineHtml(structure.value) : '',
)

const originalCode = computed(() => structure.value?.code_framework ?? '')
const codeModel = ref('')

watch(
  originalCode,
  (value) => {
    codeModel.value = value
  },
  { immediate: true },
)

watch(codeModel, (value) => emit('update:code', value))

function resetCode() {
  codeModel.value = originalCode.value
}

const dataStructures = computed(() => structure.value?.data_structures ?? [])
const objectives = computed(() => structure.value?.learning_objectives ?? [])
const pitfalls = computed(() => structure.value?.pitfalls ?? [])
const stepHints = computed(() => structure.value?.step_hints ?? [])
</script>

<template>
  <div v-if="payload" class="ds-panels">
    <section class="ds-panel ds-panel--domain">
      <header class="ds-panel-head">
        <span class="ds-panel-icon">📜</span>
        <h4>业务场景故事</h4>
        <span class="ds-panel-tag">Domain · 零代码叙事</span>
      </header>
      <div
        v-if="domain?.illustration_hint"
        class="ds-illustration"
        role="img"
        :aria-label="domain.illustration_hint"
      >
        <span class="ds-illustration-glow" />
        <p class="ds-illustration-caption">{{ domain.illustration_hint }}</p>
      </div>
      <div v-if="storyHtml" class="ds-story ai-md-body" v-html="storyHtml" />
      <DomainFlowGraph :domain="domain" :structure="structure" />
    </section>

    <section class="ds-panel ds-panel--structure">
      <header class="ds-panel-head">
        <span class="ds-panel-icon">⚙️</span>
        <h4>底层结构剖析</h4>
        <span class="ds-panel-tag ds-panel-tag--geek">Structure · CS 学术域</span>
      </header>

      <ul v-if="objectives.length && mode === 'document'" class="ds-objectives">
        <li v-for="(o, i) in objectives" :key="i">{{ o }}</li>
      </ul>

      <div v-if="structureHtml" class="ds-structure-body ai-md-body" v-html="structureHtml" />
      <DomainFlowGraph :structure="structure" />

      <div v-if="dataStructures.length" class="ds-ds-block">
        <span class="ds-label">数据结构</span>
        <div class="ds-chips">
          <span v-for="(ds, i) in dataStructures" :key="i" class="ds-chip">{{ ds }}</span>
        </div>
      </div>

      <div v-if="structure?.time_complexity || structure?.space_complexity" class="ds-complexity">
        <div v-if="structure?.time_complexity" class="ds-complexity-item">
          <span class="ds-label">时间复杂度</span>
          <code>{{ structure.time_complexity }}</code>
        </div>
        <div v-if="structure?.space_complexity" class="ds-complexity-item">
          <span class="ds-label">空间复杂度</span>
          <code>{{ structure.space_complexity }}</code>
        </div>
      </div>

      <div v-if="structure?.correctness_proof" class="ds-proof">
        <span class="ds-label">论证要点</span>
        <p>{{ structure.correctness_proof }}</p>
      </div>

      <ul v-if="pitfalls.length" class="ds-pitfalls">
        <li v-for="(p, i) in pitfalls" :key="i">{{ p }}</li>
      </ul>

      <div v-if="mode === 'scenario' && (codeModel || stepHints.length)" class="ds-sandbox">
        <div class="ds-sandbox-head">
          <h5 class="ds-sandbox-title">代码框架 · 补全 TODO</h5>
          <el-button v-if="editableCode" size="small" plain @click="resetCode">恢复初始代码</el-button>
        </div>
        <CodeEditor
          v-if="editableCode"
          v-model="codeModel"
          language="python"
          :readonly="false"
          min-height="260px"
        />
        <pre v-else-if="codeModel" class="ds-code-readonly">{{ codeModel }}</pre>
        <ul v-if="stepHints.length" class="ds-hints">
          <li v-for="(h, i) in stepHints" :key="i">{{ i + 1 }}. {{ h }}</li>
        </ul>
      </div>
    </section>
  </div>
</template>

<style scoped>
.ds-panels {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ds-panel {
  border-radius: 14px;
  padding: 18px 20px;
  border: 1px solid var(--alp-color-border);
}

.ds-panel--domain {
  background: color-mix(in srgb, var(--alp-color-accent) 12%, var(--alp-bg-surface));
  border-color: color-mix(in srgb, var(--alp-color-accent) 35%, var(--alp-color-border));
}

.ds-panel--structure {
  background: #0f172a;
  border-color: color-mix(in srgb, var(--alp-color-primary) 30%, #334155);
  color: #e2e8f0;
  font-family: ui-monospace, 'Cascadia Code', Consolas, monospace;
}

.ds-panel--structure .ds-label,
.ds-panel--structure h4,
.ds-panel--structure h5,
.ds-panel--structure p,
.ds-panel--structure li {
  color: #e2e8f0;
}

.ds-panel-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.ds-panel-head h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  flex: 1;
}

.ds-panel-icon {
  font-size: 1.2rem;
}

.ds-panel-tag {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--alp-color-accent) 20%, transparent);
  color: var(--alp-color-primary);
  letter-spacing: 0.04em;
}

.ds-panel-tag--geek {
  background: color-mix(in srgb, var(--alp-color-primary) 18%, transparent);
  color: #6a9eb0;
}

.ds-illustration {
  position: relative;
  min-height: 100px;
  margin-bottom: 14px;
  border-radius: 12px;
  overflow: hidden;
  background:
    rgba(74, 126, 148, 0.25),
    rgba(var(--alp-color-accent-rgb), 0.2),
    #0f172a;
  display: flex;
  align-items: flex-end;
  padding: 14px 16px;
}

.ds-illustration-glow {
  position: absolute;
  inset: 0;
  background: transparent;
  pointer-events: none;
}

.ds-illustration-caption {
  position: relative;
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: #cbd5e1;
  font-style: italic;
}

.ds-story {
  line-height: 1.75;
  font-size: 14px;
}

.ds-structure-body {
  font-size: 13px;
  line-height: 1.65;
  margin-bottom: 14px;
}

.ds-structure-body :deep(p) {
  color: #cbd5e1;
}

.ds-label {
  display: block;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #64748b;
  margin-bottom: 6px;
}

.ds-objectives {
  margin: 0 0 12px;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.6;
}

.ds-ds-block {
  margin-bottom: 12px;
}

.ds-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ds-chip {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  background: var(--alp-color-primary-soft);
  border: 1px solid var(--alp-color-primary-glow);
  color: #6a9eb0;
}

.ds-complexity {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.ds-complexity code {
  display: block;
  font-size: 12px;
  color: #6aa878;
  background: var(--alp-bg-surface);
  padding: 6px 8px;
  border-radius: 6px;
  border: 1px solid #334155;
}

.ds-proof {
  margin-bottom: 12px;
  font-size: 12px;
  line-height: 1.6;
  color: #94a3b8;
}

.ds-pitfalls {
  margin: 0 0 12px;
  padding-left: 18px;
  font-size: 12px;
  color: #9c8540;
}

.ds-sandbox {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px dashed #334155;
}

.ds-sandbox-title {
  margin: 0;
  font-size: 13px;
  color: var(--alp-color-primary);
}

.ds-sandbox-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.ds-code-readonly {
  margin: 0;
  padding: 12px;
  border-radius: 8px;
  background: #020617;
  border: 1px solid #334155;
  font-size: 12px;
  overflow: auto;
  max-height: 320px;
}

.ds-hints {
  margin: 12px 0 0;
  padding-left: 18px;
  font-size: 12px;
  color: #94a3b8;
}
</style>
