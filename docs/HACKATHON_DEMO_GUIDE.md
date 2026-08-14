# Atlas AI Financial Assistant — Hackathon Demo & Video Guide

This guide details the step-by-step 6-part demo script for hackathon video recording or judge evaluation.

---

## 🎬 Hackathon Video Demonstration Flow (6 Steps)

### Demo 1 — Natural Conversational Onboarding
- **Action**: Open the Telegram Bot or Web Simulator at `http://localhost:8000`. Send a message or click "Start".
- **Atlas Response**: *"Hello 👋 I'm Atlas, your AI Financial Assistant... What best describes your role?"*
- **User Prompt**: *"Senior Equity Analyst covering Technology & Semiconductors"*
- **Atlas Response**: Remembers role in persistent SQLite database and asks for tracked tickers.

### Demo 2 — Real-Time Stock Query
- **User Prompt**: `"What is the current price of TCS?"`
- **Atlas Response**:
  - **Summary**: Tata Consultancy Services Limited (TCS): Price ₹4,185.50 (+0.86%), Previous Close ₹4,150.00, Open ₹4,160.00, High ₹4,210.00, Low ₹4,155.00, 52-Week Range ₹3,313.00 - ₹4,585.90, P/E 31.5x, Market Cap ₹15.14 Trillion.
  - **Why It Matters**: Sector context & market capital allocation.
  - **Source Citation**: Yahoo Finance / Market Data API.

### Demo 3 — Mutual Fund NAV Lookup (HDFC Top 100 / Large Cap Fund)
- **User Prompt**: `"HDFC Top 100 NAV"` (or `"Tell me about HDFC Large Cap Fund NAV"`)
- **Atlas Response**:
  - **Exact Scheme Name**: *HDFC Large Cap Fund - Direct Plan - Growth (Formerly HDFC Top 100 Fund)*
  - **Scheme Code**: 119061
  - **NAV**: ₹118.45
  - **Category**: Equity Scheme - Large Cap Fund
  - **Why It Matters**: Identifies that HDFC Top 100 was renamed to HDFC Large Cap Fund and fetches verified AMFI NAV data.

### Demo 4 — Persistent Watchlist Management
- **User Prompt 1**: `"Add TCS to my watchlist"`
- **Atlas Response**: *"Added TCS to your persistent coverage watchlist."*
- **User Prompt 2**: `"Show my watchlist"`
- **Atlas Response**: Displays active tracked equities stored in SQLite with real-time price updates (TCS, NVDA, AAPL).

### Demo 5 — PDF Document Question Answering (RAG)
- **Action**: Click 📎 in Web Simulator or upload a PDF report in Telegram (e.g. `Q3_Financial_Report.pdf`).
- **Atlas Response**: Processes PDF, extracts text, indexes semantic chunks, and extracts key highlights & risk factors.
- **User Follow-Up Questions (Without Re-uploading)**:
  - Question 1: *"What was the revenue growth?"*
  - Question 2: *"What are the major risks mentioned in the report?"*
  - Question 3: *"Summarize the management discussion."*
- **Atlas Response**: Answers grounded directly in the uploaded document using TF-IDF RAG retrieval.

### Demo 6 — Personalization & Long-Term Context
- **User Prompt**: `"What companies am I tracking and what is my role?"`
- **Atlas Response**: Retrieves stored user profile, role (*Senior Equity Analyst*), sector preferences, and watchlist tickers from SQLite `users` and `preferences` tables.
