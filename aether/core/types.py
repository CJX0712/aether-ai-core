"""核心数据类型定义。

所有模块通过统一的数据契约（Document / Chunk / Message）传递，
保证各 AI 功能模块可独立验证、可组合成完整链路。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    """一篇原始文档。"""

    text: str
    meta: dict[str, Any] = field(default_factory=dict)
    doc_id: str | None = None


@dataclass
class Chunk:
    """文档切分后的最小检索单元。"""

    text: str
    meta: dict[str, Any] = field(default_factory=dict)
    chunk_id: str | None = None
    doc_id: str | None = None
    score: float = 0.0


@dataclass
class Message:
    """对话/工具消息。"""

    role: str  # user | assistant | system | tool
    content: str
    name: str | None = None


__all__ = ["Document", "Chunk", "Message"]
