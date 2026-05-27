"""概念图社区发现。"""

from __future__ import annotations

from services.knowledge.concept_clusters import concept_clusters


def test_concept_clusters_non_empty() -> None:
    clusters = concept_clusters()
    assert len(clusters) >= 5
    assert all(k.startswith("cluster-") for k in set(clusters.values()))
