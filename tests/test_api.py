import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import delete
from backend.main import app
from backend.database.session import init_db, get_db
from backend.ai.memory_manager import get_or_create_user
from backend.models.models import (
    User,
    Preferences,
    ConversationMemory,
    Watchlist,
    Alert,
    Document,
    Meeting,
    GoogleAccount,
    Notification,
    MarketEvent,
)

@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    await init_db()

    async for db in get_db():
        await db.execute(delete(Notification))
        await db.execute(delete(MarketEvent))
        await db.execute(delete(GoogleAccount))
        await db.execute(delete(Meeting))
        await db.execute(delete(Document))
        await db.execute(delete(Alert))
        await db.execute(delete(Watchlist))
        await db.execute(delete(ConversationMemory))
        await db.execute(delete(Preferences))
        await db.execute(delete(User))
        await db.commit()
        break

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "online"

@pytest.mark.asyncio
async def test_natural_chat_onboarding():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/chat", json={
            "telegram_id": "onboard_user_001",
            "name": "Test Analyst",
            "message": "Hedge Fund Senior Analyst"
        })
        assert res.status_code == 200
        data = res.json()
        assert "reply" in data and len(data["reply"]) > 0


@pytest.mark.asyncio
async def test_company_research():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Pre-onboard user
        async for db in get_db():
            u = await get_or_create_user(db, "analyst_user_999")
            u.onboarded = True
            await db.commit()
            break

        res = await ac.post("/chat", json={
            "telegram_id": "analyst_user_999",
            "message": "Tell me about Nvidia"
        })
        assert res.status_code == 200
        data = res.json()
        assert "NVIDIA" in data["reply"] or "NVDA" in data["reply"]

@pytest.mark.asyncio
async def test_watchlist_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Add to watchlist
        add_res = await ac.post("/watchlist", json={
            "telegram_id": "analyst_user_999",
            "symbol": "TSLA"
        })
        assert add_res.status_code == 200

        # Fetch watchlist
        get_res = await ac.get("/watchlist?telegram_id=analyst_user_999")
        assert get_res.status_code == 200
        assert get_res.json()["count"] >= 1

@pytest.mark.asyncio
async def test_daily_brief():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/daily-brief?telegram_id=analyst_user_999&type=morning")
        assert res.status_code == 200
        assert "Morning Market Brief" in res.json()["formatted_message"]
