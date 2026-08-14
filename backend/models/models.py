import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.database.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True)
    role = Column(String(100), nullable=True) # e.g., Hedge Fund Analyst, CFO, Private Investor
    onboarded = Column(Boolean, default=False)
    onboarding_step = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    preferences = relationship("Preferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    memories = relationship("ConversationMemory", back_populates="user", cascade="all, delete-orphan")
    watchlists = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    meetings = relationship("Meeting", back_populates="user", cascade="all, delete-orphan")
    google_account = relationship("GoogleAccount", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Preferences(Base):
    __tablename__ = "preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    preferred_sectors = Column(JSON, default=list) # e.g. ["Tech", "Biotech", "Semiconductors"]
    companies_to_monitor = Column(JSON, default=list) # e.g. ["NVDA", "AAPL", "MSFT"]
    briefing_time = Column(String(10), default="08:00") # HH:MM format
    morning_brief = Column(Boolean, default=True)
    evening_brief = Column(Boolean, default=True)
    sec_alerts = Column(Boolean, default=True)
    earnings_alerts = Column(Boolean, default=True)
    market_news = Column(Boolean, default=True)

    user = relationship("User", back_populates="preferences")


class ConversationMemory(Base):
    __tablename__ = "conversation_memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), nullable=False) # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    extracted_entities = Column(JSON, default=dict) # e.g. {"companies": ["NVIDIA"], "intent": "research"}
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="memories")


class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    company_name = Column(String(100), nullable=True)
    target_price = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    added_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="watchlists")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    condition = Column(String(50), nullable=False) # e.g. 'drop_pct', 'rise_pct', 'sec_filing', 'earnings'
    threshold_value = Column(Float, nullable=True) # e.g. 5.0 for 5% drop
    active = Column(Boolean, default=True)
    triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="alerts")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False) # pdf, txt, csv, 10k, 10q
    raw_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    risks = Column(JSON, default=list)
    highlights = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="documents")


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    date_time = Column(DateTime, nullable=False)
    participants = Column(JSON, default=list)
    company_symbol = Column(String(20), nullable=True)
    prep_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="meetings")


class GoogleAccount(Base):
    __tablename__ = "google_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    email = Column(String(150), nullable=True)
    connected = Column(Boolean, default=False)
    access_token = Column(String(255), nullable=True)
    refresh_token = Column(String(255), nullable=True)
    connected_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="google_account")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    why_it_matters = Column(Text, nullable=False)
    category = Column(String(50), default="market_brief") # morning_brief, evening_brief, breaking, sec_filing, earnings, watchlist
    sent_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class MarketEvent(Base):
    __tablename__ = "market_events"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    event_type = Column(String(50), nullable=False) # e.g., earnings, sec_filing, news
    headline = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    impact_score = Column(Float, default=0.5) # 0.0 to 1.0 scale
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
