"""Streamlit dashboard for the Binance Futures Trading Bot."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv

from bot.client import BinanceAPIError, BinanceRequestError, BinanceTestnetClient
from bot.logging_config import configure_logging
from bot.orders import OrderRequest, place_order
from bot.validators import ValidationError, validate_order_request


PROJECT_ROOT = Path(__file__).resolve().parent
LOG_FILE = PROJECT_ROOT / "logs" / "bot.log"


def load_environment() -> None:
    """Load API credentials from the project .env file if it exists."""

    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)


def read_runtime_settings() -> tuple[str, float]:
    """Read optional client settings from environment variables."""

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


def build_client() -> BinanceTestnetClient:
    """Create the Binance Testnet client from environment variables."""

    api_key = os.getenv("BINANCE_TESTNET_API_KEY", "").strip()
    secret_key = os.getenv("BINANCE_TESTNET_SECRET_KEY", "").strip()

    if not api_key or not secret_key:
        raise RuntimeError(
            "Missing BINANCE_TESTNET_API_KEY or BINANCE_TESTNET_SECRET_KEY in the environment"
        )

    base_url, timeout = read_runtime_settings()
    return BinanceTestnetClient(
        api_key=api_key,
        secret_key=secret_key,
        base_url=base_url,
        timeout=timeout,
    )


def render_log_viewer() -> None:
    """Render the current bot log file contents."""

    st.subheader("Live Log Viewer")
    st.caption("Reads from logs/bot.log")

    if not LOG_FILE.exists():
        st.info("No log file found yet. Run an order to generate logs/bot.log.")
        return

    log_text = LOG_FILE.read_text(encoding="utf-8", errors="replace")
    st.code(log_text or "(log file is empty)", language="text")


def render_dashboard() -> None:
    """Render the trading interface and handle order placement."""

    st.set_page_config(page_title="Binance Futures Trading Bot", page_icon="📈", layout="wide")
    load_environment()
    configure_logging()

    st.title("Binance Futures Trading Bot")
    st.write("Place Binance Futures Testnet orders from a clean Streamlit dashboard.")

    with st.sidebar:
        st.header("Order Controls")
        symbol = st.text_input("Symbol", value="BTCUSDT")
        side = st.selectbox("Side", options=["BUY", "SELL"])
        order_type = st.selectbox("Order Type", options=["MARKET", "LIMIT"])
        quantity = st.number_input(
            "Quantity",
            min_value=0.0,
            value=0.001,
            step=0.001,
            format="%.8f",
        )
        price = None
        if order_type == "LIMIT":
            price = st.number_input(
                "Price",
                min_value=0.00000001,
                value=1.0,
                step=0.1,
                format="%.8f",
            )

        submit_order = st.button("Place Order", type="primary", use_container_width=True)

    col_left, col_right = st.columns([1.2, 0.8], gap="large")

    with col_left:
        st.subheader("Order Form")
        st.write("The dashboard reuses the existing trading bot modules directly.")
        st.json(
            {
                "symbol": symbol,
                "side": side,
                "order_type": order_type,
                "quantity": quantity,
                "price": price if order_type == "LIMIT" else None,
            }
        )

    with col_right:
        st.subheader("Execution Notes")
        st.info("MARKET orders ignore the price field. LIMIT orders require a positive price.")

    if submit_order:
        try:
            normalized_order: OrderRequest = validate_order_request(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=str(quantity),
                price=str(price) if order_type == "LIMIT" else None,
            )
            client = build_client()
            response = place_order(client, normalized_order)

            st.success("Order placed successfully.")
            st.subheader("Order Response")
            st.json(response)

            summary = {
                "orderId": response.get("orderId"),
                "status": response.get("status"),
                "executedQty": response.get("executedQty"),
                "avgPrice": response.get("avgPrice"),
                "price": response.get("price"),
            }
            st.code(json.dumps(summary, indent=2), language="json")
        except ValidationError as exc:
            st.error(f"Validation error: {exc}")
        except BinanceAPIError as exc:
            st.error(f"Binance API error: {exc}")
            st.code(json.dumps(getattr(exc, "payload", {}), indent=2, default=str), language="json")
        except BinanceRequestError as exc:
            st.error(f"Network error: {exc}")
        except RuntimeError as exc:
            st.error(str(exc))
        except Exception as exc:  # noqa: BLE001
            st.error(f"Unexpected error: {exc}")

    st.divider()
    render_log_viewer()


render_dashboard()