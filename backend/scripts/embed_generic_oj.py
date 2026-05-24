from pathlib import Path

p = (
    Path(__file__).resolve().parents[1].parent
    / "frontend"
    / "src"
    / "views"
    / "learn"
    / "GenericModuleLearnView.vue"
)
t = p.read_text(encoding="utf-8")
if "InlineOjPractice" not in t:
    t = t.replace(
        "import AiTutorPanel from '@/components/learning/AiTutorPanel.vue'",
        "import AiTutorPanel from '@/components/learning/AiTutorPanel.vue'\n"
        "import InlineOjPractice from '@/components/oj/InlineOjPractice.vue'",
    )
start = t.index('          <template v-if="current.main">')
end = t.index('          <div class="pager">')
replacement = """          <template v-if="current.main">
            <el-divider content-position="left">
              <span class="divider-label">主刷题 · 在线练习</span>
            </el-divider>
            <InlineOjPractice :main="current.main" :related="current.related" />
          </template>

"""
p.write_text(t[:start] + replacement + t[end:], encoding="utf-8")
print("ok")
