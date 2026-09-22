# Spec - Aether AI Core v0.1.0

> 生成日期：2026-09-23
> 状态：已确认
> 作者：晨星

---

## 1. 产品定义

- **一句话描述**：模块化端到端 AI 系统框架，把文档摄取到检索增强生成与工具调用的链路切分为职责单一、可独立验证、可组合的模块。
- **目标用户**：需要在自有环境快速搭起可运行、可复现 AI 系统并逐步替换生产组件的工程团队。
- **核心问题**：AI 系统各组件强耦合、重型依赖装不上就整体不可用、无法在无网环境验证链路正确性。

## 2. MVP 范围（锁定）

| 优先级 | 功能 | 验收标准摘要 |
|--------|------|-------------|
| P0 | 文档摄取与切分 | 长文本产生多 chunk，重叠窗口保留边界 |
| P0 | 向量化 | 同一文本编码确定性一致，向量 L2 归一化 |
| P0 | 向量库 | 增查一致，相似度排序正确 |
| P0 | 检索召回 | 内置语料 recall@5 = 1.0 |
| P0 | 精排 | 相关 chunk 排序优于无关 chunk |
| P0 | 大生成成 | 可注入实现，默认确定性 Mock |
| P0 | Agent 编排 | 能解析 Action、执行工具、基于 Observation 收敛 |
| P0 | REST 网关 | /health、/v1/ingest、/v1/ask、/v1/eval 均 200 且结构正确 |
| P0 | 离线可验证 | 无网络、无 API Key 下单测与 E2E 全绿 |
| P1 | 生产 Provider | Faiss / bge / llama.cpp / OpenAI 兼容，lazy import |

## 3. 明确不做（Out-of-Scope）

| 不做的功能 | 原因 | 何时考虑 |
|------------|------|----------|
| 向量库持久化 | MVP 采用进程内存储，保持零配置可跑 | 生产接入外部向量库时 |
| 分布式检索 | 单机规模内无收益 | 数据量超单机内存时 |
| 多模态（图/音） | 依赖重，CPU 环境难以验证 | 有明确需求且算力到位时 |
| 前端界面 | 本交付聚焦系统与工程链路 | 需要可视化演示时 |
| 模型微调 | 目标是复用开源模型而非自研训练 | 有专属数据且收益明确时 |

## 4. 技术架构（锁版）

| 层 | 技术 | 版本 | 锁定原因 |
|----|------|------|----------|
| 运行时 | Python | 3.13.14（要求 >=3.11） | 本机验证版本 |
| 数值 | numpy | 2.5.3 | 向量计算 |
| 向量库（生产） | faiss-cpu | 1.15.1 | 精确/近似检索 |
| 服务 | fastapi | 0.141.1 | REST 网关 |
| 数据校验 | pydantic | 2.13.5 | 请求/响应模型 |
| HTTP 客户端 | httpx | 0.28.1 | 云端大模型调用 |
| ASGI 服务器 | uvicorn | 0.53.0 | 服务进程托管 |
| CLI | typer | 0.27.2 | 命令行 |
| 测试 | pytest | 9.1.1 | 单测 |

完整传递依赖见 `requirements.lock.txt`。

## 5. API 端点清单

| Method | Path | 功能 | 认证 | 请求体 | 响应体 |
|--------|------|------|------|--------|--------|
| GET | `/health` | 健康检查 | 无 | — | `{status, version, author}` |
| POST | `/v1/ingest` | 写入文本/文档 | 无 | `{texts?: string[], docs?: [{text, meta}]}` | `{added: int}` |
| POST | `/v1/ask` | 检索增强问答 | 无 | `{question: string, k?: int}` | `{answer: string, contexts: [{text, score, doc_id}]}` |
| POST | `/v1/eval` | 运行评估套件 | 无 | — | `{num_indexed, recall@3, recall@5, ndcg@5, faithfulness, answer, ...}` |

## 6. 数据模型

无关系型数据表。向量库以 `(id, vector, meta)` 三元组存储，meta 内携带原文 `text` 与 `doc_id`；默认进程内字典，生产可替换为 Faiss 索引。

| 概念 | 字段 | 说明 |
|------|------|------|
| Document | text, meta, doc_id | 原始文档 |
| Chunk | text, meta, chunk_id, doc_id, score | 检索单元 |
| VectorStore 记录 | id, vector, meta{text, doc_id, ...} | 向量与元数据 |

## 7. 页面清单

无前端页面。能力通过 REST 与 CLI 暴露。

## 8. 设计 Token

无 UI 界面。工程侧约束：禁止以 emoji 表情充当功能图标（由 `tools/scan_emoji.py` 强制）；文档统一使用 `[PASS]/[FAIL]` 文本标记。

## 9. 验收标准（EARS 格式）

| 编号 | 功能 | 验收标准 | 优先级 |
|------|------|----------|--------|
| AC-01 | 摄取 | When 输入文本长度超过 chunk_size，系统**必须**产生多个 chunk 且相邻块保留重叠窗口 | P0 |
| AC-02 | 向量化 | When 对同一文本重复编码，系统**必须**返回完全一致且 L2 归一化的向量 | P0 |
| AC-03 | 检索 | When 使用内置语料查询，系统**必须**使 recall@5 >= 0.99 | P0 |
| AC-04 | 精排 | When 候选含相关与无关 chunk，系统**必须**将相关 chunk 排在更前 | P0 |
| AC-05 | Agent | When LLM 输出符合 Action 协议，系统**必须**执行对应工具并把 Observation 喂回循环 | P0 |
| AC-06 | Agent | When LLM 输出 Final Answer，系统**必须**剥离标记并返回纯答案文本 | P0 |
| AC-07 | API | When 请求 /health，系统**必须**返回 200 且 status = ok | P0 |
| AC-08 | API | When 请求 /v1/eval，系统**必须**在全新管道上运行以保证结果确定性 | P0 |
| AC-09 | 离线 | While 无网络与无 API Key，系统**必须**仍能完成单测与端到端验证 | P0 |
| AC-10 | 门禁 | When 仓库中任何文本文件含 emoji，门禁**必须**失败并非零退出 | P0 |

## 10. 边界与约束

- 默认向量库为进程内存储，服务重启后数据失效
- 默认大模型为确定性 Mock，仅保证链路可跑，不具备真实语言能力
- 生产 Provider 为 lazy import，未安装可选依赖时仅对应能力不可用
- 评估指标 `faithfulness` 为词级启发式代理，不代表严格事实一致性
- 单机规模，不含分布式与持久化

## 11. 内嵌已知坑

| 坑 | 根因 | 修法 |
|----|------|------|
| PowerShell 把整串包变量当单参数传给 pip | `$pkgs` 字符串被作为单一 argv 传入 | 依赖逐个作为独立参数传入 |
| 后台任务与前景 shell 文件系统隔离 | 沙箱各调用视图不一致 | 关键步骤写成自包含单条命令，不跨调用依赖中间产物 |
| PowerShell `Out-File` 默认 UTF-16 导致日志被识别为二进制 | 编码默认值 | 显式 `-Encoding utf8`；中文输出另设 `PYTHONIOENCODING=utf-8` |
| 评估端点复用含数据管道导致 doc_id 重复、指标失真 | 运行期状态污染 | 评估在全新管道上运行 |
| 测试数据短于切分阈值，多分块路径未被覆盖 | 样例过短 | 测试数据显式超过 chunk_size |

## 12. 端到端验证步骤

```bash
# 1. 安装（锁版）
pip install -r requirements.lock.txt && pip install -e .

# 2. 单元测试（离线）
pytest tests                 # 期望：20 passed

# 3. 端到端（拉起真实服务进程）
python tools/run_e2e.py      # 期望：通过 8 / 失败 0

# 4. P0 门禁
python tools/scan_emoji.py   # 期望：P0 门禁通过，0 处 emoji

# 5. 一键
make verify
```

## 13. 变更记录

| 日期 | 变更内容 | 原因 | 影响范围 |
|------|----------|------|----------|
| 2026-09-23 | 初版：10 模块 + 零依赖默认链路 + 生产 Provider + 评估与门禁 | 交付可运行、可复现的 AI 系统骨架 | 全部 |
