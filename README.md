# Binance Futures Testnet Trading Bot

A production-oriented Python 3.10+ CLI for placing MARKET and LIMIT orders on the Binance USDT-M Futures Testnet.

## Features

- MARKET and LIMIT orders
- BUY and SELL sides
- Strong input validation for CLI payloads
- Signed Binance Futures API requests using HMAC SHA256
- File logging to `logs/bot.log`
- Clean console summaries for each order

## Project Layout

```text
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py
│   ├── orders.py
│   ├── validators.py
│   └── logging_config.py
├── cli.py
├── .env.example
├── requirements.txt
└── README.md
```

## Binance Testnet Setup

1. Create or sign in to your Binance Futures Testnet account at https://testnet.binancefuture.com.
2. Generate a Futures Testnet API key and secret from your testnet account settings.
3. Fund the testnet account if needed using the Binance Futures Testnet faucet or wallet tools available in the testnet portal.
4. Never reuse live trading credentials in this project. The bot is wired for the testnet endpoint only.

## Installation

### 1. Create a virtual environment

From the workspace root:

```powershell
cd "d:\Simplified Trading Bot\trading_bot"
python -m venv .venv
```

### 2. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

## Environment Configuration

1. Copy `.env.example` to `.env`.
2. Fill in your Binance Futures Testnet API key and secret.

Example `.env`:

```ini
BINANCE_TESTNET_API_KEY=your_testnet_api_key_here
BINANCE_TESTNET_SECRET_KEY=your_testnet_secret_key_here
BINANCE_TESTNET_BASE_URL=https://testnet.binancefuture.com
BINANCE_TESTNET_TIMEOUT=10
```

The CLI loads environment variables with `python-dotenv`.

## Usage

Run all commands from the `trading_bot` directory after activating the virtual environment.

### MARKET BUY

```powershell
python cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### MARKET SELL

```powershell
python cli.py order --symbol BTCUSDT --side SELL --type MARKET --quantity 0.001
```

### LIMIT BUY

```powershell
python cli.py order --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 60000
```

### LIMIT SELL

```powershell
python cli.py order --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 65000
```

## Validation Rules

- `symbol` must be uppercase and contain only letters and digits, for example `BTCUSDT`.
- `side` must be `BUY` or `SELL`.
- `type` must be `MARKET` or `LIMIT`.
- `quantity` must be greater than `0`.
- `price` is required for LIMIT orders and must be greater than `0`.

## Logging

- Application logs are written to `logs/bot.log`.
- The console output prints a concise summary plus the raw order response.
- Request and response payloads are logged for troubleshooting and auditability.

### Inspect Logs

```powershell
Get-Content .\logs\bot.log -Tail 50 -Wait
```

Or open the file directly:

```powershell
notepad .\logs\bot.log
```

## Error Handling

The CLI handles:

- Network and connection failures
- Timeout failures
- Binance API errors such as bad symbol, invalid API key, or insufficient margin
- Input validation errors before the order is sent

## Notes

- This implementation uses direct HTTP requests with HMAC SHA256 signing instead of a wrapper dependency.
- The code is intentionally limited to Binance Futures Testnet order placement and is suitable as a base for a larger trading workflow.
