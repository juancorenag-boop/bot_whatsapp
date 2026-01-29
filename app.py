from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

from inventory import INVENTARIO
from search import buscar
from responses import saludo, lista_productos

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    body = request.form.get("Body", "").strip()

    resp = MessagingResponse()

    if body.lower() in ["hola", "menu", "inicio"]:
        resp.message(saludo())
        return str(resp)

    productos = buscar(body, INVENTARIO)
    resp.message(lista_productos(productos))
    return str(resp)

@app.route("/")
def home():
    return "Bot de tienda funcionando 🚀"
