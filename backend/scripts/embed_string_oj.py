from pathlib import Path

p = (
    Path(__file__).resolve().parents[1].parent
    / "frontend"
    / "src"
    / "views"
    / "learn"
    / "StringModuleView.vue"
)
t = p.read_text(encoding="utf-8")
start = t.index('              <template v-if="current.main">')
end = t.index("              <template v-if=\"current.id === 'theory'\">")
replacement = """              <template v-if="current.main">
                <el-divider content-position="left">
                  <span class="divider-label">主刷题 · 在线练习</span>
                </el-divider>
                <InlineOjPractice
                  :main="current.main"
                  :related="current.related"
                  :link-label="practiceLinkLabel"
                />
              </template>

"""
p.write_text(t[:start] + replacement + t[end:], encoding="utf-8")
print("ok")
