"""模块接口契约（Protocol / ABC）。

每个外部能力都被抽象为一个接口，运行时注入具体实现。
默认注入零依赖实现（见 aether.providers.local），使整个系统在
无网络、无 API Key、无重型依赖下也能离线跑通与验证。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .types import Chunk, Document, Message


class Embedder(ABC):
    """文本 -> 向量。"""

    dim: int = 0

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """批量将文本编码为向量列表。"""
        raise NotImplementedError


class VectorStore(ABC):
    """向量索引：增 / 查。"""

    @abstractmethod
    def add(self, vectors: list[list[float]], metas: list[dict], ids: list[str]) -> None:
        """写入向量与其元数据。"""
        raise NotImplementedError

    @abstractmethod
    def search(self, query_vec: list[float], k: int) -> list[tuple[str, float]]:
        """返回 [(id, score)]，score 越大越相似，降序排列，至多 k 条。"""
        raise NotImplementedError

    @abstractmethod
    def get(self, id: str) -> dict | None:
        """按 id 取回元数据（含原文 text）。"""
        raise NotImplementedError


class Reranker(ABC):
    """交叉编码器 / 启发式精排。"""

    @abstractmethod
    def rerank(self, query: str, chunks: list[Chunk], top_n: int | None = None) -> list[Chunk]:
        """对候选 chunk 重新打分排序，返回新的 Chunk 列表（含 score）。"""
        raise NotImplementedError


class LLM(ABC):
    """可插拔大模型生成。"""

    @abstractmethod
    def generate(self, prompt: str, history: list[Message] | None = None, **kw: Any) -> str:
        """给定提示词与（可选）历史，返回生成文本。"""
        raise NotImplementedError


class Retriever(ABC):
    """查询 -> 相关 chunk。"""

    @abstractmethod
    def retrieve(self, query: str, k: int = 5) -> list[Chunk]:
        """检索与 query 最相关的 k 个 chunk。"""
        raise NotImplementedError


class Agent(ABC):
    """任务编排（ReAct 循环 + 工具调用）。"""

    @abstractmethod
    def run(self, task: str, max_steps: int = 5) -> str:
        """执行任务，返回最终结果文本。"""
        raise NotImplementedError


__all__ = ["Embedder", "VectorStore", "Reranker", "LLM", "Retriever", "Agent"]
