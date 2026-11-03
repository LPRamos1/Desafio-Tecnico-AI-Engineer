from time import perf_counter

from app.agent.agent import Agent
from app.agent.session import Session
from app.config.logging_config import logger
from app.config.settings import BASE_DIR, DATA_DIR, VECTORSTORE_DIR
from app.knowledge.embeddings import EmbeddingModel
from app.knowledge.hybrid_search import HybridSearch
from app.knowledge.ingestion import chunk_pages, extract_pdf_pages
from app.knowledge.keyword_search import KeywordSearch
from app.knowledge.retrieval import Retriever
from app.knowledge.vector_store import ChromaVectorStore
from app.llm.gemini_client import GeminiClient
from app.repositories import data_repository as repo
from app.services.catalog_service import CatalogService
from app.services.order_service import OrderService
from app.tools.registry import build_tools


def initialize_agent() -> Agent:
    """Initialize the application dependencies and create the agent."""
    start_time = perf_counter()

    # Initialize the policy retrieval components.
    vector_store = ChromaVectorStore(VECTORSTORE_DIR)
    embedding_model = EmbeddingModel()

    retriever = Retriever(embedding_model=embedding_model,vector_store=vector_store,)

    pdf_path = BASE_DIR / "data" / "documents" / "políticas_da_loja.pdf"

    pages = extract_pdf_pages(pdf_path)
    chunks = chunk_pages(pages)

    keyword_search = KeywordSearch(chunks)

    hybrid_search = HybridSearch(retriever=retriever,keyword_search=keyword_search,)

    # Load structured data and initialize the services.
    products = repo.load_products(DATA_DIR / "products.csv")
    categories = repo.load_categories(DATA_DIR / "categories.csv")
    promotions = repo.load_promotions(DATA_DIR / "promotions.csv")

    catalog = CatalogService(products=products,categories=categories,promotions=promotions,)

    orders = OrderService(
        orders=repo.load_orders(DATA_DIR / "orders.csv"),
        items=repo.load_order_items(DATA_DIR / "order_items.csv"),
        customers=repo.load_customers(DATA_DIR / "customers.csv"),
        products=products,
    )

    # Register the tools available to the agent.
    tools = build_tools(catalog=catalog,orders=orders,retriever=hybrid_search,)

    agent = Agent(gemini_client=GeminiClient(),tools=tools,session=Session(),)

    startup_time = perf_counter() - start_time
    logger.info("[PERFORMANCE] Startup: %.2fs", startup_time)

    return agent


def main() -> None:
    """Run the agent through an interactive terminal interface."""
    print("=" * 50)
    print("EMPÓRIO DA MÚSICA - ASSISTENTE VIRTUAL")
    print("=" * 50)
    print("Digite 'sair' para encerrar.\n")

    agent = initialize_agent()

    while True:
        try:
            message = input("Você: ").strip()

            if not message:
                continue

            if message.lower() in ("sair", "exit", "quit"):
                print("\nAtendimento encerrado.")
                break

            response = agent.handle_message(message)
            print(f"\nAssistente: {response}\n")

        except KeyboardInterrupt:
            print("\n\nAtendimento encerrado.")
            break

        except Exception:
            logger.exception("Error during conversation")
            print("\nDesculpe, tive um problema técnico agora. ""Pode tentar de novo em instantes?\n")


if __name__ == "__main__":
    main()
