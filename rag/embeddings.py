import os

import requests
from dotenv import load_dotenv
from langchain_core.documents import Document

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "qwen/qwen3-embedding-8b",
)

OPENROUTER_EMBEDDINGS_URL = "https://openrouter.ai/api/v1/embeddings"
BATCH_SIZE = 50


def embed_request(texts: list[str]) -> list[list[float]]:
    response = requests.post(
        OPENROUTER_EMBEDDINGS_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": EMBEDDING_MODEL,
            "input": texts,
        },
        timeout=120,
    )

    response.raise_for_status()
    data = response.json()["data"]
    data.sort(key=lambda item: item["index"])
    return [item["embedding"] for item in data]


def embed_documents(documents: list[Document]) -> list[list[float]]:

    embeddings = []
    for start in range(0, len(documents), BATCH_SIZE):
        batch = documents[start:start + BATCH_SIZE]
        texts = [
            document.page_content
            for document in batch
        ]

        batch_embeddings = embed_request(texts)
        embeddings.extend(batch_embeddings)

        print(
            f"Embedded "
            f"{min(start + BATCH_SIZE, len(documents))}"
            f"/{len(documents)} documents"
        )

    return embeddings

def embed_query(query: str) -> list[float]:
    return embed_request([query])[0]