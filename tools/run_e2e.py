"""自包含端到端验证脚本。

覆盖两条通道：
1. 进程内链路：摄取 -> 向量化 -> 入库 -> 检索 -> 重排 -> 生成 -> Agent -> 评估；
2. 真实进程：拉起 uvicorn 服务，轮询 /health 直至 200，再跑核心成功流。

不依赖 docker / curl，Windows 下用 taskkill 兜底清理子进程。
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

import httpx

HOST = "127.0.0.1"
PORT = int(os.environ.get("AETHER_E2E_PORT", "8765"))
BASE = f"http://{HOST}:{PORT}"

_results: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    _results.append((name, bool(cond), detail))


def wait_health(base: str, timeout: float = 30.0):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = httpx.get(f"{base}/health", timeout=2.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        time.sleep(0.5)
    return None


def run_inproc() -> None:
    from aether.agent.agent import ReActAgent, make_calculator
    from aether.eval.suite import run_suite
    from aether.pipeline import build_default_pipeline, load_sample

    p = build_default_pipeline()
    n = load_sample(p)
    check("pipeline ingest", n == 5, f"num_indexed={n}")

    r = p.ask("iPhone 2026 用的什么芯片？")
    check("pipeline ask", len(r["contexts"]) > 0 and r["answer"].strip() != "", f"answer={r['answer'][:40]}")

    a = ReActAgent(p.llm, [make_calculator()])
    out = a.run("计算 2+3")
    check("agent calculator", "5" in out, f"out={out}")

    rep = run_suite(p)
    check("eval recall@5>=0.99", rep["recall@5"] >= 0.99, f"recall={rep['recall@5']}")


def run_server() -> None:
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "aether.api.app:app", "--host", HOST, "--port", str(PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        ok = wait_health(BASE)
        check("server /health", ok is not None and ok.get("status") == "ok", str(ok))
        if not ok:
            return

        rr = httpx.post(f"{BASE}/v1/ingest", json={"texts": ["苹果iPhone使用A19芯片"]}, timeout=15)
        check("server /v1/ingest", rr.status_code == 200 and rr.json().get("added", 0) >= 1, str(rr.json()))

        rr = httpx.post(f"{BASE}/v1/ask", json={"question": "芯片是什么？", "k": 3}, timeout=15)
        check("server /v1/ask", rr.status_code == 200 and len(rr.json().get("contexts", [])) > 0)

        rr = httpx.post(f"{BASE}/v1/eval", timeout=30)
        check("server /v1/eval", rr.status_code == 200 and rr.json().get("recall@5", 0) >= 0.99)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            subprocess.run(
                ["taskkill", "/pid", str(proc.pid), "/t", "/f"],
                capture_output=True,
            )


def main() -> None:
    run_inproc()
    run_server()

    passed = sum(1 for _, ok, _ in _results if ok)
    failed = len(_results) - passed
    for name, ok, detail in _results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")
    print(f"通过: {passed} / 失败: {failed}")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
