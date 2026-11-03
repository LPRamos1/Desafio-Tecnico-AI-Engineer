import re

import pandas as pd

from app.services.catalog_service import brl


STATUS_LABELS = {
    "delivered": "Entregue",
    "shipped": "Enviado / em transporte",
    "processing": "Em processamento",
    "pending": "Aguardando pagamento",
    "cancelled": "Cancelado",
    "returned": "Devolvido",
}

# Use the same message for missing orders and mismatched identification data.
# This prevents revealing whether an order ID exists.
_NOT_FOUND = {
    "encontrado": False,
    "mensagem": "Não localizei um pedido com esse número e esses dados de identificação.",
}


def _digits(text: str) -> str:
    """Return only the numeric characters from a value."""
    return re.sub(r"\D", "", str(text))


def _clean(value):
    """Convert pandas missing values to None."""
    return None if pd.isna(value) else value


class OrderService:
    """Retrieve order information after validating the customer's identity."""

    def __init__(self, orders, items, customers, products):
        self.orders = orders
        self.items = items
        self.customers = customers
        self.products = products

    def _owns(self, customer, identificador: str) -> bool:
        """Check whether the provided email or phone belongs to the customer."""
        identifier = identificador.strip().lower()

        if not identifier:
            return False

        if "@" in identifier:
            return identifier == customer["email"]

        phone_digits = _digits(identifier)
        customer_phone_digits = _digits(customer["phone"])

        return (len(phone_digits) >= 8 and phone_digits[-8:] == customer_phone_digits[-8:])

    def get_order(self, order_id: int, identificador: str) -> dict:
        """Return order details if the provided identification data is valid."""
        matching_orders = self.orders[self.orders["order_id"] == int(order_id)]

        if matching_orders.empty:
            return _NOT_FOUND

        order = matching_orders.iloc[0]

        matching_customers = self.customers[self.customers["customer_id"] == order["customer_id"]]

        if matching_customers.empty:
            return _NOT_FOUND

        customer = matching_customers.iloc[0]

        if not self._owns(customer, identificador):
            return _NOT_FOUND

        order_items = self.items[self.items["order_id"] == order["order_id"]]

        items = []

        for _, item in order_items.iterrows():
            matching_products = self.products[self.products["product_id"] == item["product_id"]]

            if matching_products.empty:
                product_name = f"Produto #{item['product_id']}"
            else:
                product_name = matching_products.iloc[0]["name"]

            items.append({
                "produto": product_name,
                "quantidade": int(item["quantity"]),
            })

        order_status = str(order["status"]).strip().lower()

        return {
            "encontrado": True,
            "pedido": int(order["order_id"]),
            "cliente": customer["name"].split()[0],
            "data_pedido": str(order["order_date"]),
            "status": STATUS_LABELS.get(order_status, order_status),
            "total": brl(float(order["total_brl"])),
            "forma_pagamento": str(order["payment_method"]),
            "codigo_rastreio": _clean(order["tracking_code"]),
            "previsao_entrega": _clean(order["estimated_delivery"]),
            "observacoes": _clean(order["notes"]),
            "itens": items,
        }
