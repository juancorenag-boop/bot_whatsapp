from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

from inventory import INVENTARIO
from search import buscar
from responses import saludo, lista_productos

app = Flask(__name__)

# memoria simple
seleccion_pendiente = {}
ultimos_resultados = {}

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    body = request.form.get("Body", "").strip().lower()
    user = request.form.get("From")

    resp = MessagingResponse()

    # ---- CONFIRMACIÓN SI / NO ----
    if body in ["si", "sí", "no"] and user in seleccion_pendiente:
        producto = seleccion_pendiente.pop(user)

        if body in ["si", "sí"]:
            resp.message(f"✅ *{producto['nombre']}* agregado al pedido.")
        else:
            resp.message("❌ Producto no agregado.")

        return str(resp)

    # ---- SELECCIÓN POR NÚMERO ----
    if body.isdigit() and user in ultimos_resultados:
        idx = int(body) - 1
        productos = ultimos_resultados[user]

        if 0 <= idx < len(productos):
            p = productos[idx]
            seleccion_pendiente[user] = p
            resp.message(
                f"¿Quieres agregar *{p['nombre']}* por *${p['precio']}*? (sí/no)"
            )
        else:
            resp.message("❌ Opción inválida.")

        return str(resp)

    # ---- SALUDO ----
    if body in ["hola", "menu", "inicio"]:
        resp.message(saludo())
        return str(resp)

    # ---- BÚSQUEDA ----
    productos = buscar(body, INVENTARIO)
    ultimos_resultados[user] = productos

    resp.message(lista_productos(productos))
    return str(resp)

@app.route("/")
def home():
    return "Bot de tienda funcionando 🚀"

