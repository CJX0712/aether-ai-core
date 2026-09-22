"""端到端评估套件：在合成语料上验证检索与生成质量。

相关性标签为人工设定（query 关于 iPhone 2026 芯片，相关 doc 索引 0/2/4），
用于回归各模块指标，保证链路可独立验证。
"""

from __future__ import annotations

from ..pipeline import AetherPipeline, load_sample
from .metrics import faithfulness, ndcg_at_k, recall_at_k

_QUERY = "iPhone 2026 用的什么芯片？"
_RELEVANT = {"0", "2", "4"}


def run_suite(pipeline: AetherPipeline) -> dict:
    num_indexed = load_sample(pipeline)
    chunks = pipeline.retriever.retrieve(_QUERY, k=5)
    retrieved_ids = [c.doc_id for c in chunks]

    ask_result = pipeline.ask(_QUERY)
    answer = ask_result["answer"]
    contexts = [c["text"] for c in ask_result["contexts"]]

    return {
        "num_indexed": num_indexed,
        "query": _QUERY,
        "retrieved_doc_ids": retrieved_ids,
        "recall@3": round(recall_at_k(retrieved_ids, _RELEVANT, 3), 4),
        "recall@5": round(recall_at_k(retrieved_ids, _RELEVANT, 5), 4),
        "ndcg@5": round(ndcg_at_k(retrieved_ids, _RELEVANT, 5), 4),
        "faithfulness": round(faithfulness(answer, contexts), 4),
        "answer": answer,
    }


__all__ = ["run_suite"]
