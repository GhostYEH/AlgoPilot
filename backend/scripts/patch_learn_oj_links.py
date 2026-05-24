"""为专用学习页注入 PracticeOjLinks 组件。"""
import re
from pathlib import Path

d = "di" + "v"
ROOT = Path(__file__).resolve().parents[1].parent / "frontend" / "src" / "views" / "learn"
FILES = [
    "ArrayModuleView.vue",
    "HashTableModuleView.vue",
    "StringModuleView.vue",
    "TwoPointersModuleView.vue",
]

for name in FILES:
    p = ROOT / name
    t = p.read_text(encoding="utf-8")
    if "PracticeOjLinks" not in t:
        t = t.replace(
            "import AiTutorPanel from '@/components/learning/AiTutorPanel.vue'",
            "import AiTutorPanel from '@/components/learning/AiTutorPanel.vue'\n"
            "import PracticeOjLinks from '@/components/learning/PracticeOjLinks.vue'",
        )
    t = re.sub(
        rf"<{d} class=\"practice-main\">.*?</{d}>\s*",
        '<PracticeOjLinks :main="current.main" />\n              ',
        t,
        count=1,
        flags=re.DOTALL,
    )
    t = re.sub(
        rf"<{d} class=\"related\">.*?</{d}>\s*",
        '<PracticeOjLinks :related="current.related" />\n              ',
        t,
        count=1,
        flags=re.DOTALL,
    )
    p.write_text(t, encoding="utf-8")
    print("patched", name)
