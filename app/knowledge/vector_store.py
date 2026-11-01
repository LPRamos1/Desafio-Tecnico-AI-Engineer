import chromadb

from pathlib import Path
from app.config.settings import COLLECTION_NAME


class ChromaVectorStore:
    """Manage persistent vector storage using ChromaDB."""


    def __init__(self, persistent_directory: Path):
        """
        Initializes the ChromaDB client and collection.
        Args:
            persist_directory (Path): Directory used to persist vector data.
        """

        self.client = chromadb.PersistentClient(path=str(persistent_directory))
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"
        })


    def add_chunks(self, chunks: list[dict], embeddings: list[list[float]]):
        """
        Store text chunks and their corresponding embeddings.
        Args:
            chunks (list[dict]): Text chunks with IDs and page metadata.
            embeddings (list[list[float]]): Embedding vectors for each chunk
        """

        if len(chunks) != len(embeddings):
            raise ValueError("The number of chunks must match the number of embeddings.")
        if not chunks:
            return

        self.collection.upsert(
            ids=[chunk["id"] for chunk in chunks],
            embeddings=embeddings, # type: ignore
            documents=[chunk["content"] for chunk in chunks],
            metadatas=[{"page": chunk["page"]} for chunk in chunks]
        )


    def count(self):
        """
        Return the number of stored chunks.
        Args:
            int: Number of records in the collection
        """
        return self.collection.count()


    def search(self, query_embedding: list[float], top_k: int = 3):
        """
        Search the collection using a query embedding.
        Args:
            query_embedding (list[float]): Embedding of the search query
            top_k (int): Maximum number of results to retrieve
        Returns:
            dict: Retrieved documents, metada and distance
        """
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"]
        )