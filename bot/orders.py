"""Order orchestration and response formatting helpers."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .client import BinanceTestnetClient


@dataclass(frozen=True, slots=True)
class OrderRequest:
    """Normalized order request ready for API submission."""

    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    price: Decimal | None = None


@dataclass(frozen=True, slots=True)
class OrderSummary:
    """Human-readable order summary used by the CLI output."""

    order_id: str | None
    status: str | None
    executed_qty: str | None
    avg_price: str | None
    price: str | None


def _decimal_to_str(value: Decimal) -> str:
    normalized = value.normalize()
    return format(normalized, "f")


def build_order_payload(order_request: OrderRequest) -> dict[str, str]:
    """Convert a normalized order request into Binance API payload fields."""

    payload: dict[str, str] = {
        "symbol": order_request.symbol,
        "side": order_request.side,
        "type": order_request.order_type,
        "quantity": _decimal_to_str(order_request.quantity),
    }

    if order_request.order_type == "LIMIT":
        if order_request.price is None:
            raise ValueError("LIMIT orders require a price")
        payload["price"] = _decimal_to_str(order_request.price)
        payload["timeInForce"] = "GTC"

    return payload


def place_order(
    client: BinanceTestnetClient,
    order_request: OrderRequest,
) -> dict[str, Any]:
    """Submit an order to Binance Futures Testnet and return the raw response."""

    payload = build_order_payload(order_request)
    return client.create_futures_order(**payload)


def extract_order_summary(order_response: dict[str, Any]) -> OrderSummary:
    """Extract the fields that should be highlighted in console output."""

    order_id = order_response.get("orderId")
    status = order_response.get("status")
    executed_qty = order_response.get("executedQty")
    avg_price = order_response.get("avgPrice")
    price = order_response.get("price")

    return OrderSummary(
        order_id=str(order_id) if order_id is not None else None,
        status=str(status) if status is not None else None,
        executed_qty=str(executed_qty) if executed_qty is not None else None,
        avg_price=str(avg_price) if avg_price is not None else None,
        price=str(price) if price is not None else None,
    )
