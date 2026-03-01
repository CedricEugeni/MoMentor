"""Market data service using Yahoo Finance"""
import logging
import yfinance as yf
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models import PriceCache

logger = logging.getLogger(__name__)


class MarketDataUnavailableError(Exception):
    """Exception raised when market data cannot be fetched"""
    pass


class MarketDataService:
    """Service for fetching and caching stock prices"""
    
    def __init__(self, db: Session):
        self.db = db
        self._memory_cache: Dict[str, tuple[Decimal, datetime]] = {}
        self._cache_duration = timedelta(minutes=5)
    
    def get_quotes(self, symbols: List[str]) -> Dict[str, Decimal]:
        """
        Get current prices for a list of symbols
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbol to price in USD
            
        Raises:
            MarketDataUnavailableError: If prices cannot be fetched
        """
        result = {}
        symbols_to_fetch = []
        
        # Check memory cache first
        now = datetime.utcnow()
        for symbol in symbols:
            if symbol in self._memory_cache:
                price, timestamp = self._memory_cache[symbol]
                if now - timestamp < self._cache_duration:
                    result[symbol] = price
                    continue
            symbols_to_fetch.append(symbol)
        
        # Fetch remaining symbols from Yahoo Finance
        if symbols_to_fetch:
            fetched_prices = self._fetch_from_yahoo(symbols_to_fetch)
            result.update(fetched_prices)
            
            # Update memory cache and database cache
            for symbol, price in fetched_prices.items():
                self._memory_cache[symbol] = (price, now)
                self._save_to_cache(symbol, price, now)
        
        return result

    def get_eur_usd_rate(self) -> Decimal:
        """Get EUR/USD FX rate (USD per 1 EUR) with cache fallback."""
        fx_symbol = "EURUSD=X"

        try:
            prices = self.get_quotes([fx_symbol])
            fx_rate = prices.get(fx_symbol)
            if fx_rate and fx_rate > 0:
                return fx_rate
        except Exception:
            pass

        cached = self._get_from_cache(fx_symbol)
        if cached and cached > 0:
            return cached

        raise MarketDataUnavailableError("Failed to fetch EUR/USD rate")
    
    def _fetch_from_yahoo(self, symbols: List[str], retry_count: int = 2) -> Dict[str, Decimal]:
        """
        Fetch prices from Yahoo Finance with retry logic
        
        Args:
            symbols: List of stock symbols
            retry_count: Number of retries on failure
            
        Returns:
            Dictionary mapping symbol to price
            
        Raises:
            MarketDataUnavailableError: If all retries fail
        """
        def _extract_close(history, symbol: str):
            if history is None or getattr(history, "empty", True):
                return None

            try:
                if hasattr(history.columns, "levels"):
                    close_level_index = None
                    if hasattr(history.columns, "names") and history.columns.names:
                        for idx, name in enumerate(history.columns.names):
                            if name == "Price":
                                close_level_index = idx
                                break

                    if close_level_index is None:
                        if "Close" in history.columns.levels[-1]:
                            close_level_index = -1
                        elif "Close" in history.columns.levels[0]:
                            close_level_index = 0
                        else:
                            return None

                    if close_level_index == 0:
                        close_data = history["Close"]
                    else:
                        close_data = history.xs("Close", level=close_level_index, axis=1)

                    if hasattr(close_data, "columns") and symbol in close_data.columns:
                        series = close_data[symbol]
                    else:
                        series = close_data
                else:
                    if "Close" not in history.columns:
                        return None
                    series = history["Close"]

                if getattr(series, "empty", True):
                    return None

                return series.iloc[-1]
            except Exception:
                return None

        for attempt in range(retry_count):
            try:
                prices = {}
                missing = []

                logger.warning("Yahoo fetch attempt %s for symbols=%s", attempt + 1, symbols)

                for symbol in symbols:
                    price = None
                    ticker = yf.Ticker(symbol)

                    # Fast path: avoid heavy info requests
                    try:
                        fast_info = ticker.fast_info
                        if fast_info:
                            price = (
                                fast_info.get("last_price")
                                or fast_info.get("regular_market_price")
                                or fast_info.get("previous_close")
                            )
                            logger.warning("Yahoo fast_info %s last=%s regular=%s prev=%s", symbol, fast_info.get("last_price"), fast_info.get("regular_market_price"), fast_info.get("previous_close"))
                    except Exception as exc:
                        logger.warning("Yahoo fast_info error for %s: %s", symbol, exc)
                        price = None

                    if price is None:
                        missing.append(symbol)
                    else:
                        prices[symbol] = Decimal(str(price))

                if missing:
                    logger.warning("Yahoo download fallback for symbols=%s", missing)
                    try:
                        history = yf.download(
                            tickers=" ".join(missing),
                            period="1d",
                            interval="1d",
                            group_by="ticker",
                            auto_adjust=False,
                            threads=False,
                            progress=False,
                        )
                        logger.warning("Yahoo download columns=%s empty=%s", getattr(history, "columns", None), getattr(history, "empty", None))
                        if getattr(history, "empty", False) is False:
                            try:
                                logger.warning("Yahoo download tail=\n%s", history.tail(2))
                            except Exception:
                                logger.warning("Yahoo download tail logging failed")
                    except Exception as exc:
                        logger.warning("Yahoo download error for %s: %s", missing, exc)
                        raise

                    for symbol in missing:
                        price = _extract_close(history, symbol)

                        logger.warning("Yahoo extracted close for %s: %s", symbol, price)

                        if price is None:
                            cached = self._get_from_cache(symbol)
                            if cached:
                                prices[symbol] = cached
                                continue
                            raise ValueError(f"No price available for {symbol}")

                        prices[symbol] = Decimal(str(price))

                return prices
                
            except Exception as e:
                logger.warning("Yahoo fetch attempt %s failed: %s", attempt + 1, e)
                if attempt == retry_count - 1:
                    # Last attempt failed, try database cache for all symbols
                    cached_prices = {}
                    for symbol in symbols:
                        cached = self._get_from_cache(symbol)
                        if cached:
                            cached_prices[symbol] = cached
                    
                    if cached_prices:
                        return cached_prices
                    
                    raise MarketDataUnavailableError(
                        f"Failed to fetch prices after {retry_count} attempts: {str(e)}"
                    )
                
                # Wait before retry (exponential backoff)
                import time
                time.sleep(2 ** attempt)
        
        raise MarketDataUnavailableError("Failed to fetch prices")
    
    def _save_to_cache(self, symbol: str, price: Decimal, timestamp: datetime):
        """Save price to database cache"""
        try:
            cached = self.db.query(PriceCache).filter(PriceCache.symbol == symbol).first()
            if cached:
                cached.price = price
                cached.timestamp = timestamp
            else:
                cached = PriceCache(symbol=symbol, price=price, timestamp=timestamp)
                self.db.add(cached)
            self.db.commit()
        except Exception:
            self.db.rollback()
    
    def _get_from_cache(self, symbol: str) -> Optional[Decimal]:
        """Get price from database cache"""
        try:
            cached = self.db.query(PriceCache).filter(PriceCache.symbol == symbol).first()
            if cached:
                return cached.price
        except Exception:
            pass
        return None
