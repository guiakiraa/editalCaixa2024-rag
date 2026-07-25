from langchain_core.retrievers import BaseRetriever
from embeddings import get_vector_db
import sys


def get_retriever(k: int = 3) -> BaseRetriever:
    vector_db = get_vector_db()
    return vector_db.as_retriever(search_kwargs={"k": k})


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "Qual o valor da taxa de inscrição?"

    print(f"\nQuery: {query}")

    docs = get_retriever().invoke(query)
    print(f"Retrieved {len(docs)} chunks:")

    for i, doc in enumerate(docs, start=1):
        page = doc.metadata.get("page_label")
        start_index = doc.metadata.get("start_index")
        print(f"\n[{i}] page {page} (start_index={start_index})")
        print(doc.page_content)