"""命令行入口（typer）。

子命令：
  version  打印版本
  ingest   写入文档（--path 文件 / --text 文本）
  ask      基于内置示例语料提问
  agent    运行 ReAct Agent 示例（默认调用计算器工具）
  eval     运行端到端评估套件
  serve    启动 REST 服务（uvicorn）
"""

from __future__ import annotations

import typer

from .agent.agent import ReActAgent, make_calculator
from .eval.suite import run_suite
from .pipeline import build_default_pipeline, load_sample

app = typer.Typer(help="Aether AI Core 命令行", no_args_is_help=True)


@app.command()
def version() -> None:
    from . import __version__

    typer.echo(f"aether-ai-core {__version__}")


@app.command()
def ingest(
    path: str = typer.Option(None, "--path", help="文档路径，按扩展名自动选择加载器"),
    text: str = typer.Option(None, "--text", help="直接传入文本"),
) -> None:
    p = build_default_pipeline()
    n = 0
    if path:
        from .ingest.loaders import load_auto

        n += p.add_documents([load_auto(path)])
    if text:
        n += p.add_text(text)
    typer.echo(f"已写入 {n} 个 chunk")


@app.command()
def ask(question: str = typer.Argument(..., help="提问内容")) -> None:
    p = build_default_pipeline()
    load_sample(p)
    typer.echo(p.ask(question)["answer"])


@app.command()
def agent(task: str = typer.Argument("计算 2+3 等于多少？", help="Agent 任务")) -> None:
    p = build_default_pipeline()
    a = ReActAgent(p.llm, [make_calculator()])
    typer.echo(a.run(task))


@app.command()
def eval() -> None:
    p = build_default_pipeline()
    for key, val in run_suite(p).items():
        typer.echo(f"{key}: {val}")


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    import uvicorn

    typer.echo(f"启动服务 http://{host}:{port}")
    uvicorn.run("aether.api.app:app", host=host, port=port)


if __name__ == "__main__":
    app()
