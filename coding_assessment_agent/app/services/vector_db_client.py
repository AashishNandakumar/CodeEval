import asyncio
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from app.database import get_vector_store # Import the function that returns the Chroma instance
import logging

logger = logging.getLogger(__name__)

class VectorDBClient:
    def __init__(self):
        # Get the pre-initialized Chroma instance from database.py
        self._vector_store: Chroma = get_vector_store()

    async def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]]) -> List[str]:
        """Adds documents to the Chroma vector store asynchronously."""
        if not texts:
            return []
        if len(texts) != len(metadatas):
            raise ValueError("Number of texts and metadatas must be the same.")
        try:
            # Chroma's add_texts might be sync, run in thread pool
            doc_ids = await asyncio.to_thread(
                self._vector_store.add_texts,
                texts=texts,
                metadatas=metadatas
            )
            logger.info(f"Added {len(doc_ids)} documents to vector store.")
            return doc_ids
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}", exc_info=True)
            raise

    async def similarity_search(self, query: str, k: int = 4, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Performs similarity search on the vector store asynchronously."""
        try:
            # Chroma's similarity_search might be sync, run in thread pool
            results = await asyncio.to_thread(
                self._vector_store.similarity_search,
                query=query,
                k=k,
                filter=filter_metadata
            )
            logger.debug(f"Similarity search for '{query}' returned {len(results)} results.")
            return results
        except Exception as e:
            logger.error(f"Error performing similarity search: {e}", exc_info=True)
            raise

# You might want to instantiate this client once and use it across the application
# For example, using FastAPI's dependency injection or a simple singleton pattern.
vector_db_client = VectorDBClient()
