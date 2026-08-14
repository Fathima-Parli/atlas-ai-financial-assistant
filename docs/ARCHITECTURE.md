# Atlas AI Financial Assistant - System Architecture

```
+-----------------------------------------------------------------------------------+
|                                 FRONTEND LAYER                                    |
|                                                                                   |
|    +-----------------------------+               +---------------------------+    |
|    | Telegram Bot Interface      |               | Web Telegram Simulator UI |    |
|    | (python-telegram-bot async) |               | (HTML5 / Dark Glass CSS)  |    |
|    +--------------+--------------+               +-------------+-------------+    |
+-------------------|--------------------------------------------|------------------+
                    |                                            |
                    +--------------------+   +-------------------+
                                         |   |
                                         v   v
+-----------------------------------------------------------------------------------+
|                                 BACKEND API LAYER                                 |
|                                  (FastAPI Async)                                  |
|                                                                                   |
|   +-------------------+  +-------------------+  +------------------------------+  |
|   | /chat Endpoint    |  | /upload Endpoint  |  | /watchlist & /alerts         |  |
|   | /voice & /image   |  | RAG Parser        |  | /daily-brief & /google       |  |
|   +---------+---------+  +---------+---------+  +--------------+---------------+  |
+-------------|----------------------|---------------------------|------------------+
              |                      |                           |
              v                      v                           v
+-----------------------------------------------------------------------------------+
|                                AI & INTELLIGENCE LAYER                            |
|                                                                                   |
|   +-------------------+  +-------------------+  +------------------------------+  |
|   | Memory Manager    |  | RAG Vector Search |  | Executive Analyst Agent      |  |
|   | Onboarding Engine |  | TF-IDF & Cosine   |  | OpenAI GPT-4o / Heuristic    |  |
|   +-------------------+  +-------------------+  +------------------------------+  |
+-----------------------------------------------------------------------------------+
                                     |
                                     v
+-----------------------------------------------------------------------------------+
|                            INTEGRATIONS & DATA PROVIDERS                          |
|                                                                                   |
|   +-------------------+  +-------------------+  +------------------------------+  |
|   | Yahoo Finance API |  | SEC EDGAR Parser  |  | Finnhub & Google Workspace   |  |
|   +-------------------+  +-------------------+  +------------------------------+  |
+-----------------------------------------------------------------------------------+
                                     |
                                     v
+-----------------------------------------------------------------------------------+
|                                 DATABASE & SCHEDULER                              |
|                                                                                   |
|   +---------------------------------------+  +--------------------------------+   |
|   | SQLite / PostgreSQL Database          |  | APScheduler Background Jobs    |   |
|   | User, Watchlist, Document, Memory DB  |  | Morning/Evening Brief Cron     |   |
|   +---------------------------------------+  +--------------------------------+   |
+-----------------------------------------------------------------------------------+
```

## Database Schema (SQLAlchemy Models)
1. **User**: Stores Telegram ID, role, onboarding progress.
2. **Preferences**: Stores briefing schedules, sector interests, alert settings.
3. **ConversationMemory**: Stores contextual turn history, extracted entities, and research queries.
4. **Watchlist**: Tracked equity tickers per user.
5. **Alert**: Threshold alerts (e.g. % drops, SEC filings, earnings).
6. **Document**: PDF and report metadata, chunk embeddings, executive summaries, risk lists.
7. **Meeting**: Google Calendar meeting notes and AI prep checklists.
8. **Notification**: History of morning/evening briefs and breaking alerts delivered.
