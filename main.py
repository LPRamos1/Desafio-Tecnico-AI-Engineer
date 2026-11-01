from pathlib import Path

from app.knowledge.ingestion import extract_pdf_pages, chunk_pages

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

    for chunk in chunks:
        print(
            f"\nID: {chunk['id']} | "
            f"Página: {chunk['page']} | "
            f"Caracteres: {len(chunk['content'])}"
        )
        print(chunk["content"][:200])
        print("-" * 60)


if __name__ == "__main__":
    main()