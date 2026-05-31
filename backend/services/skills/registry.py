"""SkillRegistry：启动时加载 YAML 技能卡。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from services.skills.models import SkillCard

_CARDS_DIR = Path(__file__).resolve().parent / "cards"


class SkillRegistry:
    def __init__(self, cards_dir: Path | None = None) -> None:
        self._cards_dir = cards_dir or _CARDS_DIR
        self._cards: dict[str, SkillCard] = {}
        self.reload()

    def reload(self) -> int:
        self._cards.clear()
        if not self._cards_dir.is_dir():
            return 0
        for path in sorted(self._cards_dir.glob("*.yaml")):
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                continue
            card = SkillCard.model_validate(raw)
            self._cards[card.id] = card
        return len(self._cards)

    def list_cards(self, *, course_id: str = "") -> list[SkillCard]:
        items = list(self._cards.values())
        if course_id:
            items = [c for c in items if c.course_id == course_id]
        return sorted(items, key=lambda c: c.id)

    def get(self, skill_id: str) -> SkillCard | None:
        return self._cards.get(skill_id)

    def __len__(self) -> int:
        return len(self._cards)


@lru_cache(maxsize=1)
def get_registry() -> SkillRegistry:
    return SkillRegistry()


def clear_registry_cache() -> None:
    get_registry.cache_clear()
