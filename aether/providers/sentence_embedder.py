"""Sentence-Transformers 向量化实现（lazy import）。

默认使用 BAAI/bge-small-zh-v1.5，对中文检索质量显著优于哈希向量化。
替代零依赖 HashEmbedder，接口一致。
"""

from __future__ import annotations

from ..core.protocols import Embedder


class SentenceEmbedder(Embedder):
    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5", normalize: bool = True) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "需要 sentence-transformers：pip install sentence-transformers"
            ) from exc
        self._model = SentenceTransformer(model_name)
        self.dim = self._model.get_sentence_embedding_dimension()
        self.model_name = model_name
        self._normalize = normalize

    def embed(self, texts: list[str]) -> list[list[float]]:
        vecs = self._model.encode(texts, normalize_embeddings=self._normalize)
        return vecs.tolist()


__all__ = ["SentenceEmbedder"]
