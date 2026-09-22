"""递归字符切分器（零依赖）。

按分隔符优先级递归切分，长文档落入多 chunk；支持重叠窗口以保留上下文边界。
"""

from __future__ import annotations

from ..core.types import Chunk, Document


class RecursiveCharacterSplitter:
    def __init__(
        self,
        chunk_size: int = 200,
        chunk_overlap: int = 40,
        separators: list[str] | None = None,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or [
            "\n\n", "\n", "。", "！", "？", ".", "!", "?", "；", ";", "，", ",", " ", ""
        ]

    def split(self, doc: Document) -> list[Chunk]:
        pieces = self._split_recursive(doc.text)
        out: list[Chunk] = []
        prev_tail = ""
        for i, p in enumerate(pieces):
            base = p.strip()
            if not base:
                continue
            if i > 0 and self.chunk_overlap > 0 and prev_tail:
                base = prev_tail + base
            out.append(Chunk(text=base, meta=dict(doc.meta), doc_id=doc.doc_id))
            prev_tail = p.strip()[-self.chunk_overlap:] if self.chunk_overlap > 0 else ""
        return out

    def _split_recursive(self, text: str) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text]
        for sep in self.separators:
            if sep and sep in text:
                parts = text.split(sep)
                docs: list[str] = []
                buf = ""
                for p in parts:
                    if not p:
                        continue
                    cand = (buf + p + sep) if buf else (p + sep)
                    if len(cand) <= self.chunk_size:
                        buf = cand
                    else:
                        if buf:
                            docs.append(buf)
                        buf = p + sep
                if buf:
                    docs.append(buf)
                if len(docs) > 1:
                    return docs
        return [text[i : i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]


__all__ = ["RecursiveCharacterSplitter"]
