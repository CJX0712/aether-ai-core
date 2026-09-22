"""Faiss 向量库实现（lazy import faiss-cpu）。

生产级近似/精确检索，替代零依赖 MemoryVectorStore。接口与 MemoryVectorStore 完全一致。
"""

from __future__ import annotations

import numpy as np

from ..core.protocols import VectorStore


class FaissVectorStore(VectorStore):
    def __init__(self, metric: str = "ip") -> None:
        try:
            import faiss  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError("需要 faiss-cpu：pip install faiss-cpu") from exc
        self._faiss = faiss
        self._metric = metric
        self._index = None
        self._dim: int | None = None
        self._ids: list[str] = []
        self._metas: dict[str, dict] = {}

    def _build_index(self) -> None:
        if self._metric == "l2":
            self._index = self._faiss.IndexFlatL2(self._dim)
        else:
            self._index = self._faiss.IndexFlatIP(self._dim)

    def add(self, vectors: list[list[float]], metas: list[dict], ids: list[str]) -> None:
        arr = np.array(vectors, dtype="float32")
        if self._dim is None:
            self._dim = arr.shape[1]
            self._build_index()
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        arr = arr / norms
        self._index.add(arr)
        for vid, meta in zip(ids, metas):
            self._ids.append(vid)
            self._metas[vid] = dict(meta)

    def search(self, query_vec: list[float], k: int) -> list[tuple[str, float]]:
        if not self._ids:
            return []
        q = np.array([query_vec], dtype="float32")
        n = np.linalg.norm(q)
        if n > 0:
            q = q / n
        kk = min(k, len(self._ids))
        dist, idx = self._index.search(q, kk)
        out: list[tuple[str, float]] = []
        for score, j in zip(dist[0], idx[0]):
            if j < 0:
                continue
            out.append((self._ids[int(j)], float(score)))
        return out

    def get(self, id: str) -> dict | None:
        return self._metas.get(id)


__all__ = ["FaissVectorStore"]
