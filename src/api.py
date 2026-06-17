from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.messaging_response import MessagingResponse
from pydantic import BaseModel
from typing import Optional

from .handlers.telegram import setup_telegram_handlers
from .handlers.whatsapp import whatsapp_handler
from .config import settings

app = FastAPI(title="Bot Multi-plataforma")

# CORS para web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo para mensajes web
class WebMessage(BaseModel):
    message: str
    user_id: str
    platform: str  # "web", "whatsapp", etc.

# Endpoint para WhatsApp/Twilio
@app.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    form = await request.form()
    phone = form.get("From", "").replace("whatsapp:", "")
    message = form.get("Body", "")
    
    response_text = await whatsapp_handler.handle_message(phone, message)
    
    twiml = MessagingResponse()
    twiml.message(response_text)
    
    return Response(content=str(twiml), media_type="application/xml")

# Endpoint para chat web
@app.post("/web/chat")
async def web_chat(message_data: WebMessage):
    response_text = await whatsapp_handler.handle_message(
        message_data.user_id, 
        message_data.message
    )
    return {"response": response_text}

# Endpoint para obtener productos (API pública)
@app.get("/api/products")
async def get_products(category: Optional[str] = None):
    from .services.database import DatabaseService
    return DatabaseService.get_products(category=category)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)