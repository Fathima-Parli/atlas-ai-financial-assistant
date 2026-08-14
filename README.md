# Atlas AI Financial Assistant 📈

> **A Production-Grade AI Financial Intelligence Assistant for Telegram & Web**

**Atlas** is an intelligent AI Financial Assistant designed to eliminate friction in financial research. Built for finance professionals, portfolio managers, and equity researchers, Atlas turns complex financial workflows—stock quotes, mutual fund NAV lookups, persistent PDF report Q&A, coverage watchlists, and morning briefs—into one seamless, natural conversation on Telegram.

---

## 🎯 Problem

Financial research currently requires users to constantly switch between fragmented tools: financial portals for stock prices, AMFI sites for mutual fund NAVs, SEC EDGAR/BSE filings for PDFs, spreadsheets for watchlists, and messaging apps for team discussions. This manual context switching slows down executive decision-making.

---

## 💡 Solution

**Atlas** unifies financial intelligence inside Telegram. Users ask questions naturally (e.g. *"Price of TCS"*, *"HDFC Top 100 NAV"*, *"Add TCS to my watchlist"*, or upload an annual report PDF), and Atlas routes requests to real-time market APIs, vector RAG search, or persistent SQLite memory to deliver clear executive summaries with actionable next steps.

---

## ✨ Key Features

- **Natural Language Financial Queries**: Ask about equities, mutual funds, or filings in plain English.
- **Stock Information**: Real-time price, previous close, day change (%), open, high, low, 52-week range, P/E ratio, and market cap for Indian (TCS, RELIANCE, INFY) and US (NVDA, AAPL, MSFT, TSLA) equities.
- **Mutual Fund NAV Lookup**: Live AMFI/MFAPI integration with smart scheme resolution (e.g. mapping *"HDFC Top 100"* directly to *"HDFC Large Cap Fund - Direct Plan - Growth"*).
- **Personal Watchlist**: Natural language watchlist management (*"Add TCS"*, *"Remove TCS"*, *"Show my watchlist"*, *"Is TCS moving today?"*) stored persistently in SQLite.
- **PDF Document Question Answering (RAG)**: Upload annual reports or earnings PDFs to extract executive summaries, risk factors, and ask follow-up questions grounded strictly in the document.
- **Personalized Onboarding & Memory**: Natural conversation onboarding; remembers user roles, sector coverage, briefing times, and past context across sessions.
- **Proactive Daily Intelligence**: Automated Morning Market Briefs and Evening Wraps via background cron scheduler.
- **Multi-Modal Inputs**: Native support for **Text**, **Voice Messages** (with transcription), and **Chart Images**.

---

## 🏗️ Architecture Flow

```
User (Text / Voice / Image / PDF)
                ↓
    Telegram Bot API / Web Simulator
                ↓
           FastAPI Server
                ↓
    Natural Intent & Context Engine
        /       |        \        \
   Market API  MFAPI   SQLite DB  PDF RAG (TF-IDF/Cosine)
   (yfinance)  (AMFI)  (Watchlist)  (Vector Search)
        \       |        /        /
                 ↓
     LLM Engine (Groq / OpenAI / Heuristic)
                 ↓
         Telegram Response
 (Summary • Why It Matters • Suggested Next Action)
```

---

## 🛠️ Technologies Used

- **Language**: Python 3.14
- **Backend API**: FastAPI (Async support)
- **Database**: SQLite + Async SQLAlchemy ORM
- **Telegram Framework**: `python-telegram-bot`
- **LLM Integrations**: Groq API (`llama-3.3-70b-versatile`), OpenAI API (`gpt-4o`), with offline fallback
- **Market Data APIs**: Yahoo Finance (`yfinance`), Finnhub Market News
- **Mutual Fund API**: MFAPI / AMFI public API
- **Document Processing**: `pypdf` + custom TF-IDF & Cosine Similarity vector RAG engine
- **Task Scheduler**: APScheduler (`AsyncIOScheduler`)
- **Environment Management**: `python-dotenv` & `pydantic-settings`

---

## 📄 PDF Document Research (RAG Pipeline)

When a user uploads a financial PDF (e.g. 10-K, Annual Report, Quarterly Results):
1. **Extraction**: `pypdf` extracts raw document text.
2. **Chunking & Indexing**: Text is split into semantic chunks and indexed into SQLite `documents` table per user.
3. **Persistent Q&A**: Subsequent user questions (e.g. *"What was the revenue growth?"*, *"What are the major risks?"*) query the indexed document using TF-IDF & Cosine vector search.
4. **Grounded Answers**: Context is passed to the LLM to generate precise answers grounded in the PDF text.

---

## 📋 Natural Watchlist Management

Manage coverage assets conversationally without fixed command menus:
- *"Add TCS to my watchlist"* → Saves symbol to persistent SQLite `watchlists` table.
- *"Show my watchlist"* → Retrieves live prices, P/E ratios, and day changes.
- *"Is TCS moving today?"* → Analyzes intraday price movement against previous close.
- *"Remove TCS"* → Updates SQLite database state immediately.

---

## 🚀 Local Setup & Installation

### 1. Clone Repository & Create Virtual Environment

```bash
git clone https://github.com/your-username/atlas-ai-financial-assistant.git
cd atlas-ai-financial-assistant
python -m venv venv

# Activate on Windows:
venv\Scripts\activate

# Activate on Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create `.env` file in root folder (or copy `.env.example`):

```bash
cp .env.example .env
```

Set your configuration variables:

```env
ENV=development
DEBUG=True
PORT=8000
HOST=0.0.0.0

# Database
DATABASE_URL=sqlite+aiosqlite:///./atlas_financial.db

# Optional API Keys (Atlas includes built-in offline fallbacks if omitted)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
```

### 4. Run Backend & Web Simulator

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

Open your browser to **`http://localhost:8000`** to test the interactive **Telegram Web Simulator**!

### 5. Run Live Telegram Bot (Optional)

```bash
python -m telegram_bot.bot
```

---

## 💡 Example Telegram Interactions

- **Stock Price Query**:
  > **User**: *"What is the current price of TCS?"*  
  > **Atlas**: **Summary**: Tata Consultancy Services (TCS): Price ₹4,185.50 (+0.86%), Prev Close ₹4,150.00, Day High ₹4,210.00, Day Low ₹4,155.00, 52-Week Range ₹3,313.00 - ₹4,585.90.

- **Mutual Fund NAV Query**:
  > **User**: *"HDFC Top 100 NAV"*  
  > **Atlas**: **Summary**: Scheme: *HDFC Large Cap Fund - Direct Plan - Growth (Formerly HDFC Top 100 Fund)* | NAV: ₹118.45 | Fund House: HDFC Mutual Fund.

- **Watchlist Query**:
  > **User**: *"Add TCS to my watchlist"*  
  > **Atlas**: **Summary**: Added TCS to your persistent coverage watchlist.

---

## 📂 Project Architecture & Files

```
atlas-ai-financial-assistant/
├── backend/
│   ├── ai/
│   │   ├── analyst_agent.py    # Primary executive financial reasoning engine
│   │   ├── memory_manager.py   # Natural onboarding & SQLite context memory
│   │   └── rag_engine.py       # PDF extraction & TF-IDF vector RAG search
│   ├── database/
│   │   ├── session.py          # Async SQLAlchemy engine & session maker
│   │   └── models/models.py    # SQLite tables (User, Watchlist, Document, Alert)
│   ├── integrations/
│   │   ├── mfapi.py            # Mutual Fund NAV integration (AMFI / MFAPI)
│   │   ├── yahoo_finance.py    # Stock market quote & metrics integration
│   │   ├── sec_edgar.py        # SEC filings retriever
│   │   ├── finnhub_news.py     # Market news & earnings calendar
│   │   └── google_workspace.py # Google Calendar meeting prep & Gmail search
│   ├── routes/                 # FastAPI REST API endpoints
│   ├── scheduler/              # APScheduler background briefing cron jobs
│   ├── config.py               # Settings & Pydantic configuration
│   └── main.py                 # FastAPI application entrypoint
├── telegram_bot/
│   ├── bot.py                  # Long-polling Telegram bot script
│   ├── handlers.py             # Telegram text, voice, image, & document handlers
│   └── config.py               # Bot environment settings
├── web_simulator/
│   └── index.html              # Telegram Dark Mode Web Simulator UI
├── docs/
│   ├── ARCHITECTURE.md         # Architecture diagrams & DB model specifications
│   └── HACKATHON_DEMO_GUIDE.md # 6-step hackathon video demonstration guide
├── tests/
│   └── test_api.py             # Integration test suite
├── .env.example                # Example environment configuration
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

---

## 🔮 Future Improvements

- **Broader Mutual Fund Coverage**: Expanding direct scheme search across 2,500+ Indian mutual fund schemes with historical SIP calculator.
- **Advanced Financial Analysis**: Integrating DCF valuation models, Dupont analysis, and earnings surprise metrics.
- **Multi-Vector Database Migration**: Upgrading chunk storage to Qdrant or LanceDB for multi-gigabyte document libraries.
- **Portfolio Analytics**: Native CSV portfolio import to calculate Sharpe ratio, beta, and asset allocation risk scores.

---

## ⚠️ Disclaimer

Atlas AI Financial Assistant is an educational and research project created for hackathon evaluation. Information provided by Atlas does not constitute professional financial, legal, or investment advice.
