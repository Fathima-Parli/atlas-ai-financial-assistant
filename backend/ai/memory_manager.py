import re
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models.models import User, Preferences, ConversationMemory, Watchlist, Alert

logger = logging.getLogger(__name__)

SECTOR_KEYWORDS = {
    "tech": "Technology", "technology": "Technology", "semiconductor": "Semiconductors",
    "chips": "Semiconductors", "ai": "Artificial Intelligence", "biotech": "Biotech",
    "pharma": "Healthcare & Pharma", "finance": "Banking & Finance", "crypto": "Digital Assets",
    "energy": "Clean Energy", "auto": "Automotive / EV", "ev": "Automotive / EV"
}

TICKER_PATTERN = r'\b[A-Z]{2,5}\b'

async def get_or_create_user(db: AsyncSession, telegram_id: str, name: str = None) -> User:
    """Retrieve existing user or create a new user profile."""
    result = await db.execute(select(User).where(User.telegram_id == str(telegram_id)))
    user = result.scalars().first()

    if not user:
        user = User(
            telegram_id=str(telegram_id),
            name=name or "Finance Professional",
            onboarded=False,
            onboarding_step=0
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Create default preferences
        prefs = Preferences(
            user_id=user.id,
            preferred_sectors=["Technology", "Semiconductors"],
            companies_to_monitor=["NVDA", "AAPL", "MSFT"],
            briefing_time="08:00",
            morning_brief=True,
            evening_brief=True,
            sec_alerts=True,
            earnings_alerts=True
        )
        db.add(prefs)
        
        # Add initial default watchlists
        for sym, name_str in [("NVDA", "NVIDIA Corp."), ("AAPL", "Apple Inc."), ("MSFT", "Microsoft Corp.")]:
            w = Watchlist(user_id=user.id, symbol=sym, company_name=name_str)
            db.add(w)

        await db.commit()
        await db.refresh(user)

    return user

async def save_memory(db: AsyncSession, user_id: int, role: str, content: str, entities: Dict[str, Any] = None):
    """Save conversation message to user's persistent memory."""
    mem = ConversationMemory(
        user_id=user_id,
        role=role,
        content=content,
        extracted_entities=entities or {}
    )
    db.add(mem)
    await db.commit()

async def get_recent_memories(db: AsyncSession, user_id: int, limit: int = 10) -> List[ConversationMemory]:
    """Retrieve last N messages for conversation context."""
    result = await db.execute(
        select(ConversationMemory)
        .where(ConversationMemory.user_id == user_id)
        .order_by(ConversationMemory.created_at.desc())
        .limit(limit)
    )
    memories = result.scalars().all()
    return list(reversed(memories))

async def update_user_preferences_from_text(db: AsyncSession, user: User, text: str):
    """Extract preference updates, roles, and watchlists dynamically from conversation text."""
    text_lower = text.lower()
    
    result = await db.execute(select(Preferences).where(Preferences.user_id == user.id))
    prefs = result.scalars().first()
    if not prefs:
        prefs = Preferences(user_id=user.id)
        db.add(prefs)

    # Detect role
    for role_kw in ["cfo", "analyst", "hedge fund", "portfolio manager", "investor", "founder", "trader"]:
        if role_kw in text_lower:
            user.role = text.strip() if len(text) < 50 else role_kw.capitalize()
            break

    # Detect briefing time like 8am, 9:00, 18:00
    time_match = re.search(r'\b(0?[1-9]|1[0-2]|2[0-3])(?::([0-5][0-9]))?\s*(am|pm)?\b', text_lower)
    if "briefing" in text_lower or "morning" in text_lower or "time" in text_lower:
        if time_match:
            prefs.briefing_time = time_match.group(0).upper()

    # Detect watchlists / track requests: e.g., "track Tesla", "monitor NVDA", "watch Apple"
    track_matches = re.findall(r'(?:track|monitor|watch|follow)\s+([A-Za-z0-9]+)', text, re.IGNORECASE)
    for tm in track_matches:
        symbol = tm.upper()
        # Check if already in watchlist
        w_res = await db.execute(select(Watchlist).where(Watchlist.user_id == user.id, Watchlist.symbol == symbol))
        if not w_res.scalars().first():
            w = Watchlist(user_id=user.id, symbol=symbol, company_name=f"{symbol} Corp.")
            db.add(w)
            if symbol not in prefs.companies_to_monitor:
                prefs.companies_to_monitor = list(set(prefs.companies_to_monitor + [symbol]))

    # Detect sector interests
    for kw, sec in SECTOR_KEYWORDS.items():
        if kw in text_lower:
            if sec not in prefs.preferred_sectors:
                prefs.preferred_sectors = list(set(prefs.preferred_sectors + [sec]))

    await db.commit()
