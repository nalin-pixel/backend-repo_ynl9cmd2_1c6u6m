import os
import uuid
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents

app = FastAPI(title="AI Booking Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    session_id: Optional[str] = None
    message: str
    language: str = "en"  # en, ne, hi, ar, es

class BookingCreate(BaseModel):
    name: str
    service: str
    date: str
    time: str
    location: str
    phone: str
    language: str = "en"

@app.get("/")
def read_root():
    return {"message": "AI Booking Assistant Backend Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set"
            response["database_name"] = getattr(db, 'name', '✅ Connected')
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

@app.post("/api/chat")
def chat(message: ChatMessage):
    # Very simple rule-based assistant to drive booking flow
    # Persist minimal interaction log
    session_id = message.session_id or str(uuid.uuid4())
    try:
        create_document("interaction", {
            "session_id": session_id,
            "role": "user",
            "message": message.message,
            "language": message.language,
        })
    except Exception:
        pass

    # Naive intent detection
    text = message.message.lower()
    prompts = {
        "en": {
            "greet": "Hi! I’m your AI booking assistant. What service would you like to book?",
            "ask_name": "Got it. May I have your full name?",
            "ask_date": "What date works best for you? (YYYY-MM-DD)",
            "ask_time": "What time do you prefer? (HH:MM)",
            "ask_location": "Where should we provide the service?",
            "ask_phone": "Please share your WhatsApp number with country code (e.g., +1..., +91...).",
            "confirm": "Thanks! I’ll confirm your booking now.",
        },
        "es": {
            "greet": "¡Hola! Soy tu asistente de reservas. ¿Qué servicio necesitas?",
            "ask_name": "Perfecto. ¿Cuál es tu nombre completo?",
            "ask_date": "¿Qué fecha te viene mejor? (AAAA-MM-DD)",
            "ask_time": "¿Qué hora prefieres? (HH:MM)",
            "ask_location": "¿Dónde brindaremos el servicio?",
            "ask_phone": "Comparte tu número de WhatsApp con código de país.",
            "confirm": "¡Gracias! Confirmaré tu reserva ahora.",
        },
        "hi": {
            "greet": "नमस्ते! मैं आपका बुकिंग सहायक हूँ। आप कौन सी सेवा बुक करना चाहते हैं?",
            "ask_name": "ठीक है। आपका पूरा नाम क्या है?",
            "ask_date": "आपकी पसंदीदा तारीख क्या है? (YYYY-MM-DD)",
            "ask_time": "आपको किस समय पसंद है? (HH:MM)",
            "ask_location": "सेवा कहाँ प्रदान करनी है?",
            "ask_phone": "कृपया अपना व्हाट्सएप नंबर देश कोड के साथ साझा करें।",
            "confirm": "धन्यवाद! मैं आपकी बुकिंग की पुष्टि कर रहा हूँ।",
        },
        "ar": {
            "greet": "مرحباً! أنا مساعد الحجز الذكي. ما الخدمة التي ترغب بحجزها؟",
            "ask_name": "حسناً، ما اسمك الكامل؟",
            "ask_date": "ما التاريخ المناسب لك؟ (YYYY-MM-DD)",
            "ask_time": "ما الوقت المفضل لديك؟ (HH:MM)",
            "ask_location": "أين سيتم تقديم الخدمة؟",
            "ask_phone": "من فضلك شارك رقم واتساب مع رمز الدولة.",
            "confirm": "شكراً لك! سأقوم بتأكيد الحجز الآن.",
        },
        "ne": {
            "greet": "नमस्ते! म तपाईंको बुकिङ सहायक हुँ। तपाईँ कुन सेवा चाहनुहुन्छ?",
            "ask_name": "ठिक छ। तपाईँको पूरा नाम के हो?",
            "ask_date": "कुन मिति मिल्छ? (YYYY-MM-DD)",
            "ask_time": "कुन समय ठीक पर्छ? (HH:MM)",
            "ask_location": "सेवा कहाँ दिने?",
            "ask_phone": "देश कोड सहित आफ्नो WhatsApp नम्बर दिनुहोस्।",
            "confirm": "धन्यवाद! अब म बुकिङ पुष्टि गर्छु।",
        }
    }
    lang = message.language if message.language in prompts else "en"

    # simple flow hints based on keywords
    if any(k in text for k in ["hi", "hello", "book", "reserve", "appointment"]):
        reply = prompts[lang]["greet"]
    elif any(k in text for k in ["hair", "clean", "wash", "service", "consult", "repair", "salon", "spa", "plumbing", "ac", "electric"]):
        reply = prompts[lang]["ask_name"]
    elif any(k in text for k in ["mr ", "mrs ", "my name", "i am", "i'm"]):
        reply = prompts[lang]["ask_date"]
    elif any(ch.isdigit() for ch in text) and "-" in text and text.count("-") >= 2:
        reply = prompts[lang]["ask_time"]
    elif ":" in text and any(h in text for h in ["am", "pm", "00", "30", "45", "15"]):
        reply = prompts[lang]["ask_location"]
    elif any(k in text for k in ["street", "road", "avenue", "near", "building", "city", "area", "block"]):
        reply = prompts[lang]["ask_phone"]
    elif "+" in text or any(k in text for k in ["whatsapp", "phone", "mobile"]):
        reply = prompts[lang]["confirm"]
    else:
        reply = prompts[lang]["greet"]

    try:
        create_document("interaction", {
            "session_id": session_id,
            "role": "assistant",
            "message": reply,
            "language": lang,
        })
    except Exception:
        pass

    return {"session_id": session_id, "reply": reply}

@app.post("/api/bookings")
def create_booking(payload: BookingCreate):
    try:
        booking_id = create_document("booking", payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Try to notify WhatsApp using a simple webhook-friendly service if provided
    whatsapp_webhook = os.getenv("WHATSAPP_WEBHOOK_URL")
    if whatsapp_webhook:
        try:
            import requests
            requests.post(whatsapp_webhook, json={
                "type": "booking_confirmation",
                "booking_id": booking_id,
                "payload": payload.model_dump(),
            }, timeout=6)
        except Exception:
            pass

    return {"id": booking_id, "status": "confirmed"}

@app.get("/api/bookings")
def list_bookings(limit: int = 100):
    try:
        items = get_documents("booking", {}, limit)
        for doc in items:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/interactions")
def list_interactions(limit: int = 200):
    try:
        logs = get_documents("interaction", {}, limit)
        # Convert ObjectId to str if present
        for doc in logs:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
        return {"items": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
