"""Command-line entry point for the Binance Futures Testnet trading bot."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Sequence

from dotenv import find_dotenv, load_dotenv

from bot.client import BinanceAPIError, BinanceRequestError, BinanceTestnetClient
from bot.logging_config import configure_logging
from bot.orders import extract_order_summary, place_order
from bot.validators import ValidationError, validate_order_request


def _load_environment() -> None:
    """Load environment variables from the project .env file or cwd."""

    project_dir = Path(__file__).resolve().parent
    explicit_env_path = project_dir / ".env"
    if explicit_env_path.exists():
        load_dotenv(explicit_env_path)
    else:
        load_dotenv(find_dotenv(usecwd=True))


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet trading bot CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    order_parser = subparsers.add_parser(
        "order",
        help="Place a MARKET or LIMIT futures order",
    )
    order_parser.add_argument("--symbol", required=True, help="Trading symbol")
    order_parser.add_argument("--side", required=True, help="BUY or SELL")
    order_parser.add_argument("--type", required=True, dest="order_type", help="MARKET or LIMIT")
    order_parser.add_argument("--quantity", required=True, help="Order quantity")
    order_parser.add_argument("--price", help="Limit price for LIMIT orders")

    return parser


def _read_api_credentials() -> tuple[str, str]:
    """Read Binance testnet credentials from the environment."""

    api_key = os.getenv("BINANCE_TESTNET_API_KEY", "").strip()
    secret_key = os.getenv("BINANCE_TESTNET_SECRET_KEY", "").strip()

    if not api_key or not secret_key:
        raise RuntimeError(
            "Missing BINANCE_TESTNET_API_KEY or BINANCE_TESTNET_SECRET_KEY in the environment"
        )

    return api_key, secret_key


def _read_runtime_settings() -> tuple[str, float]:
    """Read optional client settings from the environment."""

    base_url = os.getenv(
        "BINANCE_TESTNET_BASE_URL",
        "https://testnet.binancefuture.com",
    ).strip()

    timeout_raw = os.getenv("BINANCE_TESTNET_TIMEOUT", "10").strip()
    try:
        timeout = float(timeout_raw)
    except ValueError as exc:
        raise RuntimeError("BINANCE_TESTNET_TIMEOUT must be a number") from exc

    if timeout <= 0:
        raise RuntimeError("BINANCE_TESTNET_TIMEOUT must be greater than 0")

    return base_url, timeout


def _print_order_result(order_request, order_response: dict[str, object]) -> None:
    """Print a concise order summary and the raw response payload."""

    summary = extract_order_summary(order_response)
    print("Order placed successfully")
    print(f"Symbol: {order_request.symbol}")
    print(f"Side: {order_request.side}")
    print(f"Type: {order_request.order_type}")
    print(f"Quantity: {order_request.quantity}")
    if order_request.price is not None:
        print(f"Price: {order_request.price}")
    print(f"Order ID: {summary.order_id}")
    print(f"Status: {summary.status}")
    print(f"Executed Qty: {summary.executed_qty}")
    print(f"Average Price: {summary.avg_price}")
    print(f"Limit/Order Price: {summary.price}")
    print("Raw Response:")
    print(json.dumps(order_response, indent=2, sort_keys=True, default=str))


def main(argv: Sequence[str] | None = None) -> int:
    """Execute the trading bot CLI."""

    _load_environment()
    logger = configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command != "order":
        parser.error("Unsupported command")

    try:
        order_request = validate_order_request(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )

        api_key, secret_key = _read_api_credentials()
        base_url, timeout = _read_runtime_settings()
        client = BinanceTestnetClient(
            api_key=api_key,
            secret_key=secret_key,
            base_url=base_url,
            timeout=timeout,
        )
        logger.info("Validated order request: %s", order_request)
        order_response = place_order(client, order_request)
        logger.info("Order response received: %s", order_response)
        _print_order_result(order_request, order_response)
        return 0
    except ValidationError as exc:
        logger.error("Validation failure: %s", exc)
        print(f"Validation error: {exc}", file=sys.stderr)
        return 2
    except BinanceAPIError as exc:
        logger.error("Binance API failure: %s", exc, exc_info=True)
        print(f"Binance API error: {exc}", file=sys.stderr)
        return 3
    except BinanceRequestError as exc:
        logger.error("Network failure: %s", exc, exc_info=True)
        print(f"Network error: {exc}", file=sys.stderr)
        return 4
    except RuntimeError as exc:
        logger.error("Configuration failure: %s", exc)
        print(str(exc), file=sys.stderr)
        return 5
    except KeyboardInterrupt:
        print("Cancelled by user", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
