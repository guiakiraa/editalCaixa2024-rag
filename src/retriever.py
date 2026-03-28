from embeddings import get_vector_db

def get_retriever(k: int = 3):
    vector_db = get_vector_db()
    return vector_db.as_retriever(search_kwargs={"k": k})