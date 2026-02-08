"""API routes for portfolio"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.portfolio import PortfolioService

router = APIRouter()


@router.get("/current")
async def get_current_portfolio(db: Session = Depends(get_db)):
    """Get current portfolio with live prices and PnL"""
    portfolio_service = PortfolioService(db)
    return portfolio_service.get_current_portfolio_value()
