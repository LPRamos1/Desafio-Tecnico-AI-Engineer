from app.config.logging_config import logger
from app.config.settings import RETRIEVAL_TOP_K


def build_tools(catalog, orders, retriever) -> list:
    """
    Create the tools made available to Gemini.
    Args:
        catalog: Service responsible for product catalog queries.
        orders: Service responsible for order queries.
        retriever: Service responsible for retrieving store policies.
    Returns:
        list: Available tools for the agent.
    """

    def buscar_produtos(nome: str = "", categoria: str = "", preco_max: float = 0, so_disponiveis: bool = True):
        """
        Search the product catalog for prices, availability and specifications.
        Always use this tool when the customer asks about product prices,
        availability or available options.
        Never provide product prices or stock information without querying
        this tool first.

        Args:
            nome: Product brand and/or model.
            categoria: Instrument category.
            preco_max: Maximum price in BRL. Use 0 to disable this filter.
            so_disponiveis: If True, return only products currently in stock.
        Returns:
            dict: Matching products and their information.
        """
        logger.info("Searching products. Name: %s | Category: %s | Maximum price: %s",nome, categoria, preco_max)

        try:
            resultado = catalog.search(
                nome=nome,
                categoria=categoria,
                preco_max=preco_max,
                so_disponiveis=so_disponiveis
            )

            logger.info("Product search completed successfully.")
            return resultado

        except Exception:
            logger.exception("Error searching products.")
            return {"erro": ("Internal error while searching for products. "
                "Apologize and offer human assistance.")
            }


    def consultar_promocoes(product_id: int = 0):
        """
        Retrieve currently active promotions.
        For a specific product price, prefer buscar_produtos because
        it already includes promotion information.

        Args:
            product_id: Product identifier. Use 0 to retrieve all promotions.
        Returns:
            dict: Number of promotions and products on promotion.
        """
        logger.info("Searching promotions. Product ID: %s", product_id)

        try:

            promocoes = catalog.list_promotions(product_id=product_id)
            resultado = {"total": len(promocoes),"produtos_em_promocao": promocoes}

            logger.info("Promotion search completed successfully.")
            return resultado

        except Exception:
            logger.exception("Error searching promotions.")
            return {"erro": ("Internal error while searching for promotions. "
            "Apologize and offer human assistance.")
            }

    def consultar_pedido(order_id: int, identificador: str) -> dict:
        """
        Retrieve order status, tracking information and delivery estimates.
        Only use this tool after obtaining the order number and the
        customer's registered email address or phone number.

        Args:
            order_id: Order number.
            identificador: Email address or phone number registered with the order.
        Returns:
            dict: Order information or an error message.
        """

        logger.info("Searching order. Order ID: %s", order_id)

        try:
            resultado = orders.get_order(order_id=order_id,identificador=identificador)
            logger.info("Order search completed successfully.")
            return resultado

        except Exception:
            logger.exception("Error searching order %s.", order_id)
            return {"erro": ("Internal error while searching for the order. "
            "Apologize and offer human assistance.")
            }

    def consultar_politicas(consulta: str) -> str:
        """
        Search the internal store manual using hybrid RAG retrieval.
        Use this tool for questions about opening hours, address, phone number,
        payment methods, installments, returns, exchanges, warranty,
        shipping and delivery policies.

        Rewrite the customer's question as a short and objective search query.
        If multiple or conflicting rules are retrieved, consider all
        relevant passages before answering.

        Args:
            consulta: Short query describing the requested store policy.
        Returns:
            str: Retrieved context from the store manual.
        """

        logger.info("Searching store policies.")

        try:
            chunks = retriever.search(consulta, top_k=RETRIEVAL_TOP_K)

            contexto = retriever.format_context(chunks)

            logger.info("Store policy search completed successfully.")
            return contexto

        except Exception:
            logger.exception("Error searching store policies.")
            return ("The store manual could not be retrieved. "
            "Apologize and offer human assistance.")

    return [
        buscar_produtos,
        consultar_promocoes,
        consultar_pedido,
        consultar_politicas
    ]
