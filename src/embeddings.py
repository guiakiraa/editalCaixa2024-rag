from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
from ingest import load_chunks
import os

# 1. Load environment variables (like OPENAI_API_KEY)
load_dotenv()

# 2. Create embeddings for the documents
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
print("Initialized OpenAI embeddings with model 'text-embedding-3-small'.")

# 3. Load the document chunks
chunks = load_chunks()

# 4. Create or load the Chroma vector database
persist_dir = "./my_chroma_db"
if os.path.exists(persist_dir) and os.listdir(persist_dir):
    # Load
    vector_db = Chroma(
        persist_directory=persist_dir, 
        embedding_function=embeddings,
        collection_name="edital_chunks"
    )
    print(f"Loaded existing vector database from '{persist_dir}'.")
else:
    # Create and persist
    vector_db = Chroma.from_documents(
        documents=chunks, 
        embedding=embeddings,
        persist_directory=persist_dir,
        collection_name="edital_chunks"
    )
    print(f"Created new vector database and saved to '{persist_dir}'.")


collection_stats = vector_db._collection.count()
print(f"Number of chunks in the database: {collection_stats}")
