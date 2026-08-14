from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.database.session import get_db
from backend.models.models import User, Watchlist, Alert
from backend.ai.memory_manager import get_or_create_user
from backend.integrations.yahoo_finance import get_company_profile

router = APIRouter(tags=["Watchlist & Alerts"])

class AddWatchlistRequest(BaseModel):
    telegram_id: str = "demo_user_123"
    symbol: str
    target_price: Optional[float] = None

class CreateAlertRequest(BaseModel):
    telegram_id: str = "demo_user_123"
    symbol: str
    condition: str = "drop_pct"
    threshold_value: float = 5.0

@router.get("/watchlist")
async def get_watchlist_endpoint(telegram_id: str = "demo_user_123", db: AsyncSession = Depends(get_db)):
    """Retrieve user's active watchlist with live prices."""
    user = await get_or_create_user(db, telegram_id)
    result = await db.execute(select(Watchlist).where(Watchlist.user_id == user.id))
    watchlists = result.scalars().all()

    items = []
    for w in watchlists:
        profile = await get_company_profile(w.symbol)
        items.append({
            "id": w.id,
            "symbol": w.symbol,
            "company_name": profile.get("company_name", w.symbol),
            "price": profile.get("price", 0.0),
            "change_pct": profile.get("change_pct", 0.0),
            "pe_ratio": profile.get("pe_ratio", "N/A"),
            "added_at": w.added_at.isoformat()
        })

    return {
        "telegram_id": telegram_id,
        "count": len(items),
        "watchlist": items
    }

@router.post("/watchlist")
async def add_watchlist_endpoint(req: AddWatchlistRequest, db: AsyncSession = Depends(get_db)):
    """Add a new ticker symbol to watchlist."""
    user = await get_or_create_user(db, req.telegram_id)
    sym = req.symbol.upper().strip()

    # Check if existing
    result = await db.execute(select(Watchlist).where(Watchlist.user_id == user.id, Watchlist.symbol == sym))
    if result.scalars().first():
        return {"status": "exists", "message": f"{sym} is already in watchlist."}

    w = Watchlist(user_id=user.id, symbol=sym, company_name=f"{sym} Corp.", target_price=req.target_price)
    db.add(w)
    await db.commit()

    profile = await get_company_profile(sym)
    return {
        "status": "success",
        "symbol": sym,
        "profile": profile
    }

@router.post("/alerts")
async def create_alert_endpoint(req: CreateAlertRequest, db: AsyncSession = Depends(get_db)):
    """Create a price/SEC/earnings alert condition."""
    user = await get_or_create_user(db, req.telegram_id)
    sym = req.symbol.upper().strip()

    alert = Alert(
        user_id=user.id,
        symbol=sym,
        condition=req.condition,
        threshold_value=req.threshold_value,
        active=True
    )
    db.add(alert)
    await db.commit()

    return {
        "status": "success",
        "alert_id": alert.id,
        "symbol": sym,
        "condition": req.condition,
        "threshold": req.threshold_value
    }
