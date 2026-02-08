from __future__ import annotations

import json
from datetime import datetime

import yfinance as yf


def _print_title(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main() -> None:
    symbol = "AAPL"
    _print_title(f"yfinance debug for {symbol} at {datetime.utcnow().isoformat()}Z")

    ticker = yf.Ticker(symbol)

    _print_title("fast_info")
    try:
        fast_info = ticker.fast_info
        print(json.dumps(dict(fast_info), indent=2, default=str))
    except Exception as exc:
        print(f"fast_info error: {exc}")

    _print_title("history (period=1d)")
    try:
        hist = ticker.history(period="1d")
        print(hist.tail(3))
    except Exception as exc:
        print(f"history error: {exc}")

    _print_title("download (period=1d, interval=1d)")
    try:
        data = yf.download(
            tickers=symbol,
            period="1d",
            interval="1d",
            group_by="ticker",
            auto_adjust=False,
            threads=False,
            progress=False,
        )
        print(data.tail(3))
    except Exception as exc:
        print(f"download error: {exc}")


if __name__ == "__main__":
    main()
