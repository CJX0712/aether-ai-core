"""零依赖本地 Provider 实现。

这些实现不依赖任何第三方包（仅标准库），用于：
1. 默认链路，使系统在无网络、无 API Key 下即可离线运行与验证；
2. 单元测试的 Mock，保证每个模块可独立验证。
生产环境通过环境变量切换为 faiss / sentence-transformers / llama.cpp / OpenAI 兼容实现。
"""

from __future__ import annotations

import hashlib
import math
import re

from ..core.protocols import Embedder, LLM, Reranker, VectorStore
from ..core.types import Chunk, Message


_CJK = re.compile(r"[一-鿿]")
_ASCII_WORD = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> set[str]:
    """统一分词：英文/数字词 + 中文字 unigram + 中文 bigram。

    用于哈希向量化与启发式重排，保证中文语义可被稳定捕捉。
    """
    text = (text or "").lower()
    toks: set[str] = set(_ASCII_WORD.findall(text))
    cjk = _CJK.findall(text)
    toks.update(cjk)
    for i in range(len(cjk) - 1):
        toks.add(cjk[i] + cjk[i + 1])
    return toks


class HashEmbedder(Embedder):
    """基于哈希的确定性向量化（零依赖）。

    中文采用字符 bigram 哈希，英文采用词哈希；向量 L2 归一化。
    语义相近的文本余弦相似度高，足以驱动检索与重排验证。
    """

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def _hash_idx(self, tok: str) -> int:
        digest = hashlib.sha256(tok.encode("utf-8")).digest()
        return int.from_bytes(digest[:8], "big") % self.dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for t in texts:
            vec = [0.0] * self.dim
            for tok in tokenize(t):
                vec[self._hash_idx(tok)] += 1.0
            norm = math.sqrt(sum(v * v for v in vec))
            if norm > 0:
                vec = [v / norm for v in vec]
            out.append(vec)
        return out


class MemoryVectorStore(VectorStore):
    """进程内向量库（余弦相似度，零依赖）。"""

    def __init__(self) -> None:
        self._vecs: dict[str, list[float]] = {}
        self._metas: dict[str, dict] = {}

    def add(self, vectors: list[list[float]], metas: list[dict], ids: list[str]) -> None:
        for vid, vec, meta in zip(ids, vectors, metas):
            self._vecs[vid] = list(vec)
            self._metas[vid] = dict(meta)

    def search(self, query_vec: list[float], k: int) -> list[tuple[str, float]]:
        scored: list[tuple[str, float]] = []
        for vid, vec in self._vecs.items():
            dot = sum(a * b for a, b in zip(query_vec, vec))
            scored.append((vid, dot))
        scored.sort(key=lambda x: -x[1])
        return scored[:k]

    def get(self, id: str) -> dict | None:
        return self._metas.get(id)


class HeuristicReranker(Reranker):
    """BM25 风格的启发式精排（零依赖）。

    与哈希余弦召回形成互补信号：召回看重词命中密度，重排对长文档做长度归一，
    从而能把"命中密集的短片段"排在"稀疏命中的长文档"之前。
    """

    def rerank(self, query: str, chunks: list[Chunk], top_n: int | None = None) -> list[Chunk]:
        q_toks = tokenize(query)
        ranked: list[Chunk] = []
        for c in chunks:
            c_toks = tokenize(c.text)
            if not c_toks:
                score = 0.0
            else:
                overlap = len(q_toks & c_toks)
                score = overlap / math.sqrt(len(c_toks))
            ranked.append(
                Chunk(
                    text=c.text,
                    meta=dict(c.meta),
                    chunk_id=c.chunk_id,
                    doc_id=c.doc_id,
                    score=score,
                )
            )
        ranked.sort(key=lambda x: -x.score)
        if top_n is not None:
            ranked = ranked[:top_n]
        return ranked


class MockLLM(LLM):
    """确定性 Mock 大模型，遵循 ReAct 协议。

    - 含 "Context:" 的提示：直接基于上下文给最终答案（RAG 路径）；
    - 含 "Observation:" 的提示：工具已返回结果，给出 Final Answer（Agent 路径）；
    - 含 "Available tools:" 的提示：发出首个工具的 Action（Agent 路径首轮）。
    """

    def __init__(self, model_name: str = "mock-local") -> None:
        self.model_name = model_name

    def generate(self, prompt: str, history: list[Message] | None = None, **kw: object) -> str:
        if "Observation:" in prompt:
            obs = prompt.split("Observation:")[-1].strip().splitlines()[0]
            return f"Final Answer: {obs}"

        if "Available tools:" in prompt:
            block = prompt.split("Available tools:")[-1]
            m = re.search(r"- name:\s*(\w+)", block)
            if m:
                name = m.group(1)
                tm = re.search(r"Task:\s*(.*)", prompt)
                task = tm.group(1).strip() if tm else ""
                am = re.search(r"[\d\.\+\-\*/\(\) ]+", task)
                inp = am.group(0).strip() if am else task
                return f"Action: {name}\nAction Input: {inp}"

        if "Context:" in prompt:
            ctx = prompt.split("Context:")[-1].strip().splitlines()[0]
            return f"Final Answer: {ctx}"

        return "Final Answer: 当前无可调用工具与上下文，无法给出进一步结论。"


__all__ = [
    "tokenize",
    "HashEmbedder",
    "MemoryVectorStore",
    "HeuristicReranker",
    "MockLLM",
]
