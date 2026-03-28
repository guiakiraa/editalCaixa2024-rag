from langchain_community.document_loaders import PyPDFLoader

# 1. Initialize the loader with the file path
loader = PyPDFLoader(file_path="./data/edital.pdf")

# 2. Load the PDF into a list of Documents
pages = loader.load()

# Accessing the content
print(f"Total pages: {len(pages)}")
print(f"First page content: {pages[0].page_content}")
print(f"Metadata (e.g., page number): {pages[0].metadata}")
