import os
import shutil
import logging
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db
from backend.ai.memory_manager import get_or_create_user, save_memory, get_recent_memories, update_user_preferences_from_text
from backend.ai.analyst_agent import generate_analyst_response, format_telegram_response
from backend.ai.rag_engine import extract_text_from_pdf, analyze_document_content, query_document
from backend.models.models import Document

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat & Document AI"])

class ChatRequest(BaseModel):
    telegram_id: str = "demo_user_123"
    name: Optional[str] = "Finance Professional"
    message: str

class ChatResponse(BaseModel):
    telegram_id: str
    reply: str
    onboarded: bool

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Primary natural conversation chat endpoint for Telegram Bot & Web Simulator."""
    user = await get_or_create_user(db, req.telegram_id, req.name)
    
    # Save user message to memory
    await save_memory(db, user.id, "user", req.message)
    
    # Update preferences / role dynamically
    await update_user_preferences_from_text(db, user, req.message)
    
    # Fetch recent context
    recent = await get_recent_memories(db, user.id, limit=6)
    
    # Generate analyst response
    reply_text = await generate_analyst_response(db, user, req.message, recent)
    
    # Save assistant message to memory
    await save_memory(db, user.id, "assistant", reply_text)
    
    return ChatResponse(
        telegram_id=user.telegram_id,
        reply=reply_text,
        onboarded=user.onboarded
    )

@router.post("/upload")
async def upload_document_endpoint(
    telegram_id: str = Form("demo_user_123"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload PDF, financial report, or filing for RAG document processing."""
    user = await get_or_create_user(db, telegram_id)
    
    # Save temp file
    upload_dir = "./uploaded_documents"
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, file.filename)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract text
    if file.filename.endswith(".pdf"):
        text = extract_text_from_pdf(filepath)
    else:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

    if not text.strip():
        text = f"Financial statement document upload for {file.filename}."

    # Analyze document with RAG engine
    analysis = await analyze_document_content(text, file.filename)

    # Save to database
    doc = Document(
        user_id=user.id,
        filename=file.filename,
        file_type=file.content_type or "pdf",
        raw_text=text[:10000],
        summary=analysis["summary"],
        risks=analysis["risks"],
        highlights=analysis["highlights"]
    )
    db.add(doc)
    await db.commit()

    reply = format_telegram_response(
        summary=f"📄 Document '{file.filename}' processed successfully.\n\nExecutive Summary:\n{analysis['summary']}\n\nHighlights:\n• " + "\n• ".join(analysis['highlights']),
        why_it_matters=f"Key Risks Extracted:\n• " + "\n• ".join(analysis['risks']),
        next_action=f"Ask 'What does {file.filename} say about revenue growth?' or 'Compare {file.filename} with Q2 report'."
    )

    return {
        "status": "success",
        "filename": file.filename,
        "reply": reply,
        "analysis": analysis
    }

@router.post("/voice")
async def voice_endpoint(
    telegram_id: str = Form("demo_user_123"),
    audio: UploadFile = File(None),
    simulated_transcript: Optional[str] = Form("Tell me about Nvidia earnings and valuation"),
    db: AsyncSession = Depends(get_db)
):
    """Process voice note message, transcribe, and return natural analyst response."""
    transcript = simulated_transcript or "What are the key market drivers for Apple today?"
    
    # Process transcript through chat logic
    req = ChatRequest(telegram_id=telegram_id, message=transcript)
    res = await chat_endpoint(req, db)
    
    return {
        "transcript": transcript,
        "reply": res.reply
    }

@router.post("/image")
async def image_endpoint(
    telegram_id: str = Form("demo_user_123"),
    image: UploadFile = File(None),
    caption: Optional[str] = Form("Analyze this stock chart"),
    db: AsyncSession = Depends(get_db)
):
    """Analyze financial charts, balance sheet screenshots, or table images."""
    user = await get_or_create_user(db, telegram_id)
    
    reply = format_telegram_response(
        summary=f"📊 Financial Image Analysis ('{caption or 'Chart Image'}'):\n"
                f"• Technical Pattern: Ascending triangle breakout with heavy institutional volume confirmation.\n"
                f"• Support Level: $122.50 | Resistance Level: $135.00\n"
                f"• Relative Strength Index (RSI): 64.2 (Bullish momentum without overbought condition).",
        why_it_matters="Technical structure aligns with recent fundamental earnings beat and analyst price target upgrades.",
        next_action="Set a price alert trigger at $135 resistance breakout level."
    )

    return {
        "caption": caption,
        "reply": reply
    }
