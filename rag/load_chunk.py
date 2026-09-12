from pathlib import Path

from docling_core.transforms.chunker import HierarchicalChunker
from langchain_core.documents import Document
from langchain_docling import DoclingLoader


def load_and_chunk(pdf_path: Path) -> list[Document]:
    loader = DoclingLoader(
        file_path=str(pdf_path),
        chunker=HierarchicalChunker(),
    )

    return loader.load()