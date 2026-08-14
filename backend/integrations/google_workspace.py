import logging
import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

MOCK_GOOGLE_CALENDAR_EVENTS = [
    {
        "id": "cal_01",
        "title": "Q3 NVIDIA Earnings Call & Portfolio Review",
        "time": "2026-08-27T17:00:00Z",
        "participants": ["sarah.cfo@fund.com", "analyst.john@fund.com"],
        "company_symbol": "NVDA",
        "summary": "Quarterly earnings call review with investment committee."
    },
    {
        "id": "cal_02",
        "title": "Semiconductor Supply Chain Strategy Meeting with TSMC",
        "time": "2026-08-12T14:30:00Z",
        "participants": ["hardware.lead@fund.com"],
        "company_symbol": "NVDA",
        "summary": "Deep dive into CoWoS packaging allocation and sub-3nm wafer yields."
    }
]

MOCK_GMAIL_MESSAGES = [
    {
        "id": "msg_01",
        "subject": "Goldman Sachs Institutional Research: OpenAI & Semiconductor Outlook 2026",
        "from": "research@gs.com",
        "date": "2026-08-05",
        "snippet": "We reiterate Conviction Buy on NVDA with a target of $160 based on strong enterprise Copilot inference demand..."
    },
    {
        "id": "msg_02",
        "subject": "Board Meeting Notes: Cloud Infrastructure CapEx Budgeting",
        "from": "internal-notes@fund.com",
        "date": "2026-08-04",
        "snippet": "The board approved a 25% increase in compute cluster allocation for Q3 models..."
    }
]

async def search_google_calendar(user_id: int, query: str = "") -> List[Dict[str, Any]]:
    """Search Google Calendar events for financial meetings."""
    if not query:
        return MOCK_GOOGLE_CALENDAR_EVENTS
    q = query.lower()
    return [e for e in MOCK_GOOGLE_CALENDAR_EVENTS if q in e["title"].lower() or q in e.get("company_symbol", "").lower()]

async def search_gmail(user_id: int, query: str = "") -> List[Dict[str, Any]]:
    """Search Gmail inbox for research reports and communications."""
    if not query:
        return MOCK_GMAIL_MESSAGES
    q = query.lower()
    return [m for m in MOCK_GMAIL_MESSAGES if q in m["subject"].lower() or q in m["snippet"].lower()]

async def generate_meeting_prep(meeting_title: str, symbol: str = "NVDA") -> Dict[str, Any]:
    """Generate executive meeting prep notes combining calendar, news, and financials."""
    return {
        "title": meeting_title,
        "symbol": symbol,
        "agenda": [
            f"Review Q3 financial metrics for {symbol}",
            "Discuss supply chain constraints and CoWoS yield rates",
            "Evaluate guidance changes vs consensus estimates",
            "Formulate strategic investment recommendations"
        ],
        "key_questions_to_ask": [
            "What is the current lead time for Blackwell GPU deliveries?",
            "How will gross margins trend as the product mix shifts toward Blackwell?",
            "Are customers extending multi-year commitments or buying spot capacity?"
        ],
        "financial_context": f"Current P/E: 45.2x | YoY Rev Growth: +122% | Gross Margin: 75.4%",
        "why_it_matters": "Ensures executive committee alignment prior to capital allocation decisions."
    }
