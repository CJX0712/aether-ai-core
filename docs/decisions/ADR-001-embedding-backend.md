# ADR-001: 向量化后端默认采用零依赖哈希实现，生产可切换 bge

## Status: Accepted (2026-09-23)

## Background

检索链路依赖向量化，但生产级语义模型（sentence-transformers + torch）体积大、安装慢、首次使用需下载权重，
会让"干净环境一键复现"和"无网络验证"两个目标同时失效。

## Decision

- 定义 `Embedder` 接口，运行时注入实现；
- 默认实现 `HashEmbedder`（中文字符 bigram + 英文词哈希，L2 归一化），仅依赖标准库；
- 生产实现 `SentenceEmbedder`（BAAI/bge-small-zh-v1.5）通过 `build_pipeline({"embedder": "sentence"})` 切换，lazy import。

## Consequences

正面：默认链路离线可跑、单测无需网络、CI 稳定；哈希向量足以驱动检索与重排的回归验证。
负面：哈希向量不具备真实语义泛化能力，同义不同词召回弱于 bge；生产场景必须切换实现。

## Related ADRs

ADR-002（向量库）、ADR-003（大模型）
