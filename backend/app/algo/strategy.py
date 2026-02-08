"""Momentum strategy interface and implementations"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from datetime import date
from typing import List
import random


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


class RandomMixStrategy(MomentumStrategy):
    """Stub strategy that returns a random mix of AAPL, GOOG, MSFT for testing"""

    def get_allocations(
        self,
        capital_usd: Decimal,
        uninvested_cash: Decimal,
        run_date: date
    ) -> List[Allocation]:
        """Allocate 100% across AAPL, GOOG, MSFT with random weights"""
        raw_weights = [random.random() for _ in range(3)]
        total = sum(raw_weights) or 1.0

        precision = Decimal("0.0001")
        first = (Decimal(str(raw_weights[0] / total))).quantize(precision, rounding=ROUND_DOWN)
        second = (Decimal(str(raw_weights[1] / total))).quantize(precision, rounding=ROUND_DOWN)
        third = Decimal("1") - first - second

        return [
            Allocation(symbol="AAPL", percentage=first),
            Allocation(symbol="GOOG", percentage=second),
            Allocation(symbol="MSFT", percentage=third),
        ]


# Default strategy to use
def get_strategy() -> MomentumStrategy:
    """Get the current momentum strategy instance"""
    return RandomMixStrategy()
