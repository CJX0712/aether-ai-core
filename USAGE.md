# 使用指南

作者：晨星　｜　版本：0.1.0

---

## 一、命令行

安装后提供 `aether` 命令；也可直接用 `python -m aether.cli`。

| 子命令 | 作用 | 示例 |
|--------|------|------|
| `version` | 打印版本 | `aether version` |
| `ingest` | 写入文档 | `aether ingest --path docs/note.md` 或 `aether ingest --text "苹果使用A19芯片"` |
| `ask` | 基于内置示例语料提问 | `aether ask "iPhone 2026 用的什么芯片？"` |
| `agent` | 运行 ReAct Agent（默认计算器工具） | `aether agent "计算 2+3"` |
| `eval` | 运行评估套件 | `aether eval` |
| `serve` | 启动 REST 服务 | `aether serve --host 127.0.0.1 --port 8000` |

实测输出（`aether eval`）：

```
num_indexed: 5
recall@3: 1.0
recall@5: 1.0
ndcg@5: 1.0
faithfulness: 0.9412
```

## 二、Python API

默认离线链路（零依赖，开箱即用）：

```python
from aether.pipeline import build_default_pipeline, load_sample

p = build_default_pipeline()
load_sample(p)

result = p.ask("iPhone 2026 用的什么芯片？")
print(result["answer"])
for c in result["contexts"]:
    print(c["score"], c["text"][:40])
```

切换到生产实现（Faiss + bge + 云端大模型）：

```python
from aether.pipeline import build_pipeline

p = build_pipeline({
    "embedder": "sentence",
    "store": "faiss",
    "reranker": "local",
    "llm": "openai",
    "llm_base_url": "https://api.openai.com/v1",
    "llm_model": "gpt-4o-mini",
})
p.add_text("你自己的业务文档内容……")
print(p.ask("你的问题")["answer"])
```

本地离线大模型：

```python
from aether.pipeline import build_pipeline

p = build_pipeline({
    "llm": "llama_cpp",
    "llm_model_path": "models/qwen2-7b-instruct-q4_k_m.gguf",
})
```

自定义 Agent 工具：

```python
from aether.agent import ReActAgent, Tool
from aether.pipeline import build_default_pipeline

def lookup(code: str) -> str:
    return {"A19": "3nm 工艺"}.get(code.strip(), "未收录")

p = build_default_pipeline()
agent = ReActAgent(p.llm, [Tool("lookup", "查询芯片代号对应的工艺", lookup)])
print(agent.run("查询 A19 的工艺"))
```

## 三、REST API

| Method | Path | 功能 | 请求体 | 响应 |
|--------|------|------|--------|------|
| GET | `/health` | 健康检查 | — | `{"status","version","author"}` |
| POST | `/v1/ingest` | 写入文本/文档 | `{"texts": [...], "docs": [{"text","meta"}]}` | `{"added": n}` |
| POST | `/v1/ask` | 检索增强问答 | `{"question": str, "k": int}` | `{"answer", "contexts": [{"text","score","doc_id"}]}` |
| POST | `/v1/eval` | 运行评估套件 | — | `{"num_indexed","recall@3","recall@5","ndcg@5","faithfulness",...}` |

示例：

```bash
curl -X POST http://127.0.0.1:8000/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"texts":["苹果iPhone使用A19芯片"]}'

curl -X POST http://127.0.0.1:8000/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"芯片是什么？","k":3}'
```

交互式文档：启动服务后访问 `http://127.0.0.1:8000/docs`。

## 四、评估指标说明

| 指标 | 定义 | 说明 |
|------|------|------|
| `recall@k` | 前 k 条结果中命中的相关文档占比 | 衡量"相关材料是否被召回" |
| `nDCG@k` | 折损累计增益归一化值 | 同时衡量召回与排序质量 |
| `faithfulness` | 答案词与检索上下文的词级重叠比例 | **启发式代理指标**，非严格事实一致性判据 |

评估相关性标签来自内置合成语料的人工标注（查询关于 iPhone 2026 芯片，相关文档索引为 0 / 2 / 4），用于回归验证而非基准评测。

## 五、常见问题

| 现象 | 原因 | 处理 |
|------|------|------|
| 实例化生产 Provider 报 "需要 xxx：pip install ..." | 对应可选依赖未安装 | 按提示安装，或保持默认零依赖链路 |
| `ask` 返回 "(未配置 LLM)" | 管道未注入 LLM | 使用 `build_default_pipeline()` 或显式配置 `llm` |
| E2E 报端口占用 | 默认 8765 被占用 | 设置 `AETHER_E2E_PORT` 换端口 |
| 服务重启后数据为空 | 默认向量库为进程内存储 | 生产切换 Faiss 持久化或外部向量库 |
