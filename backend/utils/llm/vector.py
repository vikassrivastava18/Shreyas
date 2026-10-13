# openai embeddings used
"""Contains logic to store and retrieve vectors (FAISS vector store)."""
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import logger

embedding_model = OpenAIEmbeddings()

BASE_DIR = Path(__file__).resolve().parents[2]
FAISS_INDEX_PATH = BASE_DIR / "core" / "data" / "faiss_db_new"

faiss_db = FAISS.load_local(
    str(FAISS_INDEX_PATH),
    embedding_model,
    allow_dangerous_deserialization=True,
)


def store_vector_store(documents, index_path="core/data/faiss_db_new"):
    try:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunked_documents = text_splitter.split_documents(documents)
        faiss_db = FAISS.from_documents(chunked_documents, embedding_model)
        faiss_db.save_local(str(BASE_DIR / index_path))
        print("book stored in vector database")
    except Exception as error:
        logger.error(f"Error in saving vector data: {error}", exc_info=True)