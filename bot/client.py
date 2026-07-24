"""Binance Futures Testnet HTTP client wrapper."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlencode

import requests

LOGGER = logging.getLogger(__name__)


class BinanceClientError(Exception):
    """Base class for client-related failures."""


@dataclass(slots=True)
class BinanceAPIError(BinanceClientError):
    """Raised when Binance returns an API-level error response."""

    code: int
    message: str
    status_code: int | None = None
    payload: Any | None = None

    def __str__(self) -> str:
        if self.status_code is None:
            return f"Binance API error {self.code}: {self.message}"
        return f"Binance API error {self.code} (HTTP {self.status_code}): {self.message}"


@dataclass(slots=True)
class BinanceRequestError(BinanceClientError):
    """Raised when a network or transport-level failure occurs."""

    message: str

    def __str__(self) -> str:
        return self.message


class BinanceTestnetClient:
    """HTTP client for Binance USDT-M Futures Testnet endpoints.

    The class performs direct signed HTTP requests and surfaces predictable
    exceptions for the CLI layer to handle cleanly.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        base_url: str = "https://testnet.binancefuture.com",
        timeout: float = 10.0,
        recv_window: int = 5000,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        if not secret_key:
            raise ValueError("secret_key is required")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.recv_window = recv_window
        self.secret_key = secret_key.encode("utf-8")
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": api_key})

    def _sign(self, params: Mapping[str, Any]) -> str:
        query_string = urlencode(params, doseq=True)
        signature = hmac.new(
            self.secret_key,
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    @staticmethod
    def _serialize_params(params: Mapping[str, Any] | None) -> dict[str, Any]:
        serialized: dict[str, Any] = {}
        if not params:
            return serialized

        for key, value in params.items():
            if value is None:
                continue
            serialized[key] = value
        return serialized

    def _parse_response(self, response: requests.Response) -> Any:
        try:
            payload = response.json()
        except ValueError:
            payload = response.text

        LOGGER.info(
            "Binance response status=%s body=%s",
            response.status_code,
            payload,
        )

        if response.status_code >= 400:
            if isinstance(payload, dict):
                code = int(payload.get("code", response.status_code))
                message = str(payload.get("msg", payload))
            else:
                code = response.status_code
                message = str(payload)
            raise BinanceAPIError(
                code=code,
                message=message,
                status_code=response.status_code,
                payload=payload,
            )

        if isinstance(payload, dict) and payload.get("code") not in (None, 0):
            raise BinanceAPIError(
                code=int(payload.get("code", -1)),
                message=str(payload.get("msg", payload)),
                status_code=response.status_code,
                payload=payload,
            )

        return payload

    def _request(
        self,
        method: str,
        path: str,
        params: Mapping[str, Any] | None = None,
        signed: bool = False,
    ) -> Any:
        clean_params = self._serialize_params(params)
        request_params = dict(clean_params)

        if signed:
            request_params["timestamp"] = int(time.time() * 1000)
            request_params["recvWindow"] = self.recv_window
            request_params["signature"] = self._sign(request_params)

        url = f"{self.base_url}{path}"
        LOGGER.info(
            "Binance request method=%s url=%s params=%s signed=%s",
            method,
            url,
            request_params if signed else clean_params,
            signed,
        )

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=request_params if request_params else None,
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            raise BinanceRequestError(
                "Request timed out while contacting Binance Testnet"
            ) from exc
        except requests.ConnectionError as exc:
            raise BinanceRequestError(
                "Connection error while contacting Binance Testnet"
            ) from exc
        except requests.RequestException as exc:
            raise BinanceRequestError(f"Unexpected request failure: {exc}") from exc

        LOGGER.info(
            "Binance raw response status=%s text=%s",
            response.status_code,
            response.text,
        )
        return self._parse_response(response)

    def create_futures_order(self, **payload: Any) -> dict[str, Any]:
        """Place a signed USDT-M futures order on the testnet."""

        response = self._request(
            method="POST",
            path="/fapi/v1/order",
            params=payload,
            signed=True,
        )
        if not isinstance(response, dict):
            raise BinanceRequestError("Unexpected non-JSON response from Binance")
        return response
