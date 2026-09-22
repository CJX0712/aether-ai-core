"""REST API 网关（FastAPI）。

默认注入零依赖链路，离线即可启动；生产实现通过环境变量/配置在 build_pipeline 中切换。
所有重型依赖均为 lazy import，保证 API 模块可被测试客户端无副作用导入。
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from ..core.types import Document
from ..pipeline import build_default_pipeline, load_sample

app = FastAPI(title="Aether AI Core", version="0.1.0")

_pipeline = None


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = build_default_pipeline()
        load_sample(_pipeline)
    return _pipeline


class IngestReq(BaseModel):
    texts: list[str] | None = None
    docs: list[dict] | None = None


class AskReq(BaseModel):
    question: str
    k: int = 5


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0", "author": "晨星"}


@app.post("/v1/ingest")
def ingest(req: IngestReq):
    p = get_pipeline()
    n = 0
    if req.texts:
        for t in req.texts:
            n += p.add_text(t)
    if req.docs:
        for d in req.docs:
            n += p.add_documents([Document(text=d.get("text", ""), meta=d.get("meta", {}))])
    return {"added": n}


@app.post("/v1/ask")
def ask(req: AskReq):
    return get_pipeline().ask(req.question, req.k)


@app.post("/v1/eval")
def eval_endpoint():
    """在全新管道上运行评估，避免复用已写入数据的运行期状态，保证结果确定性。"""
    from ..eval.suite import run_suite
    from ..pipeline import build_default_pipeline

    return run_suite(build_default_pipeline())


__all__ = ["app", "get_pipeline"]
