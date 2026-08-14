import logging
import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

MOCK_MARKET_NEWS = [
    {
        "id": 101,
        "symbol": "NVDA",
        "headline": "NVIDIA Blackwell B200 Production Reaches Full Volume Capacity Ahead of Schedule",
        "summary": "Analyst checks indicate TSMC CoWoS packaging bottlenecks easing faster than expected, boosting Q3 revenue projections by $2.5B.",
        "source": "Bloomberg Markets",
        "published_at": "2026-08-06T14:30:00Z",
        "sentiment": "Strongly Positive",
        "why_it_matters": "Demonstrates accelerating data center supply delivery, directly addressing major investor concern regarding production bottlenecks."
    },
    {
        "id": 102,
        "symbol": "AAPL",
        "headline": "Apple Intelligence Multi-Modal Rollout Expands to EU & Asian Regulatory Regions",
        "summary": "Apple secures preliminary EU compliance greenlight for on-device AI data handling, unlocking 400M premium iPhone upgrade base.",
        "source": "Wall Street Journal",
        "published_at": "2026-08-06T12:15:00Z",
        "sentiment": "Positive",
        "why_it_matters": "Resolves key regulatory roadblock in international markets, boosting hardware super-cycle thesis for Q4."
    },
    {
        "id": 103,
        "symbol": "MSFT",
        "headline": "Microsoft Announces Next-Gen Copilot Enterprise Pricing & Custom Agent Builder",
        "summary": "Enterprise adoption rates cross 60% among Fortune 500 companies with average ARPU expansion of $30/user/month.",
        "source": "Financial Times",
        "published_at": "2026-08-06T10:00:00Z",
        "sentiment": "Positive",
        "why_it_matters": "Validates monetization model for enterprise AI software investments, calming CapEx margin concerns."
    },
    {
        "id": 104,
        "symbol": "TSLA",
        "headline": "Federal Transit Authority Opens Streamlined Approval Track for Autonomous Robotaxi Fleets",
        "summary": "New regulatory framework sets clear standard for Level 4 autonomous vehicle commercial operations across 12 major metro markets.",
        "source": "Reuters Financial",
        "published_at": "2026-08-06T09:45:00Z",
        "sentiment": "Very Positive",
        "why_it_matters": "Lowers regulatory friction for Tesla's Cybercab commercial launch timeline."
    }
]

async def get_market_news(symbols: List[str] = None) -> List[Dict[str, Any]]:
    """Get curated financial market news filtered by symbols if provided."""
    if not symbols:
        return MOCK_MARKET_NEWS
    
    symbols_upper = [s.upper() for s in symbols]
    filtered = [n for n in MOCK_MARKET_NEWS if n["symbol"] in symbols_upper]
    return filtered if filtered else MOCK_MARKET_NEWS[:2]

async def get_earnings_calendar(symbols: List[str] = None) -> List[Dict[str, Any]]:
    """Fetch upcoming earnings announcements."""
    return [
        {
            "symbol": "NVDA",
            "company_name": "NVIDIA Corp.",
            "earnings_date": "2026-08-27",
            "timing": "After Market Close",
            "eps_estimate": "$0.64",
            "revenue_estimate": "$28.6B",
            "why_it_matters": "Primary barometer for global AI infrastructure capital spending across hyperscalers."
        },
        {
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "earnings_date": "2026-10-29",
            "timing": "After Market Close",
            "eps_estimate": "$1.52",
            "revenue_estimate": "$94.2B",
            "why_it_matters": "Key indicator of consumer tech demand and early Apple Intelligence upgrade adoption."
        },
        {
            "symbol": "MSFT",
            "company_name": "Microsoft Corp.",
            "earnings_date": "2026-10-22",
            "timing": "After Market Close",
            "eps_estimate": "$3.10",
            "revenue_estimate": "$64.8B",
            "why_it_matters": "Demonstrates Azure AI cloud revenue growth vs CapEx spend trajectory."
        }
    ]
