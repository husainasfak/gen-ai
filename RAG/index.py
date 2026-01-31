# indexing
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from dotenv import load_dotenv

load_dotenv()


pdf_path = Path(__file__).parent / "PDF-Guide-Node-Andrew-Mead-v3.pdf"


# load this file 
loader = PyPDFLoader(file_path=pdf_path)

docs = loader.load()

print(f"Number of documents: {len(docs)}")


# spolit the doc in smaller chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=400,
)


chunks = text_splitter.split_documents(documents=docs)

print(f"Number of chunks: {len(chunks)}")


# vector embeddings for chunks

embeddings_model = OpenAIEmbeddings(
    model="text-embedding-3-large"
    
)

vector_store = QdrantVectorStore.from_documents(
    documents=chunks,
    embedding=embeddings_model,
    url="http://localhost:6333",
    collection_name="pdf_guide_collection"
)

print("Indexing completed.")