import logging
import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

MOCK_SEC_FILINGS = {
    "NVDA": [
        {
            "filing_type": "10-K",
            "date": "2026-02-25",
            "title": "Annual Report (Form 10-K) for FY2026",
            "accession_number": "0001045810-26-000012",
            "summary": "Total revenue reached $115.6B, up 122% YoY led by Compute & Networking division. R&D spend increased 42% to $12.1B. Form 10-K outlines Item 1A Risk Factors including export controls and wafer allocation constraints.",
            "url": "https://www.sec.gov/edgar/searchedgar/companysearch"
        },
        {
            "filing_type": "8-K",
            "date": "2026-05-18",
            "title": "Current Report (Form 8-K) - Material Agreement",
            "accession_number": "0001045810-26-000045",
            "summary": "NVIDIA announced strategic silicon co-development agreement with leading cloud hyperscaler and updated executive incentive compensation structure.",
            "url": "https://www.sec.gov/edgar/searchedgar/companysearch"
        }
    ],
    "AAPL": [
        {
            "filing_type": "10-Q",
            "date": "2026-05-02",
            "title": "Quarterly Report (Form 10-Q) for Q2 FY2026",
            "accession_number": "0000320193-26-000022",
            "summary": "Services revenue set all-time record of $23.9B (+12% YoY). iPhone revenue $45.9B. Authorized additional $110B share repurchase program.",
            "url": "https://www.sec.gov/edgar/searchedgar/companysearch"
        }
    ],
    "MSFT": [
        {
            "filing_type": "10-Q",
            "date": "2026-04-25",
            "title": "Quarterly Report (Form 10-Q) for Q3 FY2026",
            "accession_number": "0000789019-26-000018",
            "summary": "Azure revenue growth was 31% YoY (7% attributed to AI services). Intelligent Cloud segment gross margin came in at 71.5%.",
            "url": "https://www.sec.gov/edgar/searchedgar/companysearch"
        }
    ]
}

async def get_latest_filings(symbol: str, count: int = 3) -> List[Dict[str, Any]]:
    """Retrieve recent SEC EDGAR filings for a ticker symbol."""
    symbol_upper = symbol.upper().strip()
    if symbol_upper in MOCK_SEC_FILINGS:
        return MOCK_SEC_FILINGS[symbol_upper][:count]
    
    # Generic filing response if ticker not explicitly mocked
    today_str = datetime.date.today().isoformat()
    return [
        {
            "filing_type": "10-Q",
            "date": today_str,
            "title": f"Form 10-Q Quarterly Report - {symbol_upper}",
            "accession_number": f"0000000000-{today_str[:4]}-001024",
            "summary": f"Quarterly financial disclosures for {symbol_upper} detailing operational cash flows, liquidity position, and risk factor updates.",
            "url": "https://www.sec.gov/edgar/searchedgar/companysearch"
        }
    ]
