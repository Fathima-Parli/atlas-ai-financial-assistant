import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.future import select

from backend.database.session import AsyncSessionLocal
from backend.models.models import User, Preferences
from backend.services.briefing_service import generate_morning_brief, generate_evening_summary

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def scheduled_morning_brief_job():
    """Job to execute morning briefings for active users."""
    logger.info("Executing scheduled Morning Market Brief job...")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.onboarded == True))
        users = result.scalars().all()
        for user in users:
            try:
                await generate_morning_brief(db, user)
                logger.info(f"Morning brief generated for user {user.telegram_id}")
            except Exception as e:
                logger.error(f"Error sending morning brief to {user.telegram_id}: {e}")

async def scheduled_evening_summary_job():
    """Job to execute evening summary for active users."""
    logger.info("Executing scheduled Evening Market Summary job...")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.onboarded == True))
        users = result.scalars().all()
        for user in users:
            try:
                await generate_evening_summary(db, user)
                logger.info(f"Evening summary generated for user {user.telegram_id}")
            except Exception as e:
                logger.error(f"Error sending evening summary to {user.telegram_id}: {e}")

def start_scheduler():
    """Initialize and start APScheduler background tasks."""
    # Morning Briefing at 08:00 AM
    scheduler.add_job(
        scheduled_morning_brief_job,
        'cron',
        hour=8,
        minute=0,
        id='morning_brief_job',
        replace_existing=True
    )
    
    # Evening Briefing at 06:00 PM (18:00)
    scheduler.add_job(
        scheduled_evening_summary_job,
        'cron',
        hour=18,
        minute=0,
        id='evening_brief_job',
        replace_existing=True
    )

    scheduler.start()
    logger.info("APScheduler initialized successfully.")
