import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

from app.config.logging_config import logger


# Used to detect descriptions that mention a different brand from the product name.
# Example: product 144 has Roland in its name but Yamaha in its description.
KNOWN_BRANDS = {
    "yamaha",
    "roland",
    "fender",
    "gibson",
    "takamine",
    "ibanez",
    "korg",
    "casio",
    "tagima",
    "epiphone",
    "squier",
    "giannini",
    "cort",
    "nord",
    "taylor",
    "martin",
    "pearl",
    "tama",
    "zildjian",
    "shure",
    "behringer",
}


def normalize(text) -> str:
    """Convert text to lowercase ASCII without accents or punctuation."""
    normalized_text = (unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode())

    return re.sub(r"[^a-z0-9]+", " ", normalized_text.lower()).strip()


def _parse_specs(raw) -> dict:
    """Parse product specifications from a JSON string."""
    try:
        if isinstance(raw, str) and raw.strip():
            return json.loads(raw)

        return {}

    except json.JSONDecodeError:
        return {}


def load_products(path: Path) -> pd.DataFrame:
    """Load products and remove invalid or inconsistent records."""
    products = pd.read_csv(path)

    # Remove spreadsheet junk, such as footer rows and notes.
    products["product_id"] = pd.to_numeric(products["product_id"], errors="coerce",)
    products["price_brl"] = pd.to_numeric(products["price_brl"], errors="coerce",)

    initial_count = len(products)

    products = products.dropna(subset=["product_id", "price_brl", "name"]).copy()

    dropped_count = initial_count - len(products)

    if dropped_count:
        logger.warning("Dropped %d invalid product rows", dropped_count)

    products["product_id"] = products["product_id"].astype(int)
    products["category_id"] = (pd.to_numeric(products["category_id"], errors="coerce").fillna(0).astype(int))
    products["stock_quantity"] = (pd.to_numeric(products["stock_quantity"], errors="coerce").fillna(0).astype(int))

    products["name"] = products["name"].str.strip()
    products["description"] = products["description"].fillna("").str.strip()
    products["status"] = (products["status"].fillna("").str.strip().str.lower())
    products["specs"] = products["specs"].apply(_parse_specs)

    products = products.drop_duplicates(subset="product_id",keep="last",)

    # Ignore descriptions that mention a brand absent from the product name.
    for index, product in products.iterrows():
        name_tokens = set(normalize(product["name"]).split())
        description_brands = (
            set(normalize(product["description"]).split()) & KNOWN_BRANDS
        )

        if description_brands and not (description_brands & name_tokens):
            logger.warning(
                "Product %s: description mentions %s but name is '%s' -> description ignored",
                product["product_id"],
                description_brands,
                product["name"],
            )

            products.at[index, "description"] = ""

    return products.reset_index(drop=True)


def load_categories(path: Path) -> pd.DataFrame:
    """Load product categories and convert category IDs to integers."""

    categories = pd.read_csv(path)
    categories["category_id"] = pd.to_numeric(categories["category_id"], errors="coerce")
    categories = categories.dropna(subset=["category_id"])

    return categories.astype({"category_id": int})


def load_promotions(path: Path) -> pd.DataFrame:
    """Load promotions and normalize their numeric fields."""
    promotions = pd.read_csv(path)

    promotions["product_id"] = pd.to_numeric(promotions["product_id"], errors="coerce",)
    promotions["discount_percent"] = pd.to_numeric(promotions["discount_percent"], errors="coerce",)
    promotions["is_active"] = (
        pd.to_numeric(promotions["is_active"], errors="coerce").fillna(0).astype(int))

    promotions = promotions.dropna(subset=["product_id", "discount_percent"])

    return promotions.astype({"product_id": int})


def load_customers(path: Path) -> pd.DataFrame:
    """Load customers, supporting CSV files without a header row."""
    customers = pd.read_csv(path)

    # Some exported files do not contain column headers.
    if "customer_id" not in customers.columns:
        customers = pd.read_csv(
            path,
            header=None,
            names=[
                "customer_id",
                "name",
                "phone",
                "email",
                "city",
            ],
        )

    customers["customer_id"] = pd.to_numeric(customers["customer_id"], errors="coerce",)
    customers = customers.dropna(subset=["customer_id"]).astype({"customer_id": int})
    customers["email"] = (customers["email"].fillna("").str.strip().str.lower())

    return customers


def load_orders(path: Path) -> pd.DataFrame:
    """Load orders and normalize their identification fields."""
    orders = pd.read_csv(path)

    orders["order_id"] = pd.to_numeric(orders["order_id"], errors="coerce",)
    orders["customer_id"] = pd.to_numeric(orders["customer_id"], errors="coerce",)
    orders = orders.dropna(subset=["order_id", "customer_id"])

    return orders.astype({"order_id": int, "customer_id": int,})


def load_order_items(path: Path) -> pd.DataFrame:
    """Load order items and convert numeric fields to integers."""
    order_items = pd.read_csv(path)

    numeric_columns = ("order_id", "quantity", "product_id")

    for column in numeric_columns:
        order_items[column] = pd.to_numeric(
            order_items[column],
            errors="coerce",
        )

    return order_items.dropna().astype(int)
