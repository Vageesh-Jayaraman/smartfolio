import os
import uuid

from dotenv import load_dotenv
from langchain_core.documents import Document
from langsmith import traceable
from qdrant_client import QdrantClient
from qdrant_client.http.models import MatchAny
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

@traceable(name="Qdrant Retrieval")
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
                key="metadata.company",
                match=MatchValue(value=company),
            )
        )

    if periods:
        conditions.append(
            FieldCondition(
                key="metadata.period",
                match=MatchAny(any=periods),
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

if __name__ == "__main__":
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="metadata.company",
        field_schema="keyword",
    )

    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="metadata.period",
        field_schema="keyword",
    )

    print("Payload indexes created")