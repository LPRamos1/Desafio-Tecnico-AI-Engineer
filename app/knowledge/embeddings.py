from sentence_transformers import SentenceTransformer

from app.config.settings import EMBEDDING_MODEL


class EmbeddingModel:
    """Generate vector representations of text."""


    def __init__(self):
        """Initialize the sentence transformer model."""
        self.model = SentenceTransformer(EMBEDDING_MODEL)


    def encode(self, texts: list[str]):
        """
        Convert texts into normalized embedding vectors.
        Args:
            texts (list[dict]): Texts to convert into embeddings.
        Returns:
            list(list[dicts]): Embedding vector for the input texts.
        """
        if not texts:
            return []
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True
        )

        return embeddings.tolist()
    