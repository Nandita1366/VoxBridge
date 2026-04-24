import os
import asyncio
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant
import json

from config import BASE_URL, TWILIO_ACCOUNT_SID, TWILIO_API_KEY, TWILIO_API_SECRET, TWIML_APP_SID
from database import init_db, get_db
from models import CallSession, Order, TranscriptEntry
from websocket_manager import ws_manager
from twilio_handler import build_greeting_twiml, build_bot_reply_twiml, build_no_input_twiml
from stt import transcribe_speech_result
from nlp import get_bot_reply
from sentiment import analyze_sentiment, update_session_sentiment
from notifications import send_order_confirmation_whatsapp, send_sms_fallback

app = FastAPI(title="VoxBridge API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSIONS: dict = {}

os.makedirs("audio_cache", exist_ok=True)
app.mount("/audio", StaticFiles(directory="audio_cache"), name="audio")


@app.on_event("startup")
async def startup():
    await init_db()
    print(f"[VoxBridge] Server started. BASE_URL = {BASE_URL}")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "VoxBridge", "version": "1.0.0"}


@app.get("/api/token")
async def get_access_token():
    token = AccessToken(
        TWILIO_ACCOUNT_SID,
        TWILIO_API_KEY,
        TWILIO_API_SECRET,
        identity="demo-browser-caller",
        ttl=3600,
    )
    token.add_grant(VoiceGrant(outgoing_application_sid=TWIML_APP_SID, incoming_allow=True))
    return {"token": token.to_jwt()}


@app.post("/voice/inbound")
async def voice_inbound(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    call_sid = form.get("CallSid", "UNKNOWN")
    from_number = form.get("From", "")

    SESSIONS[call_sid] = {
        "history": [],
        "language": "en-IN",
        "lang_code": "en",
        "neg_streak": 0,
        "phone": from_number,
    }

    session_record = CallSession(call_sid=call_sid, phone_number=from_number, status="active")
    db.add(session_record)
    await db.commit()

    await ws_manager.broadcast(
        {
            "type": "new_call",
            "call_sid": call_sid,
            "phone": from_number,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )

    return Response(content=build_greeting_twiml(call_sid), media_type="text/xml")


@app.post("/voice/process/{call_sid}")
async def voice_process(call_sid: str, request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    speech_result = form.get("SpeechResult", "")
    confidence = float(form.get("Confidence", 0.5))

    session = SESSIONS.get(
        call_sid,
        {"history": [], "language": "en-IN", "lang_code": "en", "neg_streak": 0, "phone": ""},
    )

    # ── Low-confidence / empty input: replay in caller's language ────────────
    if not speech_result or confidence < 0.3:
        return Response(
            content=build_no_input_twiml(call_sid, session.get("language", "en-IN")),
            media_type="text/xml",
        )

    bcp47 = session.get("language", "en-IN")
    stt_result = transcribe_speech_result(speech_result, bcp47)

    sentiment = analyze_sentiment(speech_result)
    session = update_session_sentiment(session, sentiment)

    should_escalate = session.get("should_escalate", False)
    should_slow = session.get("should_slow_down", False)

    nlp_result = get_bot_reply(
        customer_text=speech_result,
        language_name=stt_result["lang_name"],
        conversation_history=session.get("history", []),
        sentinel_mode=should_slow,
    )
    session["history"] = nlp_result["updated_history"]

    # Lock in detected language after the first turn
    if len(session["history"]) <= 2:
        session["language"] = stt_result["bcp47"]
        session["lang_code"] = stt_result["detected_lang_code"]

    SESSIONS[call_sid] = session

    db.add(
        TranscriptEntry(
            call_sid=call_sid,
            role="customer",
            text=speech_result,
            language=session["lang_code"],
            sentiment=sentiment["label"],
        )
    )
    db.add(
        TranscriptEntry(
            call_sid=call_sid,
            role="bot",
            text=nlp_result["tts_text"],
            language=session["lang_code"],
            sentiment="NEUTRAL",
        )
    )
    await db.commit()

    await ws_manager.broadcast(
        {
            "type": "transcript_update",
            "call_sid": call_sid,
            "customer_text": speech_result,
            "bot_text": nlp_result["tts_text"],
            "language": session["lang_code"],
            "bcp47": session["language"],
            "sentiment": sentiment["label"],
            "neg_streak": session["neg_streak"],
            "sentinel_active": should_slow,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )

    if should_escalate:
        await db.execute(
            CallSession.__table__.update()
            .where(CallSession.call_sid == call_sid)
            .values(status="escalated")
        )
        await db.commit()
        await ws_manager.broadcast(
            {"type": "escalation", "call_sid": call_sid, "reason": "Customer frustration threshold reached"}
        )
        return Response(
            content=build_bot_reply_twiml("", call_sid, session["language"], sentinel_escalate=True),
            media_type="text/xml",
        )

    if nlp_result["order_confirmed"]:
        order_data = nlp_result["order_data"]
        new_order = Order(
            call_sid=call_sid,
            phone_number=session.get("phone", ""),
            item_name=order_data.get("item", ""),
            quantity=int(order_data.get("qty", 1)),
            delivery_address=order_data.get("address", ""),
            language=session["lang_code"],
            raw_transcript=speech_result,
            confirmed=True,
        )
        db.add(new_order)

        await db.execute(
            CallSession.__table__.update()
            .where(CallSession.call_sid == call_sid)
            .values(status="completed", language=session["lang_code"])
        )
        await db.commit()

        phone = session.get("phone", "")
        wa_sent = send_order_confirmation_whatsapp(phone, order_data, session["lang_code"])
        if not wa_sent:
            send_sms_fallback(phone, order_data)

        await ws_manager.broadcast(
            {
                "type": "order_confirmed",
                "call_sid": call_sid,
                "order": order_data,
                "language": session["lang_code"],
                "whatsapp_sent": wa_sent,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        return Response(
            content=build_bot_reply_twiml(
                nlp_result["tts_text"], call_sid, session["language"], is_final=True
            ),
            media_type="text/xml",
        )

    return Response(
        content=build_bot_reply_twiml(
            nlp_result["tts_text"], call_sid, session["language"], is_final=False
        ),
        media_type="text/xml",
    )


@app.post("/voice/no-input/{call_sid}")
async def voice_no_input(call_sid: str):
    # ── Look up the session language so the prompt is in the caller's language ─
    session = SESSIONS.get(call_sid, {})
    bcp47 = session.get("language", "en-IN")
    return Response(content=build_no_input_twiml(call_sid, bcp47), media_type="text/xml")


@app.get("/api/calls")
async def get_calls(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CallSession).order_by(CallSession.created_at.desc()).limit(50))
    calls = result.scalars().all()
    return [
        {
            "id": c.id,
            "call_sid": c.call_sid,
            "phone": c.phone_number,
            "language": c.language,
            "status": c.status,
            "sentiment_score": c.sentiment_score,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in calls
    ]


@app.get("/api/orders")
async def get_orders(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).order_by(Order.created_at.desc()).limit(100))
    orders = result.scalars().all()
    return [
        {
            "id": o.id,
            "call_sid": o.call_sid,
            "phone": o.phone_number,
            "item": o.item_name,
            "qty": o.quantity,
            "address": o.delivery_address,
            "language": o.language,
            "confirmed": o.confirmed,
            "whatsapp_sent": o.whatsapp_sent,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orders
    ]


@app.get("/api/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    total_calls = await db.scalar(select(func.count(CallSession.id)))
    total_orders = await db.scalar(
        select(func.count(Order.id)).where(Order.confirmed == True)
    )
    escalated = await db.scalar(
        select(func.count(CallSession.id)).where(CallSession.status == "escalated")
    )
    lang_result = await db.execute(
        select(Order.language, func.count(Order.id))
        .where(Order.confirmed == True)
        .group_by(Order.language)
    )
    lang_dist = {row[0]: row[1] for row in lang_result}

    return {
        "total_calls": total_calls or 0,
        "confirmed_orders": total_orders or 0,
        "escalations": escalated or 0,
        "language_distribution": lang_dist,
    }


@app.get("/api/transcript/{call_sid}")
async def get_transcript(call_sid: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TranscriptEntry)
        .where(TranscriptEntry.call_sid == call_sid)
        .order_by(TranscriptEntry.created_at)
    )
    entries = result.scalars().all()
    return [
        {
            "role": e.role,
            "text": e.text,
            "language": e.language,
            "sentiment": e.sentiment,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in entries
    ]


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(30)
            await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)