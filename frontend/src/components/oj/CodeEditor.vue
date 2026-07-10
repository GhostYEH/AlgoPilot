<script setup lang="ts">
import { computed, shallowRef, watch } from 'vue'
import { Codemirror } from 'vue-codemirror'
import { python } from '@codemirror/lang-python'
import { cpp } from '@codemirror/lang-cpp'
import { oneDark } from '@codemirror/theme-one-dark'
import { EditorView, Decoration } from '@codemirror/view'
import { StateEffect, StateField } from '@codemirror/state'

const model = defineModel<string>({ required: true })

const props = withDefaults(
  defineProps<{
    readonly?: boolean
    minHeight?: string
    language?: 'python' | 'cpp'
    fontSize?: string
    /** 可视化调试：当前执行行（1-based） */
    highlightLine?: number
  }>(),
  {
    readonly: false,
    minHeight: '360px',
    language: 'python',
    fontSize: '14px',
    highlightLine: 0,
  },
)

const traceLineEffect = StateEffect.define<number>()

const traceLineField = StateField.define({
  create() {
    return Decoration.none
  },
  update(deco, tr) {
    deco = deco.map(tr.changes)
    for (const e of tr.effects) {
      if (!e.is(traceLineEffect)) continue
      const lineNo = e.value
      if (lineNo < 1) return Decoration.none
      const line = tr.state.doc.line(Math.min(lineNo, tr.state.doc.lines))
      return Decoration.set([
        Decoration.line({ class: 'cm-trace-current-line' }).range(line.from),
      ])
    }
    return deco
  },
  provide: (f) => EditorView.decorations.from(f),
})

const langExt = computed(() => {
  const base = [
    oneDark,
    EditorView.lineWrapping,
    EditorView.editable.of(!props.readonly),
    traceLineField,
  ]
  if (props.language === 'cpp') {
    return [...base, cpp()]
  }
  return [...base, python()]
})

const view = shallowRef<EditorView>()

function onEditorReady(payload: { view: EditorView }) {
  view.value = payload.view
  applyHighlight(payload.view, props.highlightLine)
}

function applyHighlight(ed: EditorView, lineNo: number) {
  ed.dispatch({ effects: traceLineEffect.of(lineNo) })
  if (lineNo < 1) return
  const line = ed.state.doc.line(Math.min(lineNo, ed.state.doc.lines))
  ed.dispatch({
    effects: EditorView.scrollIntoView(line.from, { y: 'center' }),
  })
}

watch(
  () => props.fontSize,
  (size) => {
    if (view.value) {
      view.value.dom.style.fontSize = size
    }
  },
)

watch(
  () => props.highlightLine,
  (lineNo) => {
    if (view.value) applyHighlight(view.value, lineNo ?? 0)
  },
)
</script>

<template>
  <div
    class="oj-editor"
    :style="{ minHeight: props.minHeight, '--oj-editor-font-size': props.fontSize }"
  >
    <Codemirror
      v-model="model"
      :extensions="langExt"
      :style="{ height: '100%', fontSize: props.fontSize }"
      @ready="onEditorReady"
    />
  </div>
</template>

<style scoped>
.oj-editor {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--el-border-color);
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
}
.oj-editor :deep(.cm-editor) {
  min-height: inherit;
  font-size: var(--oj-editor-font-size, 14px);
  max-width: 100%;
}
.oj-editor :deep(.cm-scroller) {
  min-height: inherit;
  overflow: auto;
}
.oj-editor :deep(.cm-trace-current-line) {
  background: rgba(34, 211, 238, 0.16) !important;
  box-shadow: inset 3px 0 0 #22d3ee;
}
</style>
