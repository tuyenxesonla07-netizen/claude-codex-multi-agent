# tools/rag/text_splitter.py

"""
递归字符文本分块器。

将长文本切分为适合 embedding 和检索的小块。
支持按段落、句子、字符多级分割，保持上下文连贯性。
"""

from dataclasses import dataclass, field
from typing import List, Optional
import re


@dataclass
class DocumentChunk:
    """单个文档块"""
    content: str
    metadata: dict = field(default_factory=dict)
    chunk_index: int = 0
    document_id: str = ""
    source: str = ""           # 来源（文件名/URL）
    position: int = 0          # 在原文中的位置（字符偏移）


class TextSplitter:
    """
    递归字符文本分块器。

    按优先级依次尝试分隔符：段落 → 换行 → 句子 → 空格 → 字符。
    确保每个块不超过 chunk_size，相邻块之间有 chunk_overlap 重叠。

    用法:
        splitter = TextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_text("长文本内容...", metadata={"source": "doc.pdf"})
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200,
                 separators: List[str] = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", "。", "！", "？", ". ", " ", ""]

    def split_text(self, text: str, metadata: dict = None,
                   document_id: str = "", source: str = "") -> List[DocumentChunk]:
        """将文本切分为 DocumentChunk 列表"""
        if not text.strip():
            return []

        raw_chunks = self._recursive_split(text, self.separators)
        chunks = []
        position = 0
        for idx, content in enumerate(raw_chunks):
            if content.strip():
                chunks.append(DocumentChunk(
                    content=content,
                    metadata=metadata or {},
                    chunk_index=idx,
                    document_id=document_id,
                    source=source,
                    position=position,
                ))
                position += len(content)
        return chunks

    def split_document(self, content: str, metadata: dict = None,
                       document_id: str = "", source: str = "") -> List[DocumentChunk]:
        """split_text 的别名，语义更清晰"""
        return self.split_text(content, metadata, document_id, source)

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """递归按分隔符切分"""
        if len(text) <= self.chunk_size:
            return [text]

        if not separators:
            return self._force_split(text)

        sep = separators[0]
        remaining = separators[1:]
        parts = text.split(sep) if sep else list(text)

        chunks = []
        current = ""
        for part in parts:
            candidate = (current + sep + part) if current else part
            if len(candidate) > self.chunk_size and current:
                chunks.append(current)
                # overlap: 保留前一个 chunk 末尾
                overlap_text = current[-self.chunk_overlap:] if self.chunk_overlap > 0 else ""
                current = overlap_text + part
            else:
                current = candidate
        if current:
            chunks.append(current)

        # 对超长 chunk 递归用下一级分隔符继续切
        if remaining:
            refined = []
            for chunk in chunks:
                if len(chunk) > self.chunk_size:
                    refined.extend(self._recursive_split(chunk, remaining))
                else:
                    refined.append(chunk)
            chunks = refined

        return chunks

    def _force_split(self, text: str) -> List[str]:
        """强制按字符位置切分（兜底）"""
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunks.append(text[start:end])
            start = end - self.chunk_overlap if end < len(text) else end
        return chunks
