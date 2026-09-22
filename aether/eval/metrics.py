"""评估指标：召回率 / nDCG / 忠实度（启发式词重叠）。"""

from __future__ import annotations

import math

from ..providers.local import tokenize


def recall_at_k(retrieved: list, relevant: set, k: int) -> float:
    if not relevant:
        return 0.0
    top = set(retrieved[:k])
    return len(top & set(relevant)) / len(set(relevant))


def ndcg_at_k(retrieved: list, relevant: set, k: int) -> float:
    rel = set(relevant)
    dcg = 0.0
    for i, d in enumerate(retrieved[:k]):
        if d in rel:
            dcg += 1.0 / math.log2(i + 2)
    idcg = 0.0
    for i in range(min(len(relevant), k)):
        idcg += 1.0 / math.log2(i + 2)
    return dcg / idcg if idcg > 0 else 0.0


def faithfulness(answer: str, contexts: list[str]) -> float:
    """词级重叠启发式：答案中有多少词能在检索上下文中找到。

    注意：这是轻量代理指标，非严格事实一致性判据。
    """
    ans = tokenize(answer)
    ctx = set().union(*[tokenize(c) for c in contexts]) if contexts else set()
    if not ans:
        return 0.0
    return len(ans & ctx) / len(ans)


__all__ = ["recall_at_k", "ndcg_at_k", "faithfulness"]
