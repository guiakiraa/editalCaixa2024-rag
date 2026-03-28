from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
from ingest import load_chunks
import os

load_dotenv()

PERSIST_DIR = "./my_chroma_db"
COLLECTION_NAME = "edital_chunks"

def get_vector_db() -> Chroma:
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    if os.path.exists(PERSIST_DIR) and os.listdir(PERSIST_DIR):
        print(f"Loading existing vector database from '{PERSIST_DIR}'.")
        return Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME,
        )

    print("Creating new vector database...")
    chunks = load_chunks()
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIR,
        collection_name=COLLECTION_NAME,
    )
    print(f"Saved {vector_db._collection.count()} chunks to '{PERSIST_DIR}'.")
    return vector_db
