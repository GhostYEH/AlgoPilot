"""MasteryAgent：基于掌握度生成建议与路径调整。"""

from __future__ import annotations

from services.mastery.models import (
    MasteryReport,
    MasteryResourceHint,
)


class MasteryAgent:
    name = "MasteryAgent"
    role = "学习效果掌握度评估"

    def enrich_report(
        self,
        report: MasteryReport,
        *,
        chapter_module_keys: list[str] | None = None,
        next_chapter_id: str = "",
    ) -> MasteryReport:
        """补充推荐动作、资源与路径建议。"""
        score = report.mastery_score
        level = report.mastery_level
        actions: list[str] = []
        resources: list[MasteryResourceHint] = []
        path_hint = ""

        if level == "beginner" or score < 40:
            actions.append("先完成本章概念文档与 1 道引导例题，再进入 OJ")
            resources.append(
                MasteryResourceHint(
                    resource_type="document",
                    topic=report.chapter_title or "本章导学",
                    reason="夯实基础概念，降低首次 WA 概率",
                )
            )
            path_hint = "建议停留在当前章节，插入巩固节点后再前进"
        elif level == "improving":
            actions.append("针对薄弱技能做 2～3 道同类变式题")
            if report.weak_skills:
                actions.append(f"重点巩固：{', '.join(report.weak_skills[:3])}")
            resources.append(
                MasteryResourceHint(
                    resource_type="exercises",
                    topic=report.weak_skills[0] if report.weak_skills else "本章练习",
                    reason="错因导向的变式训练",
                )
            )
            path_hint = "可继续当前章节，但需在 OJ 连续 AC 后再解锁下一章"
        elif level == "competent":
            actions.append("完成本章综合题单，并尝试 1 道 Trace 诊断复盘")
            resources.append(
                MasteryResourceHint(
                    resource_type="trace_animation",
                    topic=report.chapter_title or "算法轨迹",
                    reason="通过可视化巩固调试能力",
                )
            )
            path_hint = "掌握度达标，可进入下一章节；建议保留每周复习"
        else:
            actions.append("挑战进阶题或参加章节综合项目")
            resources.append(
                MasteryResourceHint(
                    resource_type="code_case",
                    topic="综合应用",
                    reason="将本章技能迁移到开放场景",
                )
            )
            path_hint = "可跳过基础巩固节点，路径 Agent 将优先推荐进阶模块"

        if report.weak_skills and level in ("beginner", "improving"):
            for skill in report.weak_skills[:2]:
                resources.append(
                    MasteryResourceHint(
                        resource_type="document",
                        topic=skill,
                        reason="SkillCard 关联薄弱技能",
                    )
                )

        if next_chapter_id and score >= 60:
            path_hint = f"掌握度 {score}，建议下一章：{next_chapter_id}"

        report.recommended_actions = actions[:5]
        report.recommended_resources = resources[:5]
        if not report.path_adjustment_suggestion:
            report.path_adjustment_suggestion = path_hint
        return report

    def path_adjustment_for_score(
        self,
        mastery_score: int,
        *,
        chapter_id: str = "",
        remediation_needed: bool = False,
    ) -> str:
        if remediation_needed or mastery_score < 40:
            return f"章节 {chapter_id or '当前'} 掌握度偏低，插入巩固节点并推荐复习资源"
        if mastery_score < 60:
            return "保持当前章节进度，完成推荐练习后再解锁下一章"
        if mastery_score < 80:
            return "掌握度良好，可按路径进入下一章节"
        return "掌握度优秀，路径可跳过基础复习直达进阶内容"


mastery_agent = MasteryAgent()
