from pathlib import Path

p = (
    Path(__file__).resolve().parents[1].parent
    / "frontend"
    / "src"
    / "views"
    / "learn"
    / "HashTableModuleView.vue"
)
t = p.read_text(encoding="utf-8")
if "InlineOjPractice" not in t:
    t = t.replace(
        "import AiTutorPanel from '@/components/learning/AiTutorPanel.vue'",
        "import AiTutorPanel from '@/components/learning/AiTutorPanel.vue'\n"
        "import InlineOjPractice from '@/components/oj/InlineOjPractice.vue'",
    )
# 去掉卡片头部的力扣外链
old_header_link = """                <el-link
                  v-if="current.main"
                  type="primary"
                  class="main-lc"
                  :href="leetcodeCnUrl(current.main.slug)"
                  target="_blank"
                  rel="noopener"
                >
                  <el-icon><Link /></el-icon>
                  力扣 {{ current.main.id }} · {{ current.main.title }}
                </el-link>
"""
if old_header_link in t:
    t = t.replace(old_header_link, "")

insert_anchor = "            <LearnSectionBody :section=\"asLearnSection(current)\" />\n"
insert_block = """            <LearnSectionBody :section="asLearnSection(current)" />

            <template v-if="current.main">
              <el-divider content-position="left">主刷题 · 在线练习</el-divider>
              <InlineOjPractice :main="current.main" :related="current.related" />
            </template>

"""
if insert_anchor in t and "InlineOjPractice" in t and insert_block.strip() not in t:
    t = t.replace(insert_anchor, insert_block, 1)

# 去掉底部相关练习外链
start = t.find("            <template v-if=\"current.related?.length\">")
if start > 0:
    end = t.find("            <template v-if=\"current.id === 'theory'\">", start)
    if end > start:
        t = t[:start] + t[end:]

p.write_text(t, encoding="utf-8")
print("ok")
