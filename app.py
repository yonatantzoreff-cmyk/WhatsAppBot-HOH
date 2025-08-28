# app.py
from fastapi import FastAPI, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from bot import process_incoming_message

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/twilio-webhook")
async def twilio_webhook(request: Request):
    form = await request.form()
    from_number = form.get("From", "")
    body = (form.get("Body") or "").strip()

    reply_text = process_incoming_message(body, from_number)

    resp = MessagingResponse()
    resp.message(reply_text)
    return Response(content=str(resp), media_type="application/xml")
