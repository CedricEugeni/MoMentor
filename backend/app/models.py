"""Database models"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class TriggerType(str, enum.Enum):
    """Algorithm run trigger type"""
    AUTO = "auto"
    MANUAL = "manual"
    TEST = "test"


class RunStatus(str, enum.Enum):
    """Algorithm run status"""
    PENDING = "pending"
    COMPLETED = "completed"


class MoveAction(str, enum.Enum):
    """Move action type"""
    SELL = "SELL"
    BUY = "BUY"


class AlgorithmRun(Base):
    """Algorithm run record"""
    __tablename__ = "algorithm_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    run_date = Column(DateTime, nullable=False)
    trigger_type = Column(SQLEnum(TriggerType), nullable=False)
    total_capital_usd = Column(Numeric(precision=15, scale=2), nullable=False)
    uninvested_cash_usd = Column(Numeric(precision=15, scale=2), nullable=False, default=0)
    input_currency = Column(String(3), nullable=False, default="USD")
    fx_rate_to_usd = Column(Numeric(precision=12, scale=6), nullable=False, default=1)
    fx_rate_timestamp_utc = Column(DateTime, nullable=True)
    allocation_residual_cash_usd = Column(Numeric(precision=15, scale=2), nullable=False, default=0)
    status = Column(SQLEnum(RunStatus), nullable=False, default=RunStatus.PENDING)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    recommended_allocations = relationship("RecommendedAllocation", back_populates="run", cascade="all, delete-orphan")
    cashflow_moves = relationship("OptimizedMoveCashflow", back_populates="run", cascade="all, delete-orphan")
    swap_moves = relationship("OptimizedMoveSwap", back_populates="run", cascade="all, delete-orphan")
    actual_positions = relationship("ActualPosition", back_populates="run", cascade="all, delete-orphan")
    actual_cash = relationship("ActualCash", back_populates="run", uselist=False, cascade="all, delete-orphan")


class RecommendedAllocation(Base):
    """Recommended allocation for a run"""
    __tablename__ = "recommended_allocations"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("algorithm_runs.id"), nullable=False)
    symbol = Column(String(10), nullable=False)
    target_percentage = Column(Numeric(precision=5, scale=4), nullable=False)
    target_amount_usd = Column(Numeric(precision=15, scale=2), nullable=False)
    
    # Relationships
    run = relationship("AlgorithmRun", back_populates="recommended_allocations")


class OptimizedMoveCashflow(Base):
    """Optimized move with cash flow"""
    __tablename__ = "optimized_moves_cashflow"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("algorithm_runs.id"), nullable=False)
    symbol = Column(String(10), nullable=False)
    action = Column(SQLEnum(MoveAction), nullable=False)
    suggested_shares = Column(Numeric(precision=18, scale=4), nullable=False)
    suggested_value_usd = Column(Numeric(precision=15, scale=2), nullable=False)
    order_index = Column(Integer, nullable=False)
    
    # Relationships
    run = relationship("AlgorithmRun", back_populates="cashflow_moves")


class OptimizedMoveSwap(Base):
    """Optimized move with direct swap"""
    __tablename__ = "optimized_moves_swaps"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("algorithm_runs.id"), nullable=False)
    from_symbol = Column(String(10), nullable=True)  # None if pure buy
    to_symbol = Column(String(10), nullable=True)  # None if pure sell
    swap_shares_from = Column(Numeric(precision=18, scale=4), nullable=True)
    swap_shares_to = Column(Numeric(precision=18, scale=4), nullable=True)
    swap_value_usd = Column(Numeric(precision=15, scale=2), nullable=False)
    order_index = Column(Integer, nullable=False)
    
    # Relationships
    run = relationship("AlgorithmRun", back_populates="swap_moves")


class ActualPosition(Base):
    """Actual position confirmed by user"""
    __tablename__ = "actual_positions"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("algorithm_runs.id"), nullable=False)
    symbol = Column(String(10), nullable=False)
    actual_shares = Column(Numeric(precision=18, scale=4), nullable=False)
    actual_avg_price_usd = Column(Numeric(precision=15, scale=4), nullable=False)
    total_value_usd = Column(Numeric(precision=15, scale=2), nullable=False)
    first_validation_date = Column(DateTime, nullable=False)
    
    # Relationships
    run = relationship("AlgorithmRun", back_populates="actual_positions")


class ActualCash(Base):
    """Actual uninvested cash confirmed by user"""
    __tablename__ = "actual_cash"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("algorithm_runs.id"), nullable=False, unique=True)
    uninvested_cash_usd = Column(Numeric(precision=15, scale=2), nullable=False)
    first_validation_date = Column(DateTime, nullable=False)
    
    # Relationships
    run = relationship("AlgorithmRun", back_populates="actual_cash")


class PriceCache(Base):
    """Cached stock prices"""
    __tablename__ = "price_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, unique=True)
    price = Column(Numeric(precision=15, scale=4), nullable=False)
    timestamp = Column(DateTime, nullable=False)


class SchedulerLog(Base):
    """Scheduler execution log"""
    __tablename__ = "scheduler_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    run_date = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False)
    error = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
