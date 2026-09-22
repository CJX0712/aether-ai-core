"""评估套件单测。"""

from aether.eval.suite import run_suite
from aether.pipeline import build_default_pipeline


def test_eval_suite():
    p = build_default_pipeline()
    rep = run_suite(p)
    assert rep["recall@5"] >= 0.99
    assert 0.0 <= rep["ndcg@5"] <= 1.0
    assert "answer" in rep
    assert rep["num_indexed"] == 5
