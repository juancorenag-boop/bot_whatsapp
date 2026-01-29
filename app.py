from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    from_number = request.form.get("From")
    body = request.form.get("Body") or ""
    body = body.strip().lower()

    print("📩 Mensaje recibido")
    print("From:", from_number)
    print("Body:", body)

    resp = MessagingResponse()
    
    if body in ["hola", "menu"]:
        resp.message("¡Hola! Bot funcionando ✅")
    else:
        resp.message("❓ No entendí tu mensaje. Escribe 'hola'.")

    return str(resp)

@app.route("/")
def home():
    return "Bot activo 🚀"
