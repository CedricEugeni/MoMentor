"""API routes for algorithm runs"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Literal
from decimal import Decimal
from datetime import datetime

from app.database import get_db
from app.models import AlgorithmRun, RunStatus, ActualPosition, ActualCash
from app.services.run_generator import generate_algorithm_run
from app.services.market_data import MarketDataUnavailableError, MarketDataService

router = APIRouter()


class GenerateRunRequest(BaseModel):
    """Request to generate a new run"""
    mode: str  # "monthly", "manual", "test"
    capital: Optional[float] = None
    capital_currency: Literal["USD", "EUR"] = "USD"


class PositionConfirmation(BaseModel):
    """Position confirmation from user"""
    symbol: str
    shares: float
    avg_price: float


class ConfirmPositionsRequest(BaseModel):
    """Request to confirm actual positions"""
    positions: List[PositionConfirmation]
    uninvested_cash: float
    force_confirm: bool = False


@router.post("/generate")
async def generate_run(request: GenerateRunRequest, db: Session = Depends(get_db)):
    """Generate a new algorithm run with recommendations"""
    try:
        manual_capital = Decimal(str(request.capital)) if request.capital is not None else None
        
        run = generate_algorithm_run(
            db=db,
            mode=request.mode,
            manual_capital=manual_capital,
            capital_currency=request.capital_currency
        )
        
        return {
            "run_id": run.id,
            "run_date": run.run_date.isoformat(),
            "trigger_type": run.trigger_type.value,
            "total_capital_usd": float(run.total_capital_usd),
            "input_currency": run.input_currency,
            "fx_rate_to_usd": float(run.fx_rate_to_usd),
            "fx_rate_timestamp_utc": run.fx_rate_timestamp_utc.isoformat() if run.fx_rate_timestamp_utc else None,
            "status": run.status.value
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate run: {str(e)}")


@router.post("/trigger-monthly")
async def trigger_monthly(db: Session = Depends(get_db)):
    """Trigger monthly run (called by scheduler)"""
    try:
        run = generate_algorithm_run(db=db, mode="monthly", manual_capital=None)
        return {"run_id": run.id, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/has-pending")
async def has_pending_runs(db: Session = Depends(get_db)):
    """Check if there are any pending runs"""
    count = db.query(AlgorithmRun).filter(AlgorithmRun.status == RunStatus.PENDING).count()
    return {"has_pending": count > 0}


@router.get("")
async def list_runs(db: Session = Depends(get_db)):
    """List all algorithm runs"""
    runs = db.query(AlgorithmRun).order_by(AlgorithmRun.run_date.desc()).all()
    
    return {
        "runs": [
            {
                "id": run.id,
                "run_date": run.run_date.isoformat(),
                "trigger_type": run.trigger_type.value,
                "total_capital_usd": float(run.total_capital_usd),
                "input_currency": run.input_currency,
                "fx_rate_to_usd": float(run.fx_rate_to_usd),
                "fx_rate_timestamp_utc": run.fx_rate_timestamp_utc.isoformat() if run.fx_rate_timestamp_utc else None,
                "status": run.status.value,
                "created_at": run.created_at.isoformat()
            }
            for run in runs
        ]
    }


@router.get("/{run_id}/details")
async def get_run_details(run_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific run"""
    run = db.query(AlgorithmRun).filter(AlgorithmRun.id == run_id).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Get recommendations
    recommendations = [
        {
            "symbol": alloc.symbol,
            "target_percentage": float(alloc.target_percentage),
            "target_amount_usd": float(alloc.target_amount_usd)
        }
        for alloc in run.recommended_allocations
    ]
    
    # Get cashflow moves
    cashflow_moves = [
        {
            "symbol": move.symbol,
            "action": move.action.value,
            "suggested_shares": float(move.suggested_shares),
            "suggested_value_usd": float(move.suggested_value_usd),
            "order_index": move.order_index
        }
        for move in sorted(run.cashflow_moves, key=lambda x: x.order_index)
    ]
    
    # Get swap moves
    swap_moves = [
        {
            "from_symbol": move.from_symbol,
            "to_symbol": move.to_symbol,
            "swap_shares_from": float(move.swap_shares_from) if move.swap_shares_from is not None else None,
            "swap_shares_to": float(move.swap_shares_to) if move.swap_shares_to is not None else None,
            "swap_value_usd": float(move.swap_value_usd),
            "order_index": move.order_index,
            "description": _format_swap_description(move)
        }
        for move in sorted(run.swap_moves, key=lambda x: x.order_index)
    ]
    
    # Get actual positions if confirmed
    actual_positions = None
    actual_cash_value = None
    
    if run.status == RunStatus.COMPLETED:
        actual_positions = [
            {
                "symbol": pos.symbol,
                "actual_shares": float(pos.actual_shares),
                "actual_avg_price_usd": float(pos.actual_avg_price_usd),
                "total_value_usd": float(pos.total_value_usd),
                "first_validation_date": pos.first_validation_date.isoformat()
            }
            for pos in run.actual_positions
        ]
        
        if run.actual_cash:
            actual_cash_value = float(run.actual_cash.uninvested_cash_usd)
    
    return {
        "id": run.id,
        "run_date": run.run_date.isoformat(),
        "trigger_type": run.trigger_type.value,
        "total_capital_usd": float(run.total_capital_usd),
        "uninvested_cash_usd": float(run.uninvested_cash_usd),
        "input_currency": run.input_currency,
        "fx_rate_to_usd": float(run.fx_rate_to_usd),
        "fx_rate_timestamp_utc": run.fx_rate_timestamp_utc.isoformat() if run.fx_rate_timestamp_utc else None,
        "allocation_residual_cash_usd": float(run.allocation_residual_cash_usd),
        "status": run.status.value,
        "created_at": run.created_at.isoformat(),
        "recommendations": recommendations,
        "cashflow_moves": cashflow_moves,
        "swap_moves": swap_moves,
        "actual_positions": actual_positions,
        "actual_cash": actual_cash_value
    }


@router.post("/{run_id}/confirm-positions")
async def confirm_positions(
    run_id: int,
    request: ConfirmPositionsRequest,
    db: Session = Depends(get_db)
):
    """Confirm actual positions after rebalancing"""
    run = db.query(AlgorithmRun).filter(AlgorithmRun.id == run_id).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    if run.status == RunStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Run already completed")
    
    # Calculate total value from positions
    total_value = sum(Decimal(str(pos.shares)) * Decimal(str(pos.avg_price)) for pos in request.positions)
    total_value += Decimal(str(request.uninvested_cash))
    
    # Check for significant discrepancy (>10%)
    expected_value = run.total_capital_usd
    discrepancy_percent = abs((total_value - expected_value) / expected_value * 100) if expected_value > 0 else 0
    
    if discrepancy_percent > 10 and not request.force_confirm:
        return {
            "warning": True,
            "message": f"Total value ({float(total_value):.2f} USD) differs from expected ({float(expected_value):.2f} USD) by {float(discrepancy_percent):.1f}%",
            "discrepancy_percent": float(discrepancy_percent),
            "total_value": float(total_value),
            "expected_value": float(expected_value)
        }
    
    # Try to get current prices for validation
    symbols = [pos.symbol for pos in request.positions]
    market_data_service = MarketDataService(db)
    
    try:
        market_data_service.get_quotes(symbols)
    except MarketDataUnavailableError:
        if not request.force_confirm:
            return {
                "warning": True,
                "code": "MARKET_DATA_UNAVAILABLE",
                "message": "Market data is currently unavailable. You can confirm anyway and we will use your entered prices."
            }
    
    # Save actual positions
    validation_date = datetime.utcnow()
    
    for pos_data in request.positions:
        position = ActualPosition(
            run_id=run.id,
            symbol=pos_data.symbol,
            actual_shares=Decimal(str(pos_data.shares)),
            actual_avg_price_usd=Decimal(str(pos_data.avg_price)),
            total_value_usd=(Decimal(str(pos_data.shares)) * Decimal(str(pos_data.avg_price))).quantize(Decimal("0.01")),
            first_validation_date=validation_date
        )
        db.add(position)
    
    # Save actual cash
    cash = ActualCash(
        run_id=run.id,
        uninvested_cash_usd=Decimal(str(request.uninvested_cash)),
        first_validation_date=validation_date
    )
    db.add(cash)
    
    # Update run status
    run.status = RunStatus.COMPLETED
    
    db.commit()
    
    return {
        "success": True,
        "message": "Positions confirmed successfully",
        "run_id": run.id,
        "market_data_skipped": request.force_confirm
    }


def _format_swap_description(move):
    """Format swap move description"""
    def fmt(value):
        if value is None:
            return ""
        formatted = f"{float(value):.4f}".rstrip("0").rstrip(".")
        return formatted or "0"

    if move.from_symbol and move.to_symbol:
        return f"Vendre {fmt(move.swap_shares_from)} {move.from_symbol} → Acheter {fmt(move.swap_shares_to)} {move.to_symbol}"
    elif move.from_symbol:
        return f"Vendre {fmt(move.swap_shares_from)} {move.from_symbol}"
    elif move.to_symbol:
        return f"Acheter {fmt(move.swap_shares_to)} {move.to_symbol}"
    else:
        return "Unknown move"
