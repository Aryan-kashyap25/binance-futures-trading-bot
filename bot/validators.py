"""Input validation helpers for the trading bot CLI."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from .orders import OrderRequest

SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{5,20}$")
VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}


class ValidationError(ValueError):
    """Raised when CLI input or payload data is invalid."""


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Validated and normalized CLI arguments."""

    order_request: OrderRequest


def validate_symbol(symbol: str) -> str:
    """Validate that a symbol is uppercase and Binance-compatible."""

    normalized = symbol.strip().upper()
    if not normalized:
        raise ValidationError("symbol is required")
    if normalized != symbol.strip():
        raise ValidationError("symbol must be uppercase")
    if not SYMBOL_PATTERN.fullmatch(normalized):
        raise ValidationError(
            "symbol must contain only uppercase letters and digits, for example BTCUSDT"
        )
    return normalized


def validate_side(side: str) -> str:
    """Validate order side."""

    normalized = side.strip().upper()
    if normalized not in VALID_SIDES:
        raise ValidationError("side must be BUY or SELL")
    return normalized


def validate_order_type(order_type: str) -> str:
    """Validate order type."""

    normalized = order_type.strip().upper()
    if normalized not in VALID_ORDER_TYPES:
        raise ValidationError("type must be MARKET or LIMIT")
    return normalized


def _parse_positive_decimal(value: str, field_name: str) -> Decimal:
    try:
        parsed = Decimal(value.strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValidationError(f"{field_name} must be a positive number") from exc

    if parsed <= 0:
        raise ValidationError(f"{field_name} must be greater than 0")
    return parsed


def validate_quantity(quantity: str) -> Decimal:
    """Validate a positive order quantity."""

    return _parse_positive_decimal(quantity, "quantity")


def validate_price(price: str | None, order_type: str) -> Decimal | None:
    """Validate price only when required by LIMIT orders."""

    if order_type == "LIMIT":
        if price is None:
            raise ValidationError("price is required for LIMIT orders")
        return _parse_positive_decimal(price, "price")

    if price is None or not str(price).strip():
        return None

    return _parse_positive_decimal(price, "price")


def validate_order_request(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: str | None = None,
) -> OrderRequest:
    """Validate and normalize a full order request."""

    normalized_symbol = validate_symbol(symbol)
    normalized_side = validate_side(side)
    normalized_type = validate_order_type(order_type)
    normalized_quantity = validate_quantity(quantity)
    normalized_price = validate_price(price, normalized_type)

    return OrderRequest(
        symbol=normalized_symbol,
        side=normalized_side,
        order_type=normalized_type,
        quantity=normalized_quantity,
        price=normalized_price,
    )
