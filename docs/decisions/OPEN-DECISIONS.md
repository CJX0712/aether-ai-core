# 悬而未决登记册（OPEN-DECISIONS）

> 只追加、就地关闭（OPEN -> RESOLVED 并补 Resolution）。作者：晨星

| Date | Source | Open Item | Related Constraints | Current Leaning | Blocked By | Resolves When | Status |
|------|--------|-----------|---------------------|-----------------|------------|---------------|--------|
| 2026-09-23 | Phase 1 | 向量库是否需要持久化 | 默认进程内存储重启失效；持久化会引入配置与版本兼容成本 | MVP 保持进程内，生产切 Faiss 持久化或外部向量库 | 等待生产部署需求 | 明确生产部署形态后 | OPEN |
| 2026-09-23 | Phase 1 | 精排是否引入真实交叉编码器 | bge-reranker 需下载权重，CPU 推理慢 | MVP 用启发式重排，接口预留 | 需要更高质量排序且有算力预算 | 有线上排序质量指标后 | OPEN |
| 2026-09-23 | Phase 1 | 是否提供前端演示界面 | 当前交付聚焦系统与工程链路 | 暂不提供，保持零前端依赖 | 无明确展示需求 | 需要可视化演示时 | OPEN |
| 2026-09-23 | Phase 1 | 可选依赖是否纳入 CI 覆盖 | torch / llama-cpp 体积大、安装慢 | CI 只覆盖核心锁版依赖，可选依赖文档化 | 构建机资源 | 有自建 Runner 后 | OPEN |

## 已决项

| Date | Decision | Resolution | Status |
|------|----------|------------|--------|
| 2026-09-23 | 默认链路零依赖可离线 | 采纳 Protocol + 注入零依赖实现（见 ADR-001/002/003） | RESOLVED |
| 2026-09-23 | 依赖必须锁版可一键复现 | 采纳 `requirements.lock.txt` 精确锁定全部传递依赖 | RESOLVED |
| 2026-09-23 | 禁止 emoji 作功能图标 | 纳入 P0 门禁 `tools/scan_emoji.py`，CI 强制 | RESOLVED |
