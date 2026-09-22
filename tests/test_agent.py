"""Agent 编排单测（ReAct + 工具调用）。"""

from aether.agent.agent import ReActAgent, make_calculator
from aether.pipeline import build_default_pipeline


def test_agent_calculator():
    p = build_default_pipeline()
    a = ReActAgent(p.llm, [make_calculator()])
    out = a.run("请计算 2+3 等于多少？")
    assert "5" in out


def test_agent_no_tool_final_answer():
    p = build_default_pipeline()
    a = ReActAgent(p.llm, [])
    out = a.run("直接给我一句话")
    # run() 会剥离 "Final Answer:" 标记，返回纯答案文本
    assert isinstance(out, str) and len(out) > 0


def test_agent_max_steps():
    p = build_default_pipeline()
    a = ReActAgent(p.llm, [make_calculator()], max_steps=1)
    out = a.run("计算 9*9")
    # 单步内 LLM 发出 Action，未进入 Observation，应优雅结束
    assert isinstance(out, str)
