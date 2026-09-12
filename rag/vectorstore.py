import os
import uuid

from dotenv import load_dotenv
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.models import Filter, FieldCondition, MatchValue


load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = "financial_documents"

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)


def create_collection(vector_size: int):
    if client.collection_exists(COLLECTION_NAME):
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE,
        ),
    )

    print(f"Created collection: {COLLECTION_NAME}")


def store_documents(
        documents: list[Document],
        embeddings: list[list[float]],
):
    if len(documents) != len(embeddings):
        raise ValueError(
            "Number of documents and embeddings must be the same"
        )

    if not documents:
        return

    create_collection(vector_size=len(embeddings[0]))
    points = []

    for document, embedding in zip(documents, embeddings):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "text": document.page_content,
                    "metadata": document.metadata,
                }
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    print(f"Stored {len(points)} documents in Qdrant")

def search_documents(
        query_vector: list[float],
        company: str | None = None,
        periods: list[str] | None = None,
        limit: int = 5,
):
    conditions = []

    if company:
        conditions.append(
            FieldCondition(
                key="company",
                match=MatchValue(value=company),
            )
        )

    if periods:
        conditions.append(
            FieldCondition(
                key="period",
                match={"any": periods},
            )
        )

    query_filter = Filter(must=conditions) if conditions else None

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=query_filter,
        limit=limit,
    )

    return results.points
