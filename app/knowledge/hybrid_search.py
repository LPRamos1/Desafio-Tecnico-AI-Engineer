class HybridSearch:
    """Combine vector and keyword search rankings using RRF."""

    def __init__(self, retriever, keyword_search):
        self.retriever = retriever
        self.keyword_search = keyword_search


    def format_context(self, chunks: list[dict]):
        """Format retrieved chunks into context string."""
        return self.retriever.format_context(chunks)


    def search(self, query: str, top_k: int = 3, candidate_k: int = 10, rrf_k: int = 60):

        vector_results = self.retriever.search(query=query,top_k=candidate_k)

        keyword_results = self.keyword_search.search(query=query,top_k=candidate_k)

        rankings = {}

        for results in [vector_results, keyword_results]:
            for rank, chunk in enumerate(results, start=1):
                chunk_id = chunk["id"]

                if chunk_id not in rankings:
                    rankings[chunk_id] = {
                        "chunk": chunk,
                        "rrf_score": 0.0
                    }

                rankings[chunk_id]["rrf_score"] += (1 / (rrf_k + rank))

        ranked_chunks = sorted(rankings.values(),key=lambda item: item["rrf_score"],reverse=True)

        return [{**item["chunk"],"rrf_score": item["rrf_score"]}for item in ranked_chunks[:top_k]]
    