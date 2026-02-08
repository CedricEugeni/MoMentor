"""Service for generating algorithm runs"""
from decimal import Decimal
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models import (
    AlgorithmRun, RecommendedAllocation, OptimizedMoveCashflow,
    OptimizedMoveSwap, TriggerType, RunStatus, ActualPosition
)
from app.algo.strategy import get_strategy
from app.services.portfolio import PortfolioService
from app.services.market_data import MarketDataService
from app.services.rebalancing import RebalancingService


def generate_algorithm_run(
    db: Session,
    mode: str,  # "monthly", "manual", "test"
    manual_capital: Optional[Decimal] = None
) -> AlgorithmRun:
    """
    Generate a new algorithm run with recommendations and optimized moves
    
    Args:
        db: Database session
        mode: Trigger type (monthly, manual, test)
        manual_capital: Manual capital override (for first run or manual mode)
        
    Returns:
        Created AlgorithmRun instance
    """
    # Determine trigger type
    if mode == "monthly":
        trigger_type = TriggerType.AUTO
    elif mode == "test":
        trigger_type = TriggerType.TEST
    else:
        trigger_type = TriggerType.MANUAL
    
    # Calculate capital for this run
    portfolio_service = PortfolioService(db)
    
    if manual_capital is not None:
        # Use provided capital (first run or manual override)
        total_capital = manual_capital
        uninvested_cash = Decimal("0")
    else:
        # Calculate from previous run
        total_capital, uninvested_cash = portfolio_service.calculate_next_capital()
        
        # If no capital, this must be the first run - require manual input
        if total_capital == 0:
            raise ValueError("No capital available. Please provide initial capital for the first run.")
    
    # Get strategy and generate allocations
    strategy = get_strategy()
    allocations = strategy.get_allocations(
        capital_usd=total_capital,
        uninvested_cash=uninvested_cash,
        run_date=datetime.utcnow().date()
    )
    
    # Create algorithm run
    run = AlgorithmRun(
        run_date=datetime.utcnow(),
        trigger_type=trigger_type,
        total_capital_usd=total_capital,
        uninvested_cash_usd=uninvested_cash,
        status=RunStatus.PENDING
    )
    db.add(run)
    db.flush()  # Get run.id
    
    # Save recommended allocations
    for allocation in allocations:
        target_amount = total_capital * allocation.percentage
        rec_allocation = RecommendedAllocation(
            run_id=run.id,
            symbol=allocation.symbol,
            target_percentage=allocation.percentage,
            target_amount_usd=target_amount
        )
        db.add(rec_allocation)
    
    # Get current prices for all symbols involved
    all_symbols = set([a.symbol for a in allocations])
    
    # Get previous positions
    previous_run = (
        db.query(AlgorithmRun)
        .filter(AlgorithmRun.status == RunStatus.COMPLETED)
        .filter(AlgorithmRun.id != run.id)
        .order_by(AlgorithmRun.run_date.desc())
        .first()
    )
    
    previous_positions = []
    if previous_run:
        previous_positions = previous_run.actual_positions
        all_symbols.update([pos.symbol for pos in previous_positions])
    
    # Fetch current prices
    market_data_service = MarketDataService(db)
    try:
        current_prices = market_data_service.get_quotes(list(all_symbols))
    except Exception as e:
        # If prices fail, we can't calculate moves properly
        print(f"Warning: Failed to fetch prices: {e}")
        current_prices = {}
    
    # Calculate optimized moves (cashflow and swaps)
    rebalancing_service = RebalancingService(db)
    
    # Cashflow moves
    cashflow_moves = rebalancing_service.calculate_cashflow_moves(
        previous_positions=previous_positions,
        target_allocations=allocations,
        current_prices=current_prices,
        total_capital=total_capital
    )
    
    for move in cashflow_moves:
        cf_move = OptimizedMoveCashflow(
            run_id=run.id,
            symbol=move.symbol,
            action=move.action,
            suggested_shares=move.suggested_shares,
            suggested_value_usd=move.suggested_value_usd,
            order_index=move.order_index
        )
        db.add(cf_move)
    
    # Swap moves
    swap_moves = rebalancing_service.calculate_swap_moves(
        previous_positions=previous_positions,
        target_allocations=allocations,
        current_prices=current_prices,
        total_capital=total_capital
    )
    
    for move in swap_moves:
        swap_move = OptimizedMoveSwap(
            run_id=run.id,
            from_symbol=move.from_symbol,
            to_symbol=move.to_symbol,
            swap_shares_from=move.swap_shares_from,
            swap_shares_to=move.swap_shares_to,
            swap_value_usd=move.swap_value_usd,
            order_index=move.order_index
        )
        db.add(swap_move)
    
    db.commit()
    db.refresh(run)
    
    return run
