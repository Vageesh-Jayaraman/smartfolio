from pathlib import Path

from load_chunk import load_and_chunk
from metadata import add_metadata
from rag.embeddings import embed_documents
from rag.vectorstore import store_documents

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FINANCIALS_DIR = PROJECT_ROOT / "docs" / "financials"


def ingest_pdf(
        pdf_path: Path,
        company: str,
        period: str,
        document_type: str,
):

    chunks = load_and_chunk(pdf_path)
    print(f"Created {len(chunks)} chunks")

    chunks = add_metadata(
        chunks=chunks,
        company=company,
        period=period,
        document_type=document_type,
    )
    print("Metadata added")

    return chunks


def ingest_financials(financials_dir: Path = FINANCIALS_DIR):

    all_chunks = []

    for pdf_path in sorted(financials_dir.rglob("*.pdf")):
        relative_path = pdf_path.relative_to(financials_dir)
        if len(relative_path.parts) < 3:
            print(f"Skipping {pdf_path}: expected <company>/<period>/<document>.pdf")
            continue

        company, period = relative_path.parts[:2]
        document_type = pdf_path.stem
        print(f"\nIngesting {relative_path}")
        all_chunks.extend(
            ingest_pdf(
                pdf_path=pdf_path,
                company=company,
                period=period,
                document_type=document_type,
            )
        )
    return all_chunks


if __name__ == "__main__":
    chunks = ingest_financials()

    print(f"\nIngested {len(chunks)} chunks in total")

    embeddings = embed_documents(chunks)

    print(f"Generated {len(embeddings)} embeddings")
    print(f"Embedding dimensions: {len(embeddings[0])}")

    store_documents(
        documents=chunks,
        embeddings=embeddings,
    )


