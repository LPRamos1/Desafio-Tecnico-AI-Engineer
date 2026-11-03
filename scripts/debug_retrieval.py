"""Compare vector, keyword (BM25) and hybrid (RRF) retrieval for a question.

Manual debugging tool, not an automated test.

Usage (from the project root, after `python ingest.py`):
    python -m scripts.debug_retrieval "Can I pay in 5 installments?"
    python -m scripts.debug_retrieval --content "Quais são as regras de parcelamento?"
"""
import argparse

from app.config.settings import BASE_DIR, RETRIEVAL_TOP_K, VECTORSTORE_DIR
from app.knowledge.embeddings import EmbeddingModel
from app.knowledge.hybrid_search import HybridSearch
from app.knowledge.ingestion import chunk_pages, extract_pdf_pages
from app.knowledge.keyword_search import KeywordSearch
from app.knowledge.retrieval import Retriever
from app.knowledge.vector_store import ChromaVectorStore


def show(title: str, results: list[dict], score_key: str, show_content: bool) -> None:
    print(f"\n=== {title} ===")
    for position, chunk in enumerate(results, start=1):
        print(f"{position}. {chunk['id']} "
              f"(section {chunk.get('section')}, page {chunk.get('page')}) "
              f"{score_key}={chunk[score_key]:.4f}")
        if show_content:
            print(f"{chunk['content']}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0]) #type: ignore
    parser.add_argument("question", nargs="?", help="Question to search (asked interactively if omitted)")
    parser.add_argument("--content", action="store_true", help="Also print the text of each chunk")
    parser.add_argument("--top-k", type=int, default=RETRIEVAL_TOP_K)
    args = parser.parse_args()

    question = (args.question or input("Question: ")).strip()

    retriever = Retriever(EmbeddingModel(), ChromaVectorStore(VECTORSTORE_DIR))
    pdf_path = BASE_DIR / "data" / "documents" / "políticas_da_loja.pdf"
    keyword_search = KeywordSearch(chunk_pages(extract_pdf_pages(pdf_path)))
    hybrid = HybridSearch(retriever, keyword_search)

    show("VECTOR (distance: lower is closer)", retriever.search(question, args.top_k), "distance", args.content)
    show("KEYWORD / BM25 (higher is better)", keyword_search.search(question, args.top_k), "score", args.content)
    show("HYBRID / RRF (higher is better)", hybrid.search(question, top_k=args.top_k), "rrf_score", args.content)


if __name__ == "__main__":
    main()