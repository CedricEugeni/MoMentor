"""
MoMentor - Momentum Investing Strategy Mentor
FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.routes import runs, portfolio
from app.scheduler import start_scheduler, shutdown_scheduler
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup: Create tables and start scheduler
    Base.metadata.create_all(bind=engine)
    
    if settings.ENABLE_AUTO_SCHEDULING:
        start_scheduler()
    
    yield
    
    # Shutdown: Stop scheduler
    if settings.ENABLE_AUTO_SCHEDULING:
        shutdown_scheduler()


app = FastAPI(
    title="MoMentor API",
    description="Momentum investing strategy mentor API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(runs.router, prefix="/api/runs", tags=["runs"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "momentor-backend"}


@app.post("/api/reset")
async def reset_database():
    """Reset all data in the database"""
    from app.database import SessionLocal
    from app.models import (
        AlgorithmRun, RecommendedAllocation, OptimizedMoveCashflow,
        OptimizedMoveSwap, ActualPosition, ActualCash, PriceCache, SchedulerLog
    )
    
    db = SessionLocal()
    try:
        # Delete all records from all tables
        db.query(ActualPosition).delete()
        db.query(ActualCash).delete()
        db.query(OptimizedMoveCashflow).delete()
        db.query(OptimizedMoveSwap).delete()
        db.query(RecommendedAllocation).delete()
        db.query(PriceCache).delete()
        db.query(SchedulerLog).delete()
        db.query(AlgorithmRun).delete()
        
        db.commit()
        return {"message": "Database reset successfully"}
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()
