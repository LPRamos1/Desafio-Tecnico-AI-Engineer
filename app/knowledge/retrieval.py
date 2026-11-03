from app.knowledge.embeddings import EmbeddingModel
from app.knowledge.vector_store import ChromaVectorStore


class Retriever:
    """Retrieve relevant knowledge chunks for a user query."""

    def __init__(self, embedding_model: EmbeddingModel, vector_store: ChromaVectorStore):
        """
        Initialize the retrieval dependencies.
        Args:
            embedding_model (EmbeddingModel): Model used to encode queries.
            vector_store (ChromaVectorStore): Persistent vector database.
        """
        self.embedding_model= embedding_model
        self.vector_store = vector_store


    def search(self, query: str, top_k: int = 3):
        """
        Search for the most relevant chunks
        Args:
            query (str): User question to search.
            top_k (int): Maximum number of results to retrieve.
        Returns:
            lias[dict]: Retrieved chunks with metadata and distance.
        """
        if not query.strip():
            raise ValueError("Search query cannot be empty.")
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        query_embedding = self.embedding_model.encode([query])[0]

        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k
            )   

        retrieved_chunks = []

        for index, document in enumerate(results["documents"][0]):  # type: ignore
            metadata = results["metadatas"][0][index]   # type: ignore
            distance = results["distances"][0][index]   # type: ignore
            chunk_id = results["ids"][0][index]

            retrieved_chunks.append({
                "id": chunk_id,
                "content": document,
                "page": metadata["page"],
                "section": metadata["section"],
                "distance": distance
            })

        return retrieved_chunks


    def format_context(self, chunks: list[dict]):
        """Format retrieved chunks into context string"""
        
        if not chunks:
            return "Nenhum conteudo relevante foi encontrado."

        context_parts = []

        for chunk in chunks:
            context_parts.append(
                f"[Seção {chunk['section']} | Página {chunk['page']}]\n"
                f"{chunk['content']}"
            )

        return "\n\n".join(context_parts)
    