from pathlib import Path

from app.knowledge.ingestion import extract_pdf_pages, chunk_pages
from app.knowledge.embeddings import EmbeddingModel

def main():
    project_root = Path(__file__).resolve().parent
    print(project_root)
    pdf_path = (
        project_root
        / "data"
        / "documents"
        / "políticas_da_loja.pdf"
    )

    pages = extract_pdf_pages(pdf_path)

    chunks = chunk_pages(pages)

    print(f"\nTotal de chunks: {len(chunks)}")

    embedding_model = EmbeddingModel()

    texts = [
        "Quais são as formas de pagamento da loja?",
        "A loja oferece desconto para pagamentos via PIX?",
        "Qual é o horário de funcionamento?"
    ]

    embeddings = embedding_model.encode(texts)

    for text, vector in zip(texts, embeddings):
        print(f"\nTexto: {text}")
        print(f"Dimensões: {len(vector)}")
        print(f"Primeiros valores: {vector[:5]}")

if __name__ == "__main__":
    main()