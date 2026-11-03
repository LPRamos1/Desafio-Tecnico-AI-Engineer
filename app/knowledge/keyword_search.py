import re

from rank_bm25 import BM25Okapi


class KeywordSearch:
    """Retrieve relevant text chunks using BM25 keyword ranking."""

    def __init__(self, chunks: list[dict]):
        if not chunks:
            raise ValueError("The chunks list cannot be empty.")

        self.chunks = chunks

        # Tokenize each document to build the BM25 index.
        self.tokenized_corpus = [
            self._tokenize(chunk["content"])for chunk in chunks]

        self.bm25 = BM25Okapi(self.tokenized_corpus)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Convert text into lowercase word tokens."""
        return re.findall(r"\w+", text.lower())

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        if not query.strip():
            raise ValueError("Search query cannot be empty.")

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        query_tokens = self._tokenize(query)

        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)

        # Sort chunk indexes by BM25 score, highest first.
        ranked_indexes = sorted(range(len(scores)),key=lambda index: scores[index],reverse=True)

        results = []

        for index in ranked_indexes[:top_k]:
            chunk = self.chunks[index]

            results.append({
                "id": chunk["id"],
                "content": chunk["content"],
                "page": chunk["page"],
                "section": chunk.get("section"),
                "score": float(scores[index])
            })

        return results
    