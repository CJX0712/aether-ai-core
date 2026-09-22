# ADR-002: 向量库默认进程内余弦，生产切换 Faiss

## Status: Accepted (2026-09-23)

## Background

Faiss 提供生产级检索能力，但在受限环境安装并非总能成功；若把它设为硬依赖，
一旦装不上会导致整个系统不可用，也让离线验证失去意义。

## Decision

- 定义 `VectorStore` 接口（`add` / `search` / `get`），运行时注入；
- 默认实现 `MemoryVectorStore`（进程内字典 + 余弦相似度），零依赖；
- 生产实现 `FaissVectorStore`（IndexFlatIP，向量写入时归一化使内积等价于余弦），lazy import；
- 通过 `build_pipeline({"store": "faiss"})` 切换。

## Consequences

正面：核心链路零依赖可验证；Faiss 接入无需改动调用方。
负面：进程内存储不持久化、重启失效，且为线性扫描，规模增长后需替换为 Faiss 或外部向量库。

## Related ADRs

ADR-001（向量化）、ADR-003（大模型）
