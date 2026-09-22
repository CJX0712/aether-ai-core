"""可选生产 Provider 冒烟：模块可导入（重型依赖均为 lazy import）。"""

import importlib

_MODULES = [
    "aether.providers.faiss_store",
    "aether.providers.sentence_embedder",
    "aether.providers.llama_cpp_llm",
    "aether.providers.openai_llm",
]


def test_optional_modules_import():
    """重型依赖延迟导入，未安装也不应阻塞模块加载。"""
    for name in _MODULES:
        importlib.import_module(name)


def test_openai_provider_instantiable():
    """httpx 已安装，OpenAI 兼容 Provider 可实例化。"""
    from aether.providers.openai_llm import OpenAILLM

    llm = OpenAILLM(api_key="test", base_url="https://example.invalid/v1", model="m")
    assert llm.model == "m"
