from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Initialize the loader with the file path
loader = PyPDFLoader(file_path="./data/edital.pdf")

# 2. Load the PDF into a list of Documents
pages = loader.load()

# 3. Configure the text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    add_start_index=True,
)

# 4. Split the documents into smaller chunks
chunks = text_splitter.split_documents(pages)

print(f"The original PDF had {len(pages)} pages.")
print(f"Now you have {len(chunks)} text chunks.")