"""OpenAI 兼容大模型实现（仅依赖 httpx，无需官方 SDK）。

可对接 OpenAI / DeepSeek / 通义 / 本地 vLLM 等任意 /chat/completions 兼容端点。
替代 MockLLM，接口一致。
"""

from __future__ import annotations

import os

from ..core.protocols import LLM
from ..core.types import Message


class OpenAILLM(LLM):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        timeout: float = 60.0,
    ) -> None:
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover
            raise ImportError("需要 httpx：pip install httpx") from exc
        self._httpx = httpx
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def generate(self, prompt: str, history: list[Message] | None = None, **kw: object) -> str:
        messages = [{"role": h.role, "content": h.content} for h in (history or [])]
        messages.append({"role": "user", "content": prompt})
        resp = self._httpx.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": float(kw.get("temperature", 0.2)),
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


__all__ = ["OpenAILLM"]
