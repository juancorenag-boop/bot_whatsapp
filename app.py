from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

from inventory import INVENTARIO
from search import buscar
from responses import saludo, lista_productos

app = Flask(__name__)  # ⚠️ ESTO DEBE IR ANTES

# memoria simple de selección pendiente
seleccion_pendiente = {}

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    body = request.form.get("Body", "").strip().lower()
    user = request.form.get("From")  # identificador del usuario

    resp = MessagingResponse()

    # ---- CONFIRMACIÓN SI / NO ----
    if body in ["si", "sí", "no"] and user in seleccion_pendiente:
        producto = seleccion_pendiente.pop(user)

        if body in ["si", "sí"]:
            resp.message(f"✅ *{producto['nombre']}* agregado al pedido.")
        else:
            resp.message("❌ Producto no agregado.")

        return str(resp)

    # ---- SALUDO ----
    if body in ["hola", "menu", "inicio"]:
        resp.message(saludo())
        return str(resp)

    # ---- BÚSQUEDA DE PRODUCTOS ----
    productos = buscar(body, INVENTARIO)

    # si encuentra exactamente 1 producto → pedir confirmación
    if len(productos) == 1:
        p = productos[0]
        seleccion_pendiente[user] = p
        resp.message(
            f"¿Quieres agregar *{p['nombre']}* por *${p['precio']}*? (sí/no)"
        )
        return str(resp)

    # si hay varios o ninguno → comportamiento original
    resp.message(lista_productos(productos))
    return str(resp)

@app.route("/")
def home():
    return "Bot de tienda funcionando 🚀"
