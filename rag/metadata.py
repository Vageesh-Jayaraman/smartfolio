from langchain_core.documents import Document

def add_metadata(
        chunks: list[Document],
        company: str,
        period: str,
        document_type: str,
) -> list[Document]:

    for chunk in chunks:
        chunk.metadata.update(
            {
                "company": company,
                "period": period,
                "document_type": document_type,
            }
        )

    return chunks