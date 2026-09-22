# 部署指南

作者：晨星　｜　版本：0.1.0

---

## 一、环境要求

| 项 | 要求 |
|----|------|
| Python | 3.11 及以上（本机验证 3.13.14） |
| 操作系统 | Windows / Linux / macOS |
| GPU | 非必需；默认链路纯 CPU 运行 |
| 网络 | 默认链路不需要；仅安装可选生产依赖时需要 |
| API Key | 默认链路不需要；仅使用云端大模型时需要 |

## 二、本地部署（推荐起步）

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.lock.txt
pip install -e .
```

启动服务：

```bash
aether serve --host 127.0.0.1 --port 8000
# 或
uvicorn aether.api.app:app --host 127.0.0.1 --port 8000
```

验证：

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok","version":"0.1.0","author":"晨星"}
```

一键全量验证（单测 + 端到端 + P0 门禁）：

```bash
make verify
```

## 三、容器部署

```bash
docker build -t aether-ai-core:0.1.0 .
docker run --rm -p 8000:8000 aether-ai-core:0.1.0
```

镜像内置 HEALTHCHECK，会轮询本机 `/health`；构建过程只安装 `requirements.lock.txt`，保证可复现。

## 四、可选生产依赖

核心链路无需以下依赖；按需安装以获得更高检索/生成质量。

| 能力 | 安装命令 | 生效方式 |
|------|----------|----------|
| bge 语义向量化 | `pip install -e ".[embed]"` | `build_pipeline({"embedder": "sentence"})` |
| 本地大模型（GGUF） | `pip install -e ".[local-llm]"` | `build_pipeline({"llm": "llama_cpp", "llm_model_path": "<path>.gguf"})` |
| PDF / DOCX 解析 | `pip install -e ".[docs]"` | `load_auto()` 自动按扩展名路由 |

说明：`[embed]` 与 `[local-llm]` 体积较大，且首次使用需下载模型权重，未包含在 CI 覆盖范围内；核心链路与 CI 只依赖 `requirements.lock.txt`。

## 五、配置与环境变量

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | 云端大模型鉴权（使用 OpenAI 兼容端点时） | 无 |
| `AETHER_E2E_PORT` | 端到端验证脚本拉起服务的端口 | 8765 |

服务默认使用零依赖链路，因此开箱即用、无配置项强制要求。

## 六、健康检查与回滚

| 项 | 做法 |
|----|------|
| 健康检查 | `GET /health` 返回 `{"status":"ok"}`；容器已内置 HEALTHCHECK |
| 依赖冻结 | 始终使用 `requirements.lock.txt`，避免漂移 |
| 回滚 | 容器按镜像 tag 回滚（`aether-ai-core:0.1.0`）；源码回滚到对应 commit |
| 数据备份 | 默认向量库为进程内存储，重启即失效；生产请替换为 Faiss 持久化或外部向量库 |
