"""Momentum strategy interface and implementations"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional
import warnings

import yfinance as yf
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup

# Suppress warnings from yfinance for cleaner output
warnings.filterwarnings("ignore", category=FutureWarning)


@dataclass
class Allocation:
    """Stock allocation recommendation"""
    symbol: str
    percentage: Decimal


class MomentumStrategy(ABC):
    """Abstract base class for momentum strategies"""
    
    @abstractmethod
    def get_allocations(
        self,
        capital_usd: Decimal,
        uninvested_cash: Decimal,
        run_date: date
    ) -> List[Allocation]:
        """
        Calculate recommended allocations
        
        Args:
            capital_usd: Total capital to allocate
            uninvested_cash: Current uninvested cash
            run_date: Date of the run
            
        Returns:
            List of allocations with symbol and percentage
        """
        pass


# ============================================================================
# HELPER FUNCTIONS FOR MOMENTUMVOLA ALGORITHM
# ============================================================================

def get_last_closed_month_date(reference_date: Optional[date] = None) -> datetime:
    """
    Calculate the last day of the previous complete month.
    
    Args:
        reference_date: Date to use as reference (defaults to today)
    
    Returns:
        datetime object representing the last day of the previous month
    """
    if reference_date is None:
        today = datetime.now()
    else:
        today = datetime.combine(reference_date, datetime.min.time())
    
    first_of_current_month = today.replace(day=1)
    last_closed_date = first_of_current_month - timedelta(days=1)
    return last_closed_date


def get_index_constituents(url: str, table_id: Optional[str] = None, table_index: int = 0) -> Dict[str, str]:
    """
    Scrape Wikipedia to get index constituents.
    
    Args:
        url: Wikipedia URL to scrape
        table_id: HTML table ID to look for
        table_index: Table index to use as fallback
    
    Returns:
        Dictionary mapping ticker symbols to company names
    """
    TICKER_COL = 'Symbol'
    NAME_COL = 'Security'
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        df = None
        
        # Try by ID first
        if table_id:
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'id': table_id})
            
            if table:
                # Use StringIO to pass HTML string to pandas
                from io import StringIO
                df = pd.read_html(StringIO(str(table)), header=0)[0]
            else:
                print(f"⚠️ Table with ID '{table_id}' not found, trying index {table_index}")
        
        # Fallback to index
        if df is None:
            all_tables = pd.read_html(response.text, header=0)
            
            if table_index >= len(all_tables):
                print(f"❌ Invalid table index {table_index}. Only {len(all_tables)} tables found.")
                return {}
            
            df = all_tables[table_index]
        
        # Normalize column names
        if 'Ticker' in df.columns:
            TICKER_COL = 'Ticker'
        if 'Security' not in df.columns and 'Company' in df.columns:
            NAME_COL = 'Company'
        
        if TICKER_COL in df.columns and NAME_COL in df.columns:
            df[TICKER_COL] = df[TICKER_COL].astype(str).str.replace('.', '-', regex=False).str.strip()
            df[NAME_COL] = df[NAME_COL].astype(str).str.strip()
            
            ticker_map = df.set_index(TICKER_COL)[NAME_COL].to_dict()
            ticker_map = {k: v for k, v in ticker_map.items() if k and v and k != 'nan'}
            
            print(f"✅ Retrieved {len(ticker_map)} tickers from {url}")
            return ticker_map
        else:
            print(f"❌ Required columns not found. Available: {df.columns.tolist()}")
            return {}
            
    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return {}


def check_spy_market_condition() -> bool:
    """
    Check if SPY is above its 220-day moving average.
    
    Returns:
        True if SPY close > SMA220, False otherwise
    """
    try:
        print("🔍 Checking SPY market condition...")
        spy = yf.Ticker("SPY")
        spy_data = spy.history(period="1y", interval="1d")
        
        # Convert to float and drop invalid data
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col in spy_data.columns:
                spy_data[col] = pd.to_numeric(spy_data[col], errors='coerce')
        spy_data.dropna(subset=['Close'], inplace=True)
        
        if len(spy_data) < 220:
            print("⚠️ Insufficient SPY data for 220-day SMA")
            return False
        
        spy_data['SMA_220'] = spy_data['Close'].rolling(window=220).mean()
        
        current_close = spy_data['Close'].iloc[-1]
        sma_220 = spy_data['SMA_220'].iloc[-1]
        
        if current_close > sma_220:
            print(f"✅ SPY ({current_close:.2f}) > SMA220 ({sma_220:.2f})")
            return True
        else:
            print(f"❌ SPY ({current_close:.2f}) < SMA220 ({sma_220:.2f})")
            return False
            
    except Exception as e:
        print(f"❌ Error checking SPY condition: {e}")
        return False


def calculate_wilder_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calculate Wilder's Average True Range (ATR).
    
    Args:
        df: DataFrame with High, Low, Close columns
        period: ATR period
    
    Returns:
        DataFrame with added ATR column
    """
    df_copy = df.copy()
    
    df_copy.loc[:, 'high-low'] = df_copy['High'] - df_copy['Low']
    df_copy.loc[:, 'high-prevclose'] = abs(df_copy['High'] - df_copy['Close'].shift(1))
    df_copy.loc[:, 'low-prevclose'] = abs(df_copy['Low'] - df_copy['Close'].shift(1))
    
    df_copy.loc[:, 'true_range'] = df_copy[['high-low', 'high-prevclose', 'low-prevclose']].max(axis=1)
    df_copy.loc[:, 'atr'] = df_copy['true_range'].ewm(alpha=1/period, adjust=False).mean()
    
    return df_copy


def calculate_momentum_vola(ticker: str, end_date: datetime) -> Optional[float]:
    """
    Calculate MomentumVola score for a ticker.
    
    Args:
        ticker: Stock symbol
        end_date: End date for calculation (last closed month)
    
    Returns:
        MomentumVola score or None if calculation fails
    """
    try:
        start_date = end_date - timedelta(days=913)  # 2.5 years
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # Get daily data
        data_daily = yf.Ticker(ticker).history(start=start_date_str, end=end_date_str, interval="1d")
        
        if len(data_daily) < 100:  # Need at least ~100 days of data
            return None
        
        # Convert to float and clean
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col in data_daily.columns:
                data_daily[col] = pd.to_numeric(data_daily[col], errors='coerce')
        data_daily.dropna(subset=['Close', 'High', 'Low'], inplace=True)
        
        if len(data_daily) < 100:  # Check again after cleaning
            return None
        
        # Resample to monthly (last trading day of each month)
        data_mo = data_daily.resample('ME').last().dropna()  # Changed 'M' to 'ME' (month end)
        
        if len(data_mo) < 8:
            return None
        
        # Calculate momentum (average of last 3 monthly returns)
        data_mo.loc[:, 'monthly_return'] = data_mo['Close'].pct_change()
        momentum = data_mo['monthly_return'].iloc[-3:].mean()
        
        # Calculate ATR-based volatility
        data_mo_with_atr = calculate_wilder_atr(data_mo, period=8)
        df_vol_period = data_mo_with_atr.iloc[-8:]
        volatility = df_vol_period['atr'].mean()
        
        if volatility == 0 or pd.isna(volatility) or pd.isna(momentum):
            return None
        
        score = momentum / volatility
        return score
        
    except Exception as e:
        # Uncomment for debugging:
        # print(f"  Error calculating {ticker}: {e}")
        return None


# ============================================================================
# MOMENTUMVOLA STRATEGY IMPLEMENTATION
# ============================================================================

class MomentumVolaStrategy(MomentumStrategy):
    """
    MomentumVola strategy based on:
    1. Common stocks between S&P 500 and NASDAQ-100
    2. SPY market condition filter (above 220-day MA)
    3. Stock filter by 220-day MA
    4. MomentumVola scoring (momentum / volatility)
    5. Portfolio: 30% ETF + 70% split across top 4 stocks
    """
    
    ETF_SYMBOL = "IE00B5BMR087"  # Vanguard S&P 500 UCITS ETF
    ETF_ALLOCATION = Decimal("0.30")  # 30%
    
    def get_allocations(
        self,
        capital_usd: Decimal,
        uninvested_cash: Decimal,
        run_date: date
    ) -> List[Allocation]:
        """Calculate allocations using MomentumVola algorithm"""
        
        print("="*80)
        print("🚀 Starting MomentumVola algorithm...")
        
        # Step 1: Get last closed month date
        last_closed_date = get_last_closed_month_date(run_date)
        print(f"📅 Reference date: {last_closed_date.strftime('%Y-%m-%d')}")
        
        # Step 2: Get index constituents
        sp500_url = 'https://en.wikipedia.org/wiki/List_of_S&P_500_companies'
        nasdaq100_url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
        
        sp500_map = get_index_constituents(sp500_url, table_id="constituents")
        nasdaq100_map = get_index_constituents(nasdaq100_url, table_id="constituents")
        
        sp500_tickers = set(sp500_map.keys())
        nasdaq100_tickers = set(nasdaq100_map.keys())
        
        common_tickers = sp500_tickers.intersection(nasdaq100_tickers)
        
        # Exclude GOOGL (keep only GOOG)
        if 'GOOGL' in common_tickers:
            common_tickers.remove('GOOGL')
        
        if not common_tickers:
            raise ValueError("No common stocks found between S&P 500 and NASDAQ-100")
        
        print(f"✅ Found {len(common_tickers)} common stocks")
        
        # Step 3: Check SPY market condition
        if not check_spy_market_condition():
            raise ValueError("SPY is below its 220-day moving average. Market condition not met.")
        
        # Step 4: Filter stocks by 220-day MA
        print("🔍 Filtering stocks by 220-day moving average...")
        filtered_stocks = []
        
        for ticker in common_tickers:
            try:
                data = yf.Ticker(ticker).history(period="1y", interval="1d")
                
                for col in ['Close']:
                    if col in data.columns:
                        data[col] = pd.to_numeric(data[col], errors='coerce')
                data.dropna(subset=['Close'], inplace=True)
                
                if len(data) >= 220:
                    data['SMA_220'] = data['Close'].rolling(window=220).mean()
                    if data['Close'].iloc[-1] > data['SMA_220'].iloc[-1]:
                        filtered_stocks.append(ticker)
            except Exception:
                pass
        
        if not filtered_stocks:
            raise ValueError("No stocks passed the 220-day MA filter")
        
        print(f"✅ {len(filtered_stocks)} stocks passed the 220-day MA filter")
        
        # Step 5: Calculate MomentumVola scores
        print("🔍 Calculating MomentumVola scores...")
        scores = {}
        
        for ticker in filtered_stocks:
            score = calculate_momentum_vola(ticker, last_closed_date)
            if score is not None:
                scores[ticker] = score
        
        if not scores:
            raise ValueError("Unable to calculate MomentumVola scores for any stocks")
        
        # Step 6: Rank and select top 4
        ranked_tickers = sorted(scores, key=scores.get, reverse=True)
        top_4_tickers = ranked_tickers[:4]
        
        if len(top_4_tickers) < 4:
            print(f"⚠️ Only {len(top_4_tickers)} stocks available (expected 4)")
        
        print(f"✅ Top stocks selected: {', '.join(top_4_tickers)}")
        
        # Step 7: Build portfolio allocations
        allocations = []
        
        # ETF allocation (30%)
        allocations.append(Allocation(
            symbol=self.ETF_SYMBOL,
            percentage=self.ETF_ALLOCATION
        ))
        
        # Stock allocations (70% split equally)
        stock_allocation_total = Decimal("1.00") - self.ETF_ALLOCATION
        
        if len(top_4_tickers) > 0:
            per_stock = stock_allocation_total / len(top_4_tickers)
            
            # Quantize to 4 decimal places
            precision = Decimal("0.0001")
            allocated = Decimal("0")
            
            for i, ticker in enumerate(top_4_tickers):
                if i < len(top_4_tickers) - 1:
                    alloc = per_stock.quantize(precision, rounding=ROUND_DOWN)
                    allocations.append(Allocation(symbol=ticker, percentage=alloc))
                    allocated += alloc
                else:
                    # Last stock gets the remainder to ensure total = 100%
                    remainder = Decimal("1.00") - self.ETF_ALLOCATION - allocated
                    allocations.append(Allocation(symbol=ticker, percentage=remainder))
        
        print(f"✅ Portfolio built: {len(allocations)} positions")
        print("="*80)
        
        return allocations


# Default strategy to use
def get_strategy() -> MomentumStrategy:
    """Get the current momentum strategy instance"""
    return MomentumVolaStrategy()
