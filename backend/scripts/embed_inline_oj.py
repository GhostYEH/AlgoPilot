"""学习页：将力扣外链块替换为内嵌 InlineOjPractice。"""
import re
from pathlib import Path

d = "di" + "v"
ROOT = Path(__file__).resolve().parents[1].parent / "frontend" / "src" / "views" / "learn"

IMPORT_LINE = (
    "import InlineOjPractice from '@/components/oj/InlineOjPractice.vue'\n"
)

REPLACEMENT_MAIN_RELATED = """<InlineOjPractice
              :main="current.main"
              :related="current.related"
            />"""

REPLACEMENT_MAIN_ONLY = '<InlineOjPractice :main="current.main" />'

for path in sorted(ROOT.glob("*ModuleView.vue")):
    t = path.read_text(encoding="utf-8")
    if "InlineOjPractice" not in t:
        anchor = "import AiTutorPanel from '@/components/learning/AiTutorPanel.vue'"
        if anchor in t:
            t = t.replace(anchor, anchor + "\n" + IMPORT_LINE.strip())
        else:
            print("skip import", path.name)
            continue

    # 主刷题 + 相关练习 合并为一块（去掉两个 template 之间的 related 块）
    pattern = re.compile(
        r'<template v-if="current\.main">.*?'
        r'<template v-if="current\.related\?\.length">.*?</template>\s*'
        r'(?=\s*<template v-if=|<div class="pager"|<template v-else)',
        re.DOTALL,
    )
    block = pattern.search(t)
    if block:
        inner_main = """<template v-if="current.main">
            <el-divider content-position="left">
              <span class="divider-label">主刷题 · 在线练习</span>
            </el-divider>
            """
        if "practiceLinkLabel" in t:
            inner_main += REPLACEMENT_MAIN_RELATED.replace(
                "/>",
                '\n              :link-label="practiceLinkLabel"\n            />',
                1,
            )
        else:
            inner_main += REPLACEMENT_MAIN_RELATED
        inner_main += "\n          </template>\n\n          "
        t = t[: block.start()] + inner_main + t[block.end() :]
        path.write_text(t, encoding="utf-8")
        print("merged", path.name)
        continue

    # 仅主刷题
    pattern2 = re.compile(
        rf'<template v-if="current\.main">.*?'
        rf'<{d} class="practice-main">.*?</{d}>\s*</template>',
        re.DOTALL,
    )
    if pattern2.search(t):
        t = pattern2.sub(
            """<template v-if="current.main">
            <el-divider content-position="left">
              <span class="divider-label">主刷题 · 在线练习</span>
            </el-divider>
            """
            + (
                REPLACEMENT_MAIN_RELATED.replace(
                    ":related=\"current.related\"\n            ",
                    "",
                )
                if "current.related" not in t
                else REPLACEMENT_MAIN_RELATED
            )
            + "\n          </template>",
            t,
            count=1,
        )
        path.write_text(t, encoding="utf-8")
        print("main only", path.name)
