"""零依赖 Provider 单测。"""

from aether.core.types import Chunk
from aether.providers.local import HashEmbedder, HeuristicReranker, MemoryVectorStore


def _cos(x, y):
    return sum(a * b for a, b in zip(x, y))


def test_hash_embedder_deterministic():
    e = HashEmbedder(dim=64)
    a = e.embed(["苹果手机"])[0]
    b = e.embed(["苹果手机"])[0]
    assert a == b
    assert abs(sum(v * v for v in a) - 1.0) < 1e-6


def test_hash_embedder_similarity():
    e = HashEmbedder(dim=128)
    same = e.embed(["iPhone 芯片"])[0]
    similar = e.embed(["iPhone的芯片"])[0]
    diff = e.embed(["特斯拉电池"])[0]
    assert _cos(same, similar) > _cos(same, diff)


def test_memory_store_search():
    s = MemoryVectorStore()
    e = HashEmbedder(dim=64)
    vecs = e.embed(["苹果 iPhone", "特斯拉汽车", "苹果芯片"])
    s.add(vecs, [{"text": t} for t in ["苹果 iPhone", "特斯拉汽车", "苹果芯片"]], [f"c{i}" for i in range(3)])
    q = e.embed(["苹果"])[0]
    hits = s.search(q, 2)
    assert len(hits) == 2
    ids = {h[0] for h in hits}
    assert "c0" in ids and "c2" in ids


def test_heuristic_rerank_promotes_relevant():
    r = HeuristicReranker()
    chunks = [
        Chunk(text="特斯拉电池续航很长", score=0.9),
        Chunk(text="苹果 iPhone 芯片性能强劲", score=0.1),
    ]
    out = r.rerank("苹果 iPhone", chunks)
    assert out[0].text.startswith("苹果")
