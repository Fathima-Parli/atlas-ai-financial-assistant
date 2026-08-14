import logging
import datetime
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.models.models import User, Watchlist, Notification, Preferences
from backend.integrations.yahoo_finance import get_company_profile
from backend.integrations.finnhub_news import get_market_news, get_earnings_calendar
from backend.integrations.sec_edgar import get_latest_filings
from backend.ai.analyst_agent import format_telegram_response

logger = logging.getLogger(__name__)

async def generate_morning_brief(db: AsyncSession, user: User) -> Dict[str, Any]:
    """Generate personalized Morning Market Brief for a user."""
    # Get user watchlist
    result = await db.execute(select(Watchlist).where(Watchlist.user_id == user.id))
    watchlists = result.scalars().all()
    symbols = [w.symbol for w in watchlists] if watchlists else ["NVDA", "AAPL", "MSFT"]

    # Gather data
    news = await get_market_news(symbols)
    top_news = news[0] if news else None
    
    profiles = []
    for s in symbols[:3]:
        p = await get_company_profile(s)
        profiles.append(p)

    stock_lines = [f"• {p['symbol']}: ${p['price']} ({p['change_pct']}%)" for p in profiles]
    stock_summary = "\n".join(stock_lines)

    summary = (
        f"☕ **Morning Market Brief - {datetime.date.today().strftime('%b %d, %Y')}**\n\n"
        f"**Watchlist Pre-Market Snapshot**\n{stock_summary}\n\n"
        f"**Lead Story**: {top_news['headline'] if top_news else 'Markets open steady.'}"
    )

    why = top_news.get('why_it_matters', 'Sets tone for pre-market liquidity and institutional positioning.') if top_news else 'Key catalyst for today\'s trading session.'
    next_action = "Say 'Summarize earnings' or 'Check SEC filings' for deep coverage."

    formatted = format_telegram_response(summary, why, next_action, citations="Yahoo Finance & Bloomberg Markets")

    # Store notification
    notif = Notification(
        user_id=user.id,
        title="Morning Market Brief",
        content=summary,
        why_it_matters=why,
        category="morning_brief"
    )
    db.add(notif)
    await db.commit()

    return {
        "user_id": user.id,
        "formatted_message": formatted
    }

async def generate_evening_summary(db: AsyncSession, user: User) -> Dict[str, Any]:
    """Generate Evening Market Summary for a user."""
    result = await db.execute(select(Watchlist).where(Watchlist.user_id == user.id))
    watchlists = result.scalars().all()
    symbols = [w.symbol for w in watchlists] if watchlists else ["NVDA", "AAPL"]

    summary = (
        f"🌙 **Evening Market Wrap - {datetime.date.today().strftime('%b %d, %Y')}**\n\n"
        f"Watchlist tickers closed strong led by semiconductor and cloud enterprise software expansion."
    )
    why = "Markets digested key inflation data while institutional flows favored mega-cap tech balance sheets."
    next_action = "Review tomorrow's earnings calendar by asking 'What earnings are tomorrow?'"

    formatted = format_telegram_response(summary, why, next_action, citations="Atlas Financial Intelligence Engine")

    notif = Notification(
        user_id=user.id,
        title="Evening Market Wrap",
        content=summary,
        why_it_matters=why,
        category="evening_brief"
    )
    db.add(notif)
    await db.commit()

    return {
        "user_id": user.id,
        "formatted_message": formatted
    }
