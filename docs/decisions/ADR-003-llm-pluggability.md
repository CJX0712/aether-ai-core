# ADR-003: 大模型可插拔，默认确定性 Mock

## Status: Accepted (2026-09-23)

## Background

LLM 是链路中唯一"不可离线、不可确定性复现"的环节。若直接依赖云端或本地大模型，
单测与端到端验证将受网络、密钥、权重与推理耗时影响，破坏可复现性。

## Decision

- 定义 `LLM` 接口（`generate`），运行时注入；
- 默认实现 `MockLLM`：遵循 ReAct 文本协议（Context / Observation / Available tools 三种提示分支），输出确定；
- 生产实现 `LlamaCppLLM`（本地 GGUF，完全离线）与 `OpenAILLM`（任意 /chat/completions 兼容端点，仅依赖 httpx）；
- Agent 仅解析文本协议（Action / Final Answer），与具体大模型解耦，换 LLM 不改编排代码。

## Consequences

正面：离线可验证、结果确定；一套编排代码同时支持本地离线与云端强模型。
负面：Mock 不具备真实语言能力，端到端验证只能证明链路连通性与协议正确性，不能证明生成质量。

## Related ADRs

ADR-001（向量化）、ADR-002（向量库）
