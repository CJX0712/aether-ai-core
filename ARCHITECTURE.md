# 系统架构

作者：晨星　｜　版本：0.1.0

---

## 一、总览

Aether 是一条可拆装的 AI 流水线。每个环节是一个职责单一的模块，模块之间只通过接口（Protocol）通信，实现在装配时注入。

```
   原始文档
      │
      ▼
  ┌────────────┐
  │  ingest    │  加载（txt/md/pdf/docx）+ 递归切分
  └────────────┘
      │  Chunk
      ▼
  ┌────────────┐
  │  embedder  │  文本 -> 向量（HashEmbedder / bge）
  └────────────┘
      │  vector
      ▼
  ┌────────────┐
  │   store    │  向量索引（Memory / Faiss）
  └────────────┘
      │
      ▼
  ┌────────────┐
  │ retriever  │  查询 -> 召回 top-k
  └────────────┘
      │  候选 Chunk
      ▼
  ┌────────────┐
  │  reranker  │  精排（BM25 风格 / 交叉编码器）
  └────────────┘
      │  精排后 Chunk
      ▼
  ┌────────────┐        ┌────────────┐
  │    LLM     │◄──────►│   agent    │  ReAct 循环 + 工具调用
  └────────────┘        └────────────┘
      │  答案
      ▼
  ┌────────────┐   ┌────────────┐
  │  api / cli │   │    eval    │  指标回归
  └────────────┘   └────────────┘
```

## 二、分层与职责

| 层 | 目录 | 职责 | 是否含业务逻辑 |
|----|------|------|----------------|
| 契约层 | `aether/core` | 数据类（Document/Chunk/Message）+ 接口 Protocol | 否 |
| 实现层 | `aether/providers` | 各接口的具体实现 | 是（可替换） |
| 能力层 | `aether/ingest`、`aether/retrieve`、`aether/agent` | 单一能力模块 | 是 |
| 装配层 | `aether/pipeline.py` | 组合模块、提供工厂 | 仅装配 |
| 接入层 | `aether/api`、`aether/cli` | REST / 命令行 | 仅接入 |
| 验证层 | `aether/eval`、`tests`、`tools` | 指标与端到端验证 | 否 |

装配层只做依赖注入，不含业务逻辑；接入层只做协议转换，不含业务逻辑。

## 三、接口契约

| 接口 | 方法 | 语义 |
|------|------|------|
| `Embedder` | `embed(texts) -> list[list[float]]` | 文本批量编码为向量 |
| `VectorStore` | `add(vectors, metas, ids)` / `search(vec, k) -> [(id, score)]` / `get(id)` | 向量增删查，score 越大越相似 |
| `Reranker` | `rerank(query, chunks, top_n) -> list[Chunk]` | 候选精排，返回新 Chunk（含新 score） |
| `LLM` | `generate(prompt, history) -> str` | 生成文本 |
| `Retriever` | `retrieve(query, k) -> list[Chunk]` | 检索 top-k |
| `Agent` | `run(task, max_steps) -> str` | 执行任务并返回结果 |

## 四、Provider 切换矩阵

| 能力 | 默认（零依赖、离线） | 生产实现 | 切换方式 |
|------|---------------------|----------|----------|
| 向量化 | `HashEmbedder` 中文 bigram 哈希，L2 归一化 | `SentenceEmbedder`（BAAI/bge-small-zh-v1.5） | `build_pipeline({"embedder": "sentence"})` |
| 向量库 | `MemoryVectorStore` 进程内余弦 | `FaissVectorStore`（IndexFlatIP） | `build_pipeline({"store": "faiss"})` |
| 大模型 | `MockLLM` 确定性应答 | `LlamaCppLLM`（本地 GGUF）/ `OpenAILLM`（任意兼容端点） | `build_pipeline({"llm": "llama_cpp" \| "openai"})` |
| 文档 | txt / md | pdf（pdfplumber）、docx（python-docx） | `load_auto()` 按扩展名自动选择 |

所有重型依赖均为 **lazy import**：未安装时不影响模块加载与核心链路运行，仅在实例化对应 Provider 时给出明确的安装提示。

## 五、设计原则

| 原则 | 落地方式 |
|------|----------|
| 单一职责 | 一个模块只做一件事（切分、编码、索引、召回、精排、生成、编排各自独立） |
| 依赖倒置 | 模块只依赖 Protocol，具体实现运行时注入 |
| 可独立验证 | 每个模块有对应单测；零依赖实现使单测无需网络 |
| 离线可运行 | 默认链路零外部服务，`pytest` 与 E2E 在无网环境全绿 |
| 惰性依赖 | 重型库延迟导入，避免"装不上就整体不可用" |
| 契约稳定 | 接口签名即契约，替换实现不动调用方 |

## 六、可验证不变量

| 不变量 | 验证位置 |
|--------|----------|
| 向量化确定性：同文本两次编码结果完全一致且 L2 归一化 | `tests/test_local_providers.py` |
| 语义相近文本的余弦相似度显著高于无关文本 | `tests/test_local_providers.py` |
| 检索结果中相关文档排序优于无关文档（recall@5 = 1.0、nDCG@5 = 1.0） | `tests/test_pipeline.py`、`aether/eval/suite.py` |
| Agent 能正确解析 Action、执行工具并基于 Observation 收敛到最终答案 | `tests/test_agent.py` |
| 切分器在长文本（超过阈值）下产生多块，且重叠窗口保留上下文边界 | `tests/test_ingest.py` |
| API 端点健康、摄取、问答、评估四条流均返回 200 且结构正确 | `tests/test_api.py`、`tools/run_e2e.py` |
