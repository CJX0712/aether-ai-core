"""Faiss 生产向量库单测。"""

from aether.providers.faiss_store import FaissVectorStore
from aether.providers.local import HashEmbedder


def test_faiss_search():
    s = FaissVectorStore()
    e = HashEmbedder(dim=64)
    vecs = e.embed(["苹果 iPhone", "特斯拉汽车", "苹果芯片"])
    s.add(vecs, [{"text": t} for t in ["苹果 iPhone", "特斯拉汽车", "苹果芯片"]], [f"c{i}" for i in range(3)])
    q = e.embed(["苹果"])[0]
    hits = s.search(q, 2)
    assert len(hits) == 2
    ids = {h[0] for h in hits}
    assert "c0" in ids and "c2" in ids
