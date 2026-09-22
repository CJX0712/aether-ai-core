"""管道装配：将各单一职责模块组合成完整可运行链路。

设计要点：
- 模块间只依赖 Protocol 接口，具体实现运行时注入；
- build_default_pipeline() 注入零依赖实现，离线即可跑通；
- build_pipeline(config) 按配置切换生产实现（faiss / bge / llama.cpp / OpenAI 兼容）。
"""

from __future__ import annotations

from typing import Any

from .agent.agent import ReActAgent
from .core.protocols import Agent, Embedder, LLM, Reranker, Retriever, VectorStore
from .core.types import Chunk, Document, Message
from .ingest.splitter import RecursiveCharacterSplitter
from .providers.local import HashEmbedder, HeuristicReranker, MemoryVectorStore, MockLLM
from .retrieve.retriever import VectorRetriever


class AetherPipeline:
    def __init__(
        self,
        embedder: Embedder,
        store: VectorStore,
        splitter: RecursiveCharacterSplitter | None = None,
        reranker: Reranker | None = None,
        llm: LLM | None = None,
        agent_tools: list[Any] | None = None,
    ) -> None:
        self.embedder = embedder
        self.store = store
        self.splitter = splitter or RecursiveCharacterSplitter()
        self.reranker = reranker
        self.llm = llm
        self.retriever: Retriever = VectorRetriever(embedder, store, reranker)
        self.agent_tools = agent_tools or []
        self._seq = 0

    def add_text(self, text: str, meta: dict | None = None) -> int:
        return self.add_documents([Document(text=text, meta=meta or {})])

    def add_documents(self, docs: list[Document]) -> int:
        added = 0
        for d in docs:
            chunks = self.splitter.split(d)
            for c in chunks:
                vec = self.embedder.embed([c.text])[0]
                cid = f"c{self._seq}"
                self._seq += 1
                c.chunk_id = cid
                meta = dict(c.meta)
                meta["text"] = c.text
                meta["doc_id"] = c.doc_id
                self.store.add([vec], [meta], [cid])
                added += 1
        return added

    def ask(self, question: str, k: int = 5) -> dict[str, Any]:
        chunks = self.retriever.retrieve(question, k)
        context = "\n---\n".join(c.text for c in chunks)
        prompt = f"Context:\n{context}\n\nQuestion: {question}\nFinal Answer:"
        answer = self.llm.generate(prompt) if self.llm else "(未配置 LLM)"
        return {
            "answer": answer,
            "contexts": [{"text": c.text, "score": c.score, "doc_id": c.doc_id} for c in chunks],
        }

    def run_agent(self, task: str, max_steps: int = 5, tools: list[Any] | None = None) -> str:
        if self.llm is None:
            return "(未配置 LLM，无法运行 Agent)"
        agent: Agent = ReActAgent(self.llm, tools or self.agent_tools, max_steps)
        return agent.run(task, max_steps)


def build_default_pipeline() -> AetherPipeline:
    """零依赖离线链路：哈希向量化 + 内存向量库 + 启发式重排 + Mock 大模型。"""
    return AetherPipeline(
        embedder=HashEmbedder(dim=256),
        store=MemoryVectorStore(),
        splitter=RecursiveCharacterSplitter(chunk_size=200, chunk_overlap=40),
        reranker=HeuristicReranker(),
        llm=MockLLM(),
    )


def build_pipeline(config: dict[str, Any] | None = None) -> AetherPipeline:
    """按配置构建生产链路。

    config 示例：
    {
      "embedder": "sentence", "model_name": "BAAI/bge-small-zh-v1.5",
      "store": "faiss",
      "reranker": "local",
      "llm": "openai", "llm_base_url": "https://api.openai.com/v1", "llm_model": "gpt-4o-mini"
    }
    """
    from .providers.faiss_store import FaissVectorStore
    from .providers.llama_cpp_llm import LlamaCppLLM
    from .providers.openai_llm import OpenAILLM
    from .providers.sentence_embedder import SentenceEmbedder

    cfg = config or {}
    emb = cfg.get("embedder", "local")
    if emb == "local":
        embedder: Embedder = HashEmbedder(dim=cfg.get("dim", 256))
    elif emb == "sentence":
        embedder = SentenceEmbedder(cfg.get("model_name", "BAAI/bge-small-zh-v1.5"))
    else:
        raise ValueError(f"未知 embedder: {emb}")

    store_cfg = cfg.get("store", "local")
    if store_cfg == "local":
        store: VectorStore = MemoryVectorStore()
    elif store_cfg == "faiss":
        store = FaissVectorStore()
    else:
        raise ValueError(f"未知 store: {store_cfg}")

    rer = cfg.get("reranker", "local")
    reranker: Reranker | None = HeuristicReranker() if rer == "local" else None

    llm_cfg = cfg.get("llm", "mock")
    if llm_cfg == "mock":
        llm: LLM = MockLLM()
    elif llm_cfg == "openai":
        llm = OpenAILLM(
            base_url=cfg.get("llm_base_url", "https://api.openai.com/v1"),
            model=cfg.get("llm_model", "gpt-4o-mini"),
            api_key=cfg.get("llm_api_key"),
        )
    elif llm_cfg == "llama_cpp":
        llm = LlamaCppLLM(cfg["llm_model_path"])
    else:
        raise ValueError(f"未知 llm: {llm_cfg}")

    return AetherPipeline(
        embedder=embedder,
        store=store,
        splitter=RecursiveCharacterSplitter(
            chunk_size=cfg.get("chunk_size", 200), chunk_overlap=cfg.get("chunk_overlap", 40)
        ),
        reranker=reranker,
        llm=llm,
    )


SAMPLE_CORPUS = [
    "苹果公司将于2026年发布新款iPhone，搭载A19芯片。",
    "特斯拉的自动驾驶采用纯视觉方案，不依赖激光雷达。",
    "iPhone的电池续航在2026款上提升至30小时视频播放。",
    "微软Azure提供全球云计算服务，覆盖多个区域。",
    "A19芯片采用3纳米工艺，CPU性能提升约20%。",
]


def load_sample(pipeline: AetherPipeline) -> int:
    """载入内置示例语料，便于开箱体验与 CLI 演示。doc_id 固定为语料索引。"""
    docs = [Document(text=t, doc_id=str(i)) for i, t in enumerate(SAMPLE_CORPUS)]
    return pipeline.add_documents(docs)


__all__ = [
    "AetherPipeline",
    "build_default_pipeline",
    "build_pipeline",
    "load_sample",
    "SAMPLE_CORPUS",
]
