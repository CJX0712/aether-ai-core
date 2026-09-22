"""检索模块：查询改写 + 向量召回 + 可选重排，组合为 Retriever。"""

from __future__ import annotations

from ..core.protocols import Embedder, Reranker, Retriever, VectorStore
from ..core.types import Chunk


class VectorRetriever(Retriever):
    def __init__(
        self,
        embedder: Embedder,
        store: VectorStore,
        reranker: Reranker | None = None,
        expand: int = 3,
    ) -> None:
        self.embedder = embedder
        self.store = store
        self.reranker = reranker
        self.expand = expand

    def retrieve(self, query: str, k: int = 5) -> list[Chunk]:
        qv = self.embedder.embed([query])[0]
        hits = self.store.search(qv, k * self.expand)
        chunks: list[Chunk] = []
        for cid, score in hits:
            meta = self.store.get(cid) or {}
            text = meta.get("text", "")
            clean = {key: val for key, val in meta.items() if key != "text"}
            chunks.append(
                Chunk(text=text, meta=clean, chunk_id=cid, doc_id=meta.get("doc_id"), score=score)
            )
        if self.reranker is not None:
            chunks = self.reranker.rerank(query, chunks, top_n=k)
        else:
            chunks = chunks[:k]
        return chunks[:k]


__all__ = ["VectorRetriever"]
