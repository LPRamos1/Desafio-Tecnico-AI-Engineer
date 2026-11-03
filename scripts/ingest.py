from app.config.settings import BASE_DIR, VECTORSTORE_DIR
from app.knowledge.embeddings import EmbeddingModel
from app.knowledge.vector_store import ChromaVectorStore
from app.knowledge.ingestion import ingest_pdf


def main():

    pdf_path = BASE_DIR / "data" / "documents" / "políticas_da_loja.pdf"

    embedding_model = EmbeddingModel()
    vector_store = ChromaVectorStore(persistent_directory=VECTORSTORE_DIR)

    total_chunks = ingest_pdf(pdf_path=pdf_path,embedding_model=embedding_model,vector_store=vector_store)

    print(f"Ingestion completed: {total_chunks} chunks stored.")
    print(f"Total chunks in database: {vector_store.count()}")


if __name__ == "__main__":
    main()
