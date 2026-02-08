"""Momentum strategy interface and implementations"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from datetime import date
from typing import List


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


class AppleOnlyStrategy(MomentumStrategy):
    """
    Stub strategy that always recommends 100% AAPL
    This is a placeholder for testing purposes
    """
    
    def get_allocations(
        self,
        capital_usd: Decimal,
        uninvested_cash: Decimal,
        run_date: date
    ) -> List[Allocation]:
        """Always allocate 100% to Apple (AAPL)"""
        return [
            Allocation(symbol="AAPL", percentage=Decimal("1.0"))
        ]


# Default strategy to use
def get_strategy() -> MomentumStrategy:
    """Get the current momentum strategy instance"""
    return AppleOnlyStrategy()
