"""APScheduler configuration for automatic monthly runs"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz

from app.config import settings
from app.database import SessionLocal
from app.models import SchedulerLog

scheduler = None


def monthly_algorithm_job():
    """Job that runs on the 1st of each month at 11:00 Paris time"""
    from app.services.run_generator import generate_algorithm_run
    
    db = SessionLocal()
    try:
        # Generate monthly run
        run = generate_algorithm_run(
            db=db,
            mode="monthly",
            manual_capital=None
        )
        
        # Log success
        log = SchedulerLog(
            run_date=datetime.now(pytz.timezone(settings.TIMEZONE)),
            status="success",
            error=None
        )
        db.add(log)
        db.commit()
        
        print(f"✓ Automatic monthly run generated: Run ID {run.id}")
        
    except Exception as e:
        # Log error
        log = SchedulerLog(
            run_date=datetime.now(pytz.timezone(settings.TIMEZONE)),
            status="error",
            error=str(e)[:500]
        )
        db.add(log)
        db.commit()
        
        print(f"✗ Error generating monthly run: {str(e)}")
        
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler"""
    global scheduler
    
    if scheduler is not None:
        print("⚠ Scheduler already running")
        return
    
    scheduler = BackgroundScheduler(timezone=settings.TIMEZONE)
    
    # Schedule job: 11:00 on the 1st of every month (Paris time)
    trigger = CronTrigger(
        hour=11,
        minute=0,
        day=1,
        timezone=pytz.timezone(settings.TIMEZONE)
    )
    
    scheduler.add_job(
        monthly_algorithm_job,
        trigger=trigger,
        id="monthly_algorithm_run",
        name="Generate monthly momentum recommendations",
        replace_existing=True
    )
    
    scheduler.start()
    print(f"✓ Scheduler started - Monthly runs at 11:00 {settings.TIMEZONE}")


def shutdown_scheduler():
    """Shutdown the scheduler"""
    global scheduler
    
    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        print("✓ Scheduler stopped")
