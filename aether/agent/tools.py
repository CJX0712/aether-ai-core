"""工具定义。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class Tool:
    """可被 Agent 调用的工具。func 接收字符串输入，返回字符串结果。"""

    name: str
    description: str
    func: Callable[[str], str]


__all__ = ["Tool"]
