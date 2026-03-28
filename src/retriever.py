from langchain_core.retrievers import BaseRetriever
from embeddings import get_vector_db


def get_retriever(k: int = 3) -> BaseRetriever:
    vector_db = get_vector_db()
    return vector_db.as_retriever(search_kwargs={"k": k})