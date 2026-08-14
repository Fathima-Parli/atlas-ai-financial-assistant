import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.database.session import get_db
from backend.models.models import User, GoogleAccount
from backend.ai.memory_manager import get_or_create_user
from backend.services.briefing_service import generate_morning_brief, generate_evening_summary

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Integrations & Daily Briefs"])

class GoogleConnectRequest(BaseModel):
    telegram_id: str = "demo_user_123"
    email: str = "user@fund.com"

@router.post("/google/connect")
async def connect_google_endpoint(req: GoogleConnectRequest, db: AsyncSession = Depends(get_db)):
    """Simulate or execute Google Workspace OAuth connection (Calendar, Drive, Sheets, Gmail)."""
    user = await get_or_create_user(db, req.telegram_id)
    
    result = await db.execute(select(GoogleAccount).where(GoogleAccount.user_id == user.id))
    ga = result.scalars().first()
    
    if not ga:
        ga = GoogleAccount(
            user_id=user.id,
            email=req.email,
            connected=True
        )
        db.add(ga)
    else:
        ga.connected = True
        ga.email = req.email

    await db.commit()

    return {
        "status": "connected",
        "email": req.email,
        "message": "Google Workspace (Calendar, Gmail, Drive, Sheets) connected successfully."
    }

@router.get("/daily-brief")
async def get_daily_brief_endpoint(telegram_id: str = "demo_user_123", type: str = "morning", db: AsyncSession = Depends(get_db)):
    """Manually trigger or retrieve personalized Morning or Evening Brief."""
    user = await get_or_create_user(db, telegram_id)
    
    if type == "evening":
        brief = await generate_evening_summary(db, user)
    else:
        brief = await generate_morning_brief(db, user)

    return brief

@router.post("/telegram/webhook")
async def telegram_webhook_endpoint(request: Request, db: AsyncSession = Depends(get_db)):
    """Standard Telegram Bot Webhook endpoint for live Telegram deployment."""
    data = await request.json()
    logger.info(f"Received Telegram webhook update: {data}")
    
    if "message" in data:
        msg = data["message"]
        chat_id = str(msg["chat"]["id"])
        text = msg.get("text", "")
        
        if text:
            user = await get_or_create_user(db, chat_id, msg.get("from", {}).get("first_name", "User"))
            # Process chat response
            from backend.ai.analyst_agent import generate_analyst_response
            reply = await generate_analyst_response(db, user, text)
            return {"method": "sendMessage", "chat_id": chat_id, "text": reply, "parse_mode": "Markdown"}

    return {"status": "ok"}
