import pandas as pd

from app.repositories.data_repository import normalize


def brl(value: float) -> str:
    """
    Format a numeric value as Brazilian currency.

    Example:
        599.9 -> 'R$ 599,90'
    """

    text = f"{value:,.2f}"
    return "R$ " + text.replace(",", "X").replace(".", ",").replace("X", ".")


def _stem(text: str) -> str:
    """Return a simplified word prefix for basic category matching."""
    return text[:4] if len(text) > 4 else text


class CatalogService:
    """Handle product searches, promotions and similar product suggestions."""

    def __init__(self, products: pd.DataFrame, categories: pd.DataFrame, promotions: pd.DataFrame):
        self.products = products
        self.categories = categories
        self.promotions = promotions

        self._cat_names = dict(zip(categories["category_id"], categories["name"]))

    # ---------- Categories ----------

    def category_names(self) -> list[str]:
        """Return the names of all available product categories."""
        return list(self.categories["name"])

    def _match_category_ids(self, query: str) -> list[int]:
        """Find category IDs matching the provided category name."""

        normalized_query = normalize(query)
        category_ids = []

        for category_id, category_name in self._cat_names.items():
            normalized_name = normalize(category_name)

            if (normalized_query == normalized_name
                or normalized_query in normalized_name
                or _stem(normalized_query) == _stem(normalized_name)
                ):
                category_ids.append(category_id)

        return category_ids

    # ---------- Promotions ----------

    def active_promotion(self, product_id: int) -> dict | None:
        """
        Return the best active promotion for a product.
        Promotions are not cumulative
        """

        active_promotions = self.promotions[
            (self.promotions["product_id"] == product_id)
            & (self.promotions["is_active"] == 1)
        ]

        if active_promotions.empty:
            return None

        best_promotion = active_promotions.sort_values("discount_percent",ascending=False).iloc[0]

        return {
            "nome": str(best_promotion["description"]),
            "desconto_percent": float(best_promotion["discount_percent"])
        }

    def list_promotions(self, product_id: int = 0):
        """Return products associated with active promotions."""

        active_promotions = self.promotions[self.promotions["is_active"] == 1]

        if product_id:
            active_promotions = active_promotions[active_promotions["product_id"] == product_id]

        results = []

        for _, promotion in active_promotions.iterrows():
            product = self.products[
                self.products["product_id"] == promotion["product_id"]
            ]

            if product.empty:
                continue

            results.append(self._format(product.iloc[0], include_similar=False))

        return results

    # ---------- Formatting ----------

    def _format(self, row: pd.Series, include_similar: bool = True) -> dict:
        """Format a product row into the response structure."""

        price = float(row["price_brl"])
        product_id = int(row["product_id"])

        promotion = self.active_promotion(product_id)

        available = (
            row["status"] == "active"
            and int(row["stock_quantity"]) > 0
        )

        item = {
            "id": product_id,
            "nome": row["name"],
            "categoria": self._cat_names.get(int(row["category_id"]), ""),
            "preco": brl(price),
            "promocao": None,
            "estoque": int(row["stock_quantity"]),
            "disponivel": bool(available),
            "status_cadastro": row["status"],
            "descricao": row["description"],
            "especificacoes": row["specs"]
        }

        if promotion:
            discounted_price = round(
                price * (1 - promotion["desconto_percent"] / 100),
                2
            )

            item["promocao"] = {
                "nome": promotion["nome"],
                "desconto_percent": promotion["desconto_percent"],
                "preco_com_desconto": brl(discounted_price)
            }

        if include_similar and not available:
            similar_products = self.similar(row)

            item["similares_disponiveis"] = [
                {
                "nome": similar_product["nome"],
                "preco": similar_product["preco"]
                }for similar_product in similar_products
            ]

        return item

    def similar(self, row: pd.Series, n: int = 3) -> list[dict]:
        """Find available products in the same category and price range."""

        price = float(row["price_brl"])

        candidates = self.products[
            (self.products["category_id"] == row["category_id"])
            & (self.products["status"] == "active")
            & (self.products["stock_quantity"] > 0)
            & (self.products["product_id"] != row["product_id"])
            & (
                self.products["price_brl"].between(
                    price * 0.7,
                    price * 1.3
                )
            )
        ]

        candidates = candidates.assign(
            distance=(candidates["price_brl"] - price).abs()
        )

        candidates = candidates.sort_values("distance").head(n)

        results = []

        for _, candidate in candidates.iterrows():
            results.append(
                self._format(candidate, include_similar=False)
            )

        return results

    # ---------- Search ----------

    def search(self,nome: str = "",categoria: str = "",preco_max: float = 0,so_disponiveis: bool = True,limit: int = 8):
        """Search products using name, category, price and availability filters."""

        results_df = self.products

        if categoria:
            category_ids = self._match_category_ids(categoria)

            if not category_ids:
                return {
                    "erro": f"Categoria '{categoria}' não encontrada.",
                    "categorias_validas": self.category_names()
                }

            results_df = results_df[results_df["category_id"].isin(category_ids)]

        if nome:
            search_tokens = normalize(nome).split()
            normalized_names = results_df["name"].apply(normalize)

            matching_names = normalized_names.apply(
                lambda product_name: all(
                    token in product_name.split() or token in product_name
                    for token in search_tokens
                )
            )

            results_df = results_df[matching_names]

        if preco_max and preco_max > 0:
            results_df = results_df[results_df["price_brl"] <= preco_max]

        if so_disponiveis:
            results_df = results_df[(results_df["status"] == "active") & (results_df["stock_quantity"] > 0)]

        results_df = results_df.sort_values("price_brl")

        total_found = len(results_df)

        products = [self._format(product) for _, product in results_df.head(limit).iterrows()]

        response = {
            "total_encontrado": total_found,
            "exibindo": len(products),
            "resultados": products
        }

        if total_found == 0 and nome and so_disponiveis:
            # Check whether the product exists but is currently unavailable.
            retry_response = self.search(
                nome=nome,
                categoria=categoria,
                preco_max=preco_max,
                so_disponiveis=False,
                limit=limit
            )

            if retry_response.get("total_encontrado"):
                retry_response["observacao"] = ("Produto existe no cadastro, mas está indisponível.")

                return retry_response

        return response
