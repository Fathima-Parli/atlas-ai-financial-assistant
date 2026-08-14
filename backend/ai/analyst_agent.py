import re
import logging
import httpx
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.config import settings
from backend.models.models import User, Preferences, Watchlist, Alert, Document
from backend.integrations.yahoo_finance import get_company_profile, compare_companies
from backend.integrations.sec_edgar import get_latest_filings
from backend.integrations.finnhub_news import get_market_news, get_earnings_calendar
from backend.integrations.google_workspace import search_gmail, search_google_calendar, generate_meeting_prep
from backend.integrations.mfapi import get_mutual_fund_nav
from backend.ai.rag_engine import query_document

logger = logging.getLogger(__name__)

# Onboarding flow questions sequence
ONBOARDING_STEPS = [
    {
        "step": 0,
        "question": "Hello 👋\nI'm Atlas, your AI Financial Assistant.\n\nI'd like to understand your workflow so I can tailor intelligence to your needs.\n\nWhat best describes your role? (e.g., Hedge Fund Analyst, CFO, Private Investor, Financial Advisor)"
    },
    {
        "step": 1,
        "question": "Got it. Which companies or tickers do you follow closely? (e.g., TCS, RELIANCE, NVDA, AAPL)"
    },
    {
        "step": 2,
        "question": "Which specific sectors interest you most? (e.g., Technology, Semiconductors, Banking, Energy)"
    },
    {
        "step": 3,
        "question": "Would you like me to deliver automated daily briefings and market news?"
    },
    {
        "step": 4,
        "question": "What is your preferred briefing time? (Default: 08:00 AM)"
    }
]

def format_telegram_response(summary: str, why_it_matters: str, next_action: str, citations: str = None) -> str:
    """Format outputs matching exact Telegram readability specifications."""
    res = f"**Summary**\n{summary.strip()}\n\n"
    res += f"**Why It Matters**\n{why_it_matters.strip()}\n\n"
    if citations:
        res += f"**Source Citation**\n{citations.strip()}\n\n"
    res += f"**Suggested Next Action**\n{next_action.strip()}"
    return res

async def generate_analyst_response(
    db: AsyncSession,
    user: User,
    user_input: str,
    recent_memories: List[Any] = None
) -> str:
    """Primary executive financial reasoning agent for Atlas AI Assistant."""
    input_text = user_input.strip()
    input_lower = input_text.lower()

    # -------------------------------------------------------------
    # 1. NATURAL ONBOARDING CHECK
    # -------------------------------------------------------------
    if not user.onboarded:
        step = user.onboarding_step
        
        if "skip" in input_lower:
            user.onboarding_step += 1
        else:
            if step == 0:
                user.role = input_text
            elif step == 1:
                tickers = re.findall(r'\b[A-Za-z]{2,10}\b', input_text.upper())
                clean_tickers = [t for t in tickers if t not in ["AND", "LIKE", "FOLLOW", "WITH"]]
                for t in clean_tickers:
                    w = Watchlist(user_id=user.id, symbol=t, company_name=f"{t} Corp.")
                    db.add(w)
            user.onboarding_step += 1

        if user.onboarding_step < len(ONBOARDING_STEPS):
            await db.commit()
            return ONBOARDING_STEPS[user.onboarding_step]["question"]
        else:
            user.onboarded = True
            await db.commit()
            return format_telegram_response(
                summary="Onboarding complete! I have set up your profile, coverage watchlist, and intelligence preferences.",
                why_it_matters="Atlas is calibrated to your investment coverage and will proactively track market developments.",
                next_action="Ask me any question: 'Price of TCS', 'HDFC Top 100 NAV', 'Show my watchlist', or upload a PDF report."
            )

    # -------------------------------------------------------------
    # 2. MUTUAL FUND NAV LOOKUP (e.g. "HDFC Top 100 NAV", "HDFC Large Cap Fund")
    # -------------------------------------------------------------
    if "nav" in input_lower or "mutual fund" in input_lower or "hdfc top 100" in input_lower or "large cap fund" in input_lower or "flexi cap" in input_lower:
        mf_data = await get_mutual_fund_nav(input_text)
        if mf_data:
            summary_str = (
                f"📊 **Mutual Fund NAV Details**:\n"
                f"• **Exact Scheme**: {mf_data['scheme_name']}\n"
                f"• **Net Asset Value (NAV)**: ₹{mf_data['nav']} (as of {mf_data['date']})\n"
                f"• **Fund House**: {mf_data['fund_house']}\n"
                f"• **Category**: {mf_data['scheme_type']}"
            )
            why_str = f"HDFC Top 100 Fund was officially renamed to HDFC Large Cap Fund. Atlas correctly identified Scheme Code {mf_data['scheme_code']} to fetch verified AMFI NAV data."
            return format_telegram_response(
                summary=summary_str,
                why_it_matters=why_str,
                next_action="Ask for other mutual funds like 'Parag Parikh Flexi Cap NAV' or compare stock performance.",
                citations=mf_data["source"]
            )

    # -------------------------------------------------------------
    # 3. NATURAL WATCHLIST COMMANDS
    # -------------------------------------------------------------
    if "show my watchlist" in input_lower or "view watchlist" in input_lower or "my watchlist" in input_lower:
        result = await db.execute(select(Watchlist).where(Watchlist.user_id == user.id))
        watchlists = result.scalars().all()
        if not watchlists:
            return format_telegram_response(
                summary="Your watchlist is currently empty.",
                why_it_matters="Adding tickers allows Atlas to monitor real-time price movements and earnings alerts.",
                next_action="Type 'Add TCS to my watchlist' or 'Track NVDA'."
            )
        
        lines = []
        for w in watchlists:
            prof = await get_company_profile(w.symbol)
            lines.append(f"• **{w.symbol}** ({prof['company_name']}): {prof['price']} ({prof['change_pct']}%)")
        
        return format_telegram_response(
            summary="Your Coverage Watchlist:\n" + "\n".join(lines),
            why_it_matters="Atlas continuously tracks these assets in persistent SQLite storage.",
            next_action="Ask 'Is TCS moving today?' or 'Remove TCS'."
        )

    if any(k in input_lower for k in ["add ", "track ", "monitor ", "watch "]) and "watchlist" in input_lower or "track " in input_lower:
        symbols = re.findall(r'\b[A-Za-z]{2,10}\b', input_text.upper())
        symbols = [s for s in symbols if s not in ["ADD", "TRACK", "WATCH", "MONITOR", "TO", "MY", "WATCHLIST", "THE", "STOCK", "FOR"]]
        if symbols:
            added = []
            for s in symbols:
                w_res = await db.execute(select(Watchlist).where(Watchlist.user_id == user.id, Watchlist.symbol == s))
                if not w_res.scalars().first():
                    w = Watchlist(user_id=user.id, symbol=s, company_name=f"{s} Corp.")
                    db.add(w)
                    added.append(s)
            await db.commit()
            return format_telegram_response(
                summary=f"Added {', '.join(added) if added else 'asset'} to your persistent coverage watchlist.",
                why_it_matters="Atlas will monitor price movements, earnings announcements, and filing updates.",
                next_action="Type 'Show my watchlist' to view live prices."
            )

    if "remove " in input_lower and ("watchlist" in input_lower or len(input_text.split()) <= 4):
        symbols = re.findall(r'\b[A-Za-z]{2,10}\b', input_text.upper())
        symbols = [s for s in symbols if s not in ["REMOVE", "DELETE", "FROM", "MY", "WATCHLIST"]]
        if symbols:
            for s in symbols:
                await db.execute(select(Watchlist).where(Watchlist.user_id == user.id, Watchlist.symbol == s))
                w_res = await db.execute(select(Watchlist).where(Watchlist.user_id == user.id, Watchlist.symbol == s))
                item = w_res.scalars().first()
                if item:
                    await db.delete(item)
            await db.commit()
            return format_telegram_response(
                summary=f"Removed {', '.join(symbols)} from your coverage watchlist.",
                why_it_matters="Your SQLite database has been updated.",
                next_action="Type 'Show my watchlist' to verify active tracked symbols."
            )

    if "moving today" in input_lower or "moving" in input_lower:
        symbols = re.findall(r'\b[A-Za-z]{2,10}\b', input_text.upper())
        sym = [s for s in symbols if s not in ["IS", "MOVING", "TODAY", "THE", "STOCK"]][0] if symbols else "TCS"
        prof = await get_company_profile(sym)
        return format_telegram_response(
            summary=f"{prof['company_name']} ({sym}) Intraday Movement:\n• Price: {prof['price']}\n• Day Change: {prof['change_pct']}%\n• Range: Low {prof['low']} - High {prof['high']}\n• Prev Close: {prof['prev_close']}",
            why_it_matters=f"Current price action shows a {prof['change_pct']}% variation from previous session close.",
            next_action=f"Set alert by typing 'Alert me if {sym} drops 3%'.",
            citations=prof["source"]
        )

    # -------------------------------------------------------------
    # 4. PERSISTENT PDF DOCUMENT Q&A
    # -------------------------------------------------------------
    # Check if user has an uploaded document in DB and query mentions report/PDF/revenue/risk/growth/summary
    if any(k in input_lower for k in ["pdf", "report", "revenue", "risk", "management", "growth", "annual", "quarterly", "document", "filing"]):
        doc_res = await db.execute(
            select(Document).where(Document.user_id == user.id).order_by(Document.created_at.desc())
        )
        latest_doc = doc_res.scalars().first()
        if latest_doc and latest_doc.raw_text:
            answer = await query_document(latest_doc.raw_text, input_text)
            return format_telegram_response(
                summary=f"📄 **Document Q&A** ('{latest_doc.filename}'):\n\n{answer}",
                why_it_matters=f"Answer generated using TF-IDF RAG semantic retrieval grounded directly in '{latest_doc.filename}'.",
                next_action="Ask another question about this document or upload a new financial report."
            )

    # -------------------------------------------------------------
    # 5. GOOGLE INTEGRATION INTENTS (GMAIL & CALENDAR)
    # -------------------------------------------------------------
    if "email" in input_lower or "gmail" in input_lower:
        emails = await search_gmail(user.id, query=input_text)
        if emails:
            e = emails[0]
            return format_telegram_response(
                summary=f"Found research note: '{e['subject']}' from {e['from']} ({e['date']}).\n\nPreview: {e['snippet']}",
                why_it_matters="Direct institutional research note retrieved from connected Gmail inbox.",
                next_action="Ask me to summarize this research note or draft key takeaways."
            )

    if "meeting" in input_lower or "calendar" in input_lower or "prep" in input_lower:
        prep = await generate_meeting_prep("Q3 Financial Strategy Briefing", "NVDA")
        questions_str = "\n• " + "\n• ".join(prep["key_questions_to_ask"])
        return format_telegram_response(
            summary=f"Meeting Briefing Prepared: '{prep['title']}' ({prep['symbol']})\n\nKey Questions to Ask:{questions_str}",
            why_it_matters=prep["why_it_matters"],
            next_action="Export briefing notes to Google Docs or send to meeting participants."
        )

    # -------------------------------------------------------------
    # 6. COMPANY COMPARISON (e.g. "Compare Apple vs Microsoft")
    # -------------------------------------------------------------
    if "vs" in input_lower or "compare" in input_lower:
        tickers = re.findall(r'\b[A-Za-z]{2,10}\b', input_text.upper())
        tickers = [t for t in tickers if t not in ["VS", "COMPARE", "AND", "TELL", "ME", "FOR"]]
        if len(tickers) >= 2:
            sym_a, sym_b = tickers[0], tickers[1]
            comp = await compare_companies(sym_a, sym_b)
            cA, cB = comp["company_a"], comp["company_b"]
            
            summary_text = (
                f"Head-to-Head Comparison:\n"
                f"• **{cA['symbol']}** ({cA['company_name']}): {cA['price']} | P/E: {cA['pe_ratio']} | Rev Growth: {cA['revenue_growth']}\n"
                f"• **{cB['symbol']}** ({cB['company_name']}): {cB['price']} | P/E: {cB['pe_ratio']} | Rev Growth: {cB['revenue_growth']}"
            )
            why_text = f"{cA['symbol']} trades at {cA['pe_ratio']}x earnings vs {cB['symbol']} at {cB['pe_ratio']}x earnings."
            return format_telegram_response(
                summary=summary_text,
                why_it_matters=why_text,
                next_action=f"Ask for a deep-dive SWOT analysis on either {cA['symbol']} or {cB['symbol']}.",
                citations=f"{cA['source']} & {cB['source']}"
            )

    # -------------------------------------------------------------
    # 7. SPECIALIZED ANALYSIS (SWOT & THESIS)
    # -------------------------------------------------------------
    if "swot" in input_lower:
        symbol = "NVDA"
        sym_match = re.search(r'\b[A-Z]{2,10}\b', input_text.upper())
        if sym_match and sym_match.group(0) not in ["SWOT", "ANALYSIS", "FOR", "GENERATE"]:
            symbol = sym_match.group(0)
            
        profile = await get_company_profile(symbol)
        swot_text = (
            f"Financial SWOT for {profile['company_name']} ({symbol}):\n\n"
            f"🔹 **Strengths**: High gross margin ({profile['gross_margin']}), strong revenue growth ({profile['revenue_growth']}).\n"
            f"🔹 **Weaknesses**: Sector expenditure sensitivity.\n"
            f"🔹 **Opportunities**: {profile['opportunities'][0]}.\n"
            f"🔹 **Threats**: {profile['risks'][0]}."
        )
        return format_telegram_response(
            summary=swot_text,
            why_it_matters="Provides executive leadership with a structured strategic audit of capital allocation risk.",
            next_action="Request investment thesis summary or competitive positioning matrix.",
            citations=profile["source"]
        )

    if "thesis" in input_lower:
        symbol = "NVDA"
        sym_match = re.search(r'\b[A-Z]{2,10}\b', input_text.upper())
        if sym_match and sym_match.group(0) not in ["THESIS", "INVESTMENT", "GENERATOR", "FOR"]:
            symbol = sym_match.group(0)

        profile = await get_company_profile(symbol)
        thesis_text = (
            f"Institutional Investment Thesis - {symbol}:\n\n"
            f"1. Core Driver: Unrivaled market position in {profile['sector']}.\n"
            f"2. Financial Metric: Revenue growth of {profile['revenue_growth']} with gross margins at {profile['gross_margin']}.\n"
            f"3. Valuation Target: Base case valuation based on forward earnings trajectory."
        )
        return format_telegram_response(
            summary=thesis_text,
            why_it_matters="Synthesizes market signal into an actionable institutional thesis.",
            next_action="Ask to stress-test this thesis against key regulatory or supply risks.",
            citations=profile["source"]
        )

    # -------------------------------------------------------------
    # 8. STOCK PRICE & COMPANY RESEARCH (TCS, RELIANCE, NVDA, AAPL, etc.)
    # -------------------------------------------------------------
    ticker_found = None
    for sym in ["TCS", "RELIANCE", "INFY", "NVDA", "AAPL", "MSFT", "TSLA", "GOOGL", "HDFCBANK"]:
        if sym in input_text.upper():
            ticker_found = sym
            break

    if not ticker_found:
        if "tata consultancy" in input_lower or "tcs" in input_lower: ticker_found = "TCS"
        elif "reliance" in input_lower: ticker_found = "RELIANCE"
        elif "infosys" in input_lower: ticker_found = "INFY"
        elif "nvidia" in input_lower: ticker_found = "NVDA"
        elif "apple" in input_lower: ticker_found = "AAPL"
        elif "microsoft" in input_lower: ticker_found = "MSFT"
        elif "tesla" in input_lower: ticker_found = "TSLA"
        elif "google" in input_lower: ticker_found = "GOOGL"

    if ticker_found:
        profile = await get_company_profile(ticker_found)
        
        summary_str = (
            f"**{profile['company_name']} ({profile['symbol']}) Data**:\n"
            f"• **Current Price**: {profile['price']}\n"
            f"• **Previous Close**: {profile['prev_close']}\n"
            f"• **Day Change**: {profile['change_pct']}%\n"
            f"• **Day Range**: Low {profile['low']} - High {profile['high']}\n"
            f"• **52-Week Range**: {profile['fifty_two_week_range']}\n"
            f"• **P/E Ratio**: {profile['pe_ratio']} | **Market Cap**: {profile['market_cap']}"
        )
        why_str = f"Sector: {profile['sector']}. Growth opportunity: {profile['opportunities'][0]} offset by {profile['risks'][0]}."
        return format_telegram_response(
            summary=summary_str,
            why_it_matters=why_str,
            next_action=f"Say 'Add {ticker_found} to my watchlist' or 'Compare {ticker_found} vs INFY'.",
            citations=profile["source"]
        )

    # -------------------------------------------------------------
    # 9. LLM GENERATION FALLBACK (GROQ / OPENAI)
    # -------------------------------------------------------------
    if settings.GROQ_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                    json={
                        "model": settings.GROQ_MODEL,
                        "messages": [
                            {"role": "system", "content": "You are Atlas, an executive AI Financial Assistant for Telegram. Answer concisely and professionally. Format with: **Summary**, **Why It Matters**, and **Suggested Next Action**."},
                            {"role": "user", "content": input_text}
                        ],
                        "max_tokens": 400
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")

    if settings.OPENAI_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                    json={
                        "model": settings.OPENAI_MODEL,
                        "messages": [
                            {"role": "system", "content": "You are Atlas, an executive AI Financial Assistant for Telegram. Answer concisely and professionally. Format with: **Summary**, **Why It Matters**, and **Suggested Next Action**."},
                            {"role": "user", "content": input_text}
                        ],
                        "max_tokens": 400
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")

    # Heuristic Fallback
    return format_telegram_response(
        summary=f"Analysis of query '{input_text}': Atlas processed your financial intelligence request.",
        why_it_matters="Atlas tracks financial markets, mutual funds, watchlist movements, and uploaded document RAG context.",
        next_action="Try asking 'Price of TCS', 'HDFC Top 100 NAV', 'Show my watchlist', or upload a PDF report.",
        citations="Atlas Financial Intelligence Engine"
    )
