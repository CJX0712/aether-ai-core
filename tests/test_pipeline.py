"""管道与检索单测。"""

from aether.eval.metrics import recall_at_k
from aether.pipeline import build_default_pipeline, load_sample


def test_pipeline_add_text():
    p = build_default_pipeline()
    n = p.add_text("一段独立的中文测试内容，用于验证写入。")
    assert n >= 1


def test_pipeline_ask_offline():
    p = build_default_pipeline()
    load_sample(p)
    r = p.ask("iPhone 2026 用的什么芯片？")
    assert r["contexts"]
    assert "Final Answer" in r["answer"]


def test_retrieve_recall():
    p = build_default_pipeline()
    load_sample(p)
    chunks = p.retriever.retrieve("iPhone 2026 芯片", k=5)
    ids = [c.doc_id for c in chunks]
    assert recall_at_k(ids, {"0", "2", "4"}, 5) >= 0.99
