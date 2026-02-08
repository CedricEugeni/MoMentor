"""Rebalancing service for calculating optimized moves"""
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app.models import ActualPosition
from app.algo.strategy import Allocation


@dataclass
class CashflowMove:
    """Move with cash flow (sell then buy)"""
    symbol: str
    action: str  # SELL or BUY
    suggested_shares: int
    suggested_value_usd: Decimal
    order_index: int


@dataclass
class SwapMove:
    """Move with direct swap"""
    from_symbol: Optional[str]
    to_symbol: Optional[str]
    swap_shares_from: Optional[int]
    swap_shares_to: Optional[int]
    swap_value_usd: Decimal
    order_index: int
    description: str


class RebalancingService:
    """Service for calculating rebalancing moves"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_cashflow_moves(
        self,
        previous_positions: List[ActualPosition],
        target_allocations: List[Allocation],
        current_prices: Dict[str, Decimal],
        total_capital: Decimal
    ) -> List[CashflowMove]:
        """
        Calculate optimized moves using cash flow approach
        All sells first, then all buys
        
        Args:
            previous_positions: Current positions
            target_allocations: Target allocations from algorithm
            current_prices: Current prices for all symbols
            total_capital: Total capital to allocate
            
        Returns:
            List of cashflow moves ordered (sells first, then buys)
        """
        moves = []
        order_index = 1
        
        # Build current holdings map
        current_holdings = {
            pos.symbol: {
                "shares": pos.actual_shares,
                "value": Decimal(pos.actual_shares) * current_prices.get(pos.symbol, pos.actual_avg_price_usd)
            }
            for pos in previous_positions
        }
        
        # Build target holdings map
        target_holdings = {}
        for allocation in target_allocations:
            target_value = total_capital * allocation.percentage
            price = current_prices.get(allocation.symbol, Decimal("0"))
            if price > 0:
                target_shares = int(target_value / price)
                target_holdings[allocation.symbol] = {
                    "shares": target_shares,
                    "value": Decimal(target_shares) * price
                }
        
        # Phase 1: Generate SELL moves for positions to reduce or eliminate
        for symbol, current in current_holdings.items():
            target = target_holdings.get(symbol)
            
            if target is None:
                # Sell entire position
                price = current_prices.get(symbol, Decimal("0"))
                moves.append(CashflowMove(
                    symbol=symbol,
                    action="SELL",
                    suggested_shares=current["shares"],
                    suggested_value_usd=current["value"],
                    order_index=order_index
                ))
                order_index += 1
            elif target["shares"] < current["shares"]:
                # Sell partial position
                shares_to_sell = current["shares"] - target["shares"]
                price = current_prices.get(symbol, Decimal("0"))
                value = Decimal(shares_to_sell) * price
                moves.append(CashflowMove(
                    symbol=symbol,
                    action="SELL",
                    suggested_shares=shares_to_sell,
                    suggested_value_usd=value,
                    order_index=order_index
                ))
                order_index += 1
        
        # Phase 2: Generate BUY moves for positions to increase or create
        for symbol, target in target_holdings.items():
            current = current_holdings.get(symbol)
            
            if current is None:
                # Buy new position
                moves.append(CashflowMove(
                    symbol=symbol,
                    action="BUY",
                    suggested_shares=target["shares"],
                    suggested_value_usd=target["value"],
                    order_index=order_index
                ))
                order_index += 1
            elif target["shares"] > current["shares"]:
                # Buy additional shares
                shares_to_buy = target["shares"] - current["shares"]
                price = current_prices.get(symbol, Decimal("0"))
                value = Decimal(shares_to_buy) * price
                moves.append(CashflowMove(
                    symbol=symbol,
                    action="BUY",
                    suggested_shares=shares_to_buy,
                    suggested_value_usd=value,
                    order_index=order_index
                ))
                order_index += 1
        
        return moves
    
    def calculate_swap_moves(
        self,
        previous_positions: List[ActualPosition],
        target_allocations: List[Allocation],
        current_prices: Dict[str, Decimal],
        total_capital: Decimal
    ) -> List[SwapMove]:
        """
        Calculate optimized moves using swap approach (greedy algorithm)
        Try to match sells with buys directly
        
        Args:
            previous_positions: Current positions
            target_allocations: Target allocations from algorithm
            current_prices: Current prices for all symbols
            total_capital: Total capital to allocate
            
        Returns:
            List of swap moves
        """
        moves = []
        order_index = 1
        
        # Build current and target holdings
        current_holdings = {
            pos.symbol: {
                "shares": pos.actual_shares,
                "value": Decimal(pos.actual_shares) * current_prices.get(pos.symbol, pos.actual_avg_price_usd)
            }
            for pos in previous_positions
        }
        
        target_holdings = {}
        for allocation in target_allocations:
            target_value = total_capital * allocation.percentage
            price = current_prices.get(allocation.symbol, Decimal("0"))
            if price > 0:
                target_shares = int(target_value / price)
                target_holdings[allocation.symbol] = {
                    "shares": target_shares,
                    "value": Decimal(target_shares) * price
                }
        
        # Identify excess (to sell) and deficit (to buy)
        excess = []  # [(symbol, shares, value)]
        deficit = []  # [(symbol, shares, value)]
        
        # Find positions to reduce or eliminate
        for symbol, current in current_holdings.items():
            target = target_holdings.get(symbol, {"shares": 0, "value": Decimal("0")})
            if current["shares"] > target["shares"]:
                diff_shares = current["shares"] - target["shares"]
                price = current_prices.get(symbol, Decimal("0"))
                diff_value = Decimal(diff_shares) * price
                excess.append((symbol, diff_shares, diff_value))
        
        # Find positions to increase or create
        for symbol, target in target_holdings.items():
            current = current_holdings.get(symbol, {"shares": 0, "value": Decimal("0")})
            if target["shares"] > current["shares"]:
                diff_shares = target["shares"] - current["shares"]
                diff_value = target["value"] - current["value"]
                deficit.append((symbol, diff_shares, diff_value))
        
        # Sort by value (greedy: match largest first)
        excess.sort(key=lambda x: x[2], reverse=True)
        deficit.sort(key=lambda x: x[2], reverse=True)
        
        # Match excess with deficit
        for from_symbol, from_shares, from_value in excess:
            if deficit:
                to_symbol, to_shares, to_value = deficit.pop(0)
                moves.append(SwapMove(
                    from_symbol=from_symbol,
                    to_symbol=to_symbol,
                    swap_shares_from=from_shares,
                    swap_shares_to=to_shares,
                    swap_value_usd=min(from_value, to_value),
                    order_index=order_index,
                    description=f"Vendre {from_shares} {from_symbol} → Acheter {to_shares} {to_symbol}"
                ))
                order_index += 1
            else:
                # No more deficit, just sell
                moves.append(SwapMove(
                    from_symbol=from_symbol,
                    to_symbol=None,
                    swap_shares_from=from_shares,
                    swap_shares_to=None,
                    swap_value_usd=from_value,
                    order_index=order_index,
                    description=f"Vendre {from_shares} {from_symbol}"
                ))
                order_index += 1
        
        # Handle remaining deficit (pure buys)
        for to_symbol, to_shares, to_value in deficit:
            moves.append(SwapMove(
                from_symbol=None,
                to_symbol=to_symbol,
                swap_shares_from=None,
                swap_shares_to=to_shares,
                swap_value_usd=to_value,
                order_index=order_index,
                description=f"Acheter {to_shares} {to_symbol}"
            ))
            order_index += 1
        
        return moves
