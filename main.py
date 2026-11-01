from pathlib import Path

from app.knowledge.ingestion import extract_pdf_pages, chunk_pages
from app.knowledge.embeddings import EmbeddingModel
from app.knowledge.vector_store import ChromaVectorStore
from app.config.settings import VECTORSTORE_DIR
from app.knowledge.retrieval import Retriever


def main():
    project_root = Path(__file__).resolve().parent

    pdf_path = project_root / "data" / "documents" / "políticas_da_loja.pdf"
    vectorstore_path = project_root / VECTORSTORE_DIR

    # extract and split the PDF.
    extracted_pages = extract_pdf_pages(pdf_path)
    chunks = chunk_pages(extracted_pages)

    #     embeddings.
    embedding_model = EmbeddingModel()
    texts = [chunk["content"] for chunk in chunks]
    embeddings = embedding_model.encode(texts)

    # store chunks and embeddings.
    vector_store = ChromaVectorStore(vectorstore_path)
    vector_store.add_chunks(chunks, embeddings)

    retriever = Retriever(embedding_model, vector_store)

    questions = [
        "A loja oferece desconto para pagamentos via PIX?",
        "Quais são as condições para parcelar uma compra?",
        "Qual é o prazo para devolver um instrumento comprado pela internet?",
        "A loja vende cabos e palhetas?",
        "Qual é o horário de funcionamento aos sábados?"
    ]


    for question in questions:
        print("\n" + "=" * 70)
        print(f"PERGUNTA: {question}")
        print("=" * 70)

        results = retriever.search(question, top_k=3)

        for position, result in enumerate(results, start=1):
            print(f"\nResultado {position}")
            print(f"Página: {result['page']}")
            print(f"Distância: {result['distance']:.4f}")
            print(f"Conteúdo:\n{result['content']}")


if __name__ == "__main__":
    main()
