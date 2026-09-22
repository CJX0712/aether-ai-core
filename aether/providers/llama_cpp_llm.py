"""llama.cpp 本地大模型实现（lazy import llama-cpp-python）。

完全离线、零密钥；首次需下载 GGUF 权重。替代 MockLLM，接口一致。
"""

from __future__ import annotations

from ..core.protocols import LLM
from ..core.types import Message


class LlamaCppLLM(LLM):
    def __init__(
        self,
        model_path: str,
        n_ctx: int = 2048,
        n_threads: int = 4,
        system_prompt: str | None = None,
    ) -> None:
        try:
            from llama_cpp import Llama
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "需要 llama-cpp-python：pip install llama-cpp-python"
            ) from exc
        self._llm = Llama(model_path=model_path, n_ctx=n_ctx, n_threads=n_threads)
        self.system_prompt = system_prompt
        self.model_path = model_path

    def generate(self, prompt: str, history: list[Message] | None = None, **kw: object) -> str:
        messages: list[dict] = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        for h in history or []:
            messages.append({"role": h.role, "content": h.content})
        messages.append({"role": "user", "content": prompt})
        out = self._llm.create_chat_completion(
            messages=messages, max_tokens=int(kw.get("max_tokens", 512))
        )
        return out["choices"][0]["message"]["content"]


__all__ = ["LlamaCppLLM"]
