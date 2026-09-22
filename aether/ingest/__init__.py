"""摄取层公开接口。"""

from .loaders import load_auto, load_docx, load_markdown, load_pdf, load_text
from .splitter import RecursiveCharacterSplitter

__all__ = [
    "load_text",
    "load_markdown",
    "load_pdf",
    "load_docx",
    "load_auto",
    "RecursiveCharacterSplitter",
]
