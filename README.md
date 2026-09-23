# Aether AI Core

<p align="center">
  <a href="https://github.com/CJX0712/aether-ai-core/actions/workflows/ci.yml"><img src="https://github.com/CJX0712/aether-ai-core/actions/workflows/ci.yml/badge.svg" alt="ci"></a>
  <a href="https://github.com/CJX0712/aether-ai-core/releases"><img src="https://img.shields.io/github/v/release/CJX0712/aether-ai-core?sort=semver" alt="release"></a>
  <a href="https://github.com/CJX0712/aether-ai-core/blob/main/LICENSE"><img src="https://img.shields.io/github/license/CJX0712/aether-ai-core" alt="license"></a>
  <img src="https://img.shields.io/badge/author-%E6%99%A8%E6%98%9F-1f6feb" alt="author">
</p>

> 模块化端到端 AI 系统框架（RAG + Agent）。
> 复用业界领先开源成果，按单一职责切分 AI 功能模块；每模块接口明确、可独立验证、可组合成完整可运行链路。

作者：晨星　｜　版本：0.1.0　｜　许可：MIT

---

## 一句话定位

一套**可插拔、可离线验证、可一键复现**的 AI 系统骨架：把"文档摄取到向量召回再到生成与工具调用"这条链路切成 10 个职责单一的模块，每个模块既能单独跑单测，也能拼成完整系统。

## 核心特性

| 特性 | 说明 |
|------|------|
| 单一职责模块 | 摄取 / 向量化 / 向量库 / 检索 / 重排 / 大模型 / Agent 编排 / API 网关 / 评估 / CLI |
| 接口即契约 | 所有外部能力抽象为 Protocol，运行时注入实现，模块间零硬耦合 |
| 离线可验证 | 默认注入零依赖实现，无网络、无 API Key、无 GPU 也能跑通全链路 |
| 生产可插拔 | 一行配置切换 Faiss / bge 向量化 / llama.cpp 本地模型 / OpenAI 兼容 API |
| 依赖锁版 | `requirements.lock.txt` 精确锁定全部传递依赖，干净环境一键复现 |
| P0 门禁 | 内置 emoji 扫描，禁止以表情充当功能图标 |

## 模块划分

| 模块 | 职责 | 核心接口 | 默认实现（零依赖） | 生产可切换 |
|------|------|----------|-------------------|-----------|
| `aether.ingest` | 文档加载与切分 | `load_auto()` / `RecursiveCharacterSplitter.split()` | 文本、Markdown | PDF（pdfplumber）、DOCX（python-docx） |
| `aether.providers.local` | 向量化 | `Embedder.embed()` | `HashEmbedder`（中文 bigram 哈希） | `SentenceEmbedder`（bge-small-zh） |
| `aether.providers` | 向量库 | `VectorStore.add()/search()` | `MemoryVectorStore`（余弦） | `FaissVectorStore`（faiss-cpu） |
| `aether.retrieve` | 向量召回 | `Retriever.retrieve()` | `VectorRetriever` | 同（换 Embedder/Store 即可） |
| `aether.providers` | 精排 | `Reranker.rerank()` | `HeuristicReranker`（BM25 风格） | 交叉编码器（同接口扩展） |
| `aether.providers` | 大模型 | `LLM.generate()` | `MockLLM`（确定性） | `LlamaCppLLM` / `OpenAILLM` |
| `aether.agent` | 编排 | `Agent.run()` | `ReActAgent` + 工具注册 | 同（仅换 LLM） |
| `aether.api` | 服务网关 | REST `/v1/*` | FastAPI | 同 |
| `aether.cli` | 命令行 | `aether <子命令>` | typer | 同 |
| `aether.eval` | 评估 | `run_suite()` | recall@k / nDCG / faithfulness | 同 |

## 快速开始（干净环境一键复现）

Linux / macOS：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock.txt
pip install -e .
pytest tests
python tools/run_e2e.py
```

Windows（PowerShell）：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m pytest tests
.\.venv\Scripts\python.exe tools\run_e2e.py
```

以上命令**无需任何 API Key、无需联网**，即可完成全链路验证。

## 验证结果（本机实测）

| 项目 | 结果 |
|------|------|
| 单元测试 | 20 / 20 通过（离线） |
| 端到端验证 | 8 / 8 通过（含真实 uvicorn 进程 + /health 轮询） |
| 检索 recall@3 | 1.0 |
| 检索 recall@5 | 1.0 |
| 检索 nDCG@5 | 1.0 |
| 生成忠实度（词级启发式） | 0.9412 |
| P0 emoji 门禁 | 0 处违规 |

## 目录结构

```
aether-ai-core/
├── aether/                 源码
│   ├── core/               数据契约 + 接口协议（Protocol）
│   ├── providers/          实现（local 零依赖 / faiss / bge / llama.cpp / OpenAI 兼容）
│   ├── ingest/             加载器 + 递归切分器
│   ├── retrieve/           向量召回
│   ├── agent/              ReAct 编排 + 工具
│   ├── api/                FastAPI 网关
│   ├── eval/               指标与评估套件
│   ├── pipeline.py         管道装配与工厂
│   └── cli.py              命令行
├── tests/                  pytest（离线全绿）
├── tools/                  run_e2e.py（端到端） / scan_emoji.py（P0 门禁）
├── docs/                   SPEC / openapi / 架构决策记录
├── requirements.lock.txt   精确锁版依赖
├── Dockerfile / Makefile   构建与一键验证
└── .github/workflows/ci.yml
```

## 文档

- [架构说明](ARCHITECTURE.md)
- [部署指南](DEPLOY.md)
- [使用指南](USAGE.md)
- [规格契约](docs/SPEC.md)
- [架构决策记录](docs/decisions/)

## 许可

MIT License，Copyright (c) 2026 晨星。
