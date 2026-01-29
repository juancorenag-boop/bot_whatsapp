from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    body = request.form.get("Body") or ""
    body = body.strip().lower()

    print("📩 Mensaje recibido")
    print("Body:", body)

    resp = MessagingResponse()
    resp.message("Hola! Este es un mensaje de prueba sin acentos ni caracteres especiales.")
    return str(resp)
