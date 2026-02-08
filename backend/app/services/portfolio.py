"""Portfolio calculation service"""
from decimal import Decimal
from typing import Tuple
from sqlalchemy.orm import Session

from app.models import AlgorithmRun, ActualPosition, ActualCash, RunStatus
from app.services.market_data import MarketDataService


class PortfolioService:
    """Service for portfolio calculations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.market_data_service = MarketDataService(db)
    
    def calculate_next_capital(self) -> Tuple[Decimal, Decimal]:
        """
        Calculate capital for next algorithm run
        
        Returns:
            Tuple of (total_capital_usd, uninvested_cash_usd)
        """
        # Get the last completed run
        last_run = (
            self.db.query(AlgorithmRun)
            .filter(AlgorithmRun.status == RunStatus.COMPLETED)
            .order_by(AlgorithmRun.run_date.desc())
            .first()
        )
        
        if not last_run:
            # No previous runs, return default
            return Decimal("0"), Decimal("0")
        
        # Get actual positions for the last run
        actual_positions = last_run.actual_positions
        actual_cash = last_run.actual_cash
        
        if not actual_positions and not actual_cash:
            # No actual data provided, use theoretical values
            return last_run.total_capital_usd, last_run.uninvested_cash_usd
        
        # Calculate current portfolio value with live prices
        total_value = Decimal("0")
        
        if actual_positions:
            symbols = [pos.symbol for pos in actual_positions]
            try:
                current_prices = self.market_data_service.get_quotes(symbols)
                
                for position in actual_positions:
                    current_price = current_prices.get(position.symbol)
                    if current_price:
                        position_value = Decimal(position.actual_shares) * current_price
                        total_value += position_value
            except Exception:
                # If prices unavailable, use stored values
                for position in actual_positions:
                    total_value += position.total_value_usd
        
        # Add uninvested cash
        uninvested_cash = actual_cash.uninvested_cash_usd if actual_cash else Decimal("0")
        total_capital = total_value + uninvested_cash
        
        return total_capital, uninvested_cash
    
    def get_current_portfolio_value(self) -> dict:
        """
        Get current portfolio value with PnL calculations
        
        Returns:
            Dictionary with portfolio details and PnL
        """
        # Get the last completed run
        last_run = (
            self.db.query(AlgorithmRun)
            .filter(AlgorithmRun.status == RunStatus.COMPLETED)
            .order_by(AlgorithmRun.run_date.desc())
            .first()
        )
        
        if not last_run:
            return {
                "has_portfolio": False,
                "message": "No confirmed portfolio yet"
            }
        
        actual_positions = last_run.actual_positions
        actual_cash = last_run.actual_cash
        
        if not actual_positions and not actual_cash:
            return {
                "has_portfolio": False,
                "message": "No actual positions confirmed for the last run"
            }
        
        # Get current prices
        symbols = [pos.symbol for pos in actual_positions] if actual_positions else []
        current_prices = {}
        
        if symbols:
            try:
                current_prices = self.market_data_service.get_quotes(symbols)
            except Exception as e:
                return {
                    "has_portfolio": True,
                    "error": f"Cannot fetch current prices: {str(e)}",
                    "positions": []
                }
        
        # Calculate PnL for each position
        positions_data = []
        total_current_value = Decimal("0")
        total_entry_value = Decimal("0")
        
        for position in actual_positions:
            current_price = current_prices.get(position.symbol, position.actual_avg_price_usd)
            current_value = Decimal(position.actual_shares) * current_price
            entry_value = position.total_value_usd
            
            pnl_usd = current_value - entry_value
            pnl_percent = (pnl_usd / entry_value * 100) if entry_value > 0 else Decimal("0")
            
            positions_data.append({
                "symbol": position.symbol,
                "shares": position.actual_shares,
                "entry_price": float(position.actual_avg_price_usd),
                "current_price": float(current_price),
                "entry_value": float(entry_value),
                "current_value": float(current_value),
                "pnl_usd": float(pnl_usd),
                "pnl_percent": float(pnl_percent)
            })
            
            total_current_value += current_value
            total_entry_value += entry_value
        
        # Add cash
        uninvested_cash = actual_cash.uninvested_cash_usd if actual_cash else Decimal("0")
        total_current_value += uninvested_cash
        total_entry_value += uninvested_cash
        
        # Calculate total PnL
        total_pnl_usd = total_current_value - total_entry_value
        total_pnl_percent = (total_pnl_usd / total_entry_value * 100) if total_entry_value > 0 else Decimal("0")
        
        return {
            "has_portfolio": True,
            "run_id": last_run.id,
            "run_date": last_run.run_date.isoformat(),
            "validation_date": actual_positions[0].first_validation_date.isoformat() if actual_positions else None,
            "positions": positions_data,
            "uninvested_cash": float(uninvested_cash),
            "total_entry_value": float(total_entry_value),
            "total_current_value": float(total_current_value),
            "total_pnl_usd": float(total_pnl_usd),
            "total_pnl_percent": float(total_pnl_percent)
        }
