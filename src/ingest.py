from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_chunks(file_path: str = "./data/edital.pdf") -> list:
    print(f"Loading PDF from '{file_path}'...")
    loader = PyPDFLoader(file_path=file_path)
    pages = loader.load()
    print(f"Loaded {len(pages)} pages from the PDF.")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        add_start_index=True,
    )

    chunks = text_splitter.split_documents(pages)
    print(f"Split the document into {len(chunks)} chunks.")
    return chunks