"""REST API 单测（TestClient，离线）。"""

from fastapi.testclient import TestClient

from aether.api.app import app


def test_health():
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ingest_and_ask():
    c = TestClient(app)
    r = c.post("/v1/ingest", json={"texts": ["苹果iPhone使用A19芯片"]})
    assert r.status_code == 200
    assert r.json()["added"] >= 1
    r2 = c.post("/v1/ask", json={"question": "芯片是什么？", "k": 3})
    assert r2.status_code == 200
    assert r2.json()["contexts"]


def test_eval_endpoint():
    c = TestClient(app)
    r = c.post("/v1/eval")
    assert r.status_code == 200
    body = r.json()
    assert "recall@5" in body
    assert 0.0 <= body["ndcg@5"] <= 1.0
