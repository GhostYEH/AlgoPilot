from pathlib import Path

ROOT = Path(__file__).resolve().parents[1].parent / "frontend" / "src" / "views" / "learn"

for name in ["ArrayModuleView.vue", "HashTableModuleView.vue", "TwoPointersModuleView.vue"]:
    p = ROOT / name
    t = p.read_text(encoding="utf-8")
    if "InlineOjPractice" not in t:
        t = t.replace(
            "import AiTutorPanel from '@/components/learning/AiTutorPanel.vue'",
            "import AiTutorPanel from '@/components/learning/AiTutorPanel.vue'\n"
            "import InlineOjPractice from '@/components/oj/InlineOjPractice.vue'",
        )
    start = t.index('              <template v-if="current.main">')
    idx = t.index('          <div class="pager">', start)
    replacement = """              <template v-if="current.main">
                <el-divider content-position="left">
                  <span class="divider-label">主刷题 · 在线练习</span>
                </el-divider>
                <InlineOjPractice :main="current.main" :related="current.related" />
              </template>

"""
    t = t[:start] + replacement + t[idx:]
    p.write_text(t, encoding="utf-8")
    print("ok", name)
