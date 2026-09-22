"""ReAct 风格 Agent：思考-行动-观察 循环 + 工具调用。

遵循与 MockLLM / 真实 LLM 一致的文本协议：
- LLM 输出含 "Action: <name>\\nAction Input: <input>" -> 执行工具，把 Observation 喂回；
- LLM 输出含 "Final Answer: <text>" -> 结束并返回结果。
任意 LLM 实现只要产出上述格式即可驱动本 Agent，无需改动。
"""

from __future__ import annotations

import ast
import operator
import re

from ..core.protocols import Agent, LLM
from ..core.types import Message
from .tools import Tool


def _safe_eval(expr: str) -> str:
    """仅支持四则运算的安全求值，供 calculator 工具使用。"""
    allowed = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
    }

    def _ev(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return _ev(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise ValueError("仅支持数字")
        if isinstance(node, ast.BinOp) and type(node.op) in allowed:
            return allowed[type(node.op)](_ev(node.left), _ev(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -_ev(node.operand)
        raise ValueError("不支持的表达式")

    return str(_ev(ast.parse(expr, mode="eval")))


def make_calculator() -> Tool:
    return Tool(
        name="calculator",
        description="计算四则运算表达式，例如 2+3*4",
        func=_safe_eval,
    )


class ReActAgent(Agent):
    def __init__(self, llm: LLM, tools: list[Tool] | None = None, max_steps: int = 5) -> None:
        self.llm = llm
        self.tools = tools or []
        self.max_steps = max_steps

    def _build_prompt(self, task: str, history: list[Message]) -> str:
        p = f"Task: {task}\n"
        if self.tools:
            p += "Available tools:\n"
            for t in self.tools:
                p += f"- name: {t.name}\n  description: {t.description}\n"
        for h in history:
            p += h.content + "\n"
        return p

    def run(self, task: str, max_steps: int | None = None) -> str:
        steps = max_steps or self.max_steps
        history: list[Message] = []
        for _ in range(steps):
            prompt = self._build_prompt(task, history)
            out = self.llm.generate(prompt, history=history)
            if "Final Answer:" in out:
                return out.split("Final Answer:")[-1].strip()
            m = re.search(r"Action:\s*(\w+)\s*\n?Action Input:\s*(.*)", out, re.DOTALL)
            if not m:
                return out.strip()
            name = m.group(1)
            inp = m.group(2).strip()
            tool = next((t for t in self.tools if t.name == name), None)
            obs = tool.func(inp) if tool else f"error: 未找到工具 {name}"
            history.append(Message(role="user", content=f"Observation: {obs}"))
        return "已达到最大步数仍未给出最终答案。"


__all__ = ["Tool", "ReActAgent", "make_calculator"]
