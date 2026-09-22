"""摄取模块单测。"""

from aether.core.types import Document
from aether.ingest.loaders import load_text
from aether.ingest.splitter import RecursiveCharacterSplitter


def test_splitter_multi_chunk():
    # 测试数据显式超过阈值，确保多分块路径被覆盖
    text = "。".join([f"这是第{i}段关于苹果公司的产品信息，包含芯片与续航细节说明" for i in range(20)])
    sp = RecursiveCharacterSplitter(chunk_size=50, chunk_overlap=10)
    chunks = sp.split(Document(text=text))
    assert len(chunks) > 1
    # 重叠窗口应保留上下文：后续块以先前块尾端开头
    assert chunks[1].text.startswith(chunks[0].text[-10:])


def test_splitter_short_text_single_chunk():
    sp = RecursiveCharacterSplitter(chunk_size=200)
    chunks = sp.split(Document(text="一句短文本。"))
    assert len(chunks) == 1


def test_loader_text(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("hello world 中文", encoding="utf-8")
    d = load_text(str(f))
    assert "hello world" in d.text
    assert d.doc_id == str(f)
