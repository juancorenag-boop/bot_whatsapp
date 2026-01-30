from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

from inventory import INVENTARIO
from search import buscar
from responses import saludo, lista_productos

app = Flask(__name__)

ultimos_resultados = {}
seleccion_pendiente = {}

def user_id(req):
    return req.form.get("From", "").replace("whatsapp:", "")

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    body_raw = request.form.get("Body", "").strip()
    body = body_raw.lower()
    user = user_id(request)

    resp = MessagingResponse()

    # ---- CONFIRMACIÓN SI / NO ----
    if body in ["si", "sí", "no"] and user in seleccion_pendiente:
        p = seleccion_pendiente.pop(user)
        if body in ["si", "sí"]:
            resp.message(f"✅ {p['nombre']} agregado al pedido.")
        else:
            resp.message("❌ Producto no agregado.")
        return str(resp)

    # ---- SELECCIÓN POR NÚMERO (SOLO SI YA HAY LISTA) ----
    if body.isdigit() and user in ultimos_resultados:
        productos = ultimos_resultados[user]
        idx = int(body) - 1

        if 0 <= idx < len(productos):
            p = productos[idx]
            seleccion_pendiente[user] = p
            resp.message(
                f"¿Quieres agregar {p['nombre']} por ${p['precio']}? (si/no)"
            )
        else:
            resp.message("❌ Número inválido.")
        return str(resp)

    # ---- SALUDO ----
    if body in ["hola", "menu", "inicio"]:
        ultimos_resultados.pop(user, None)
        seleccion_pendiente.pop(user, None)
        resp.message(saludo())
        return str(resp)

    # ---- BÚSQUEDA POR NOMBRE (ESTO SIEMPRE FUNCIONA) ----
    productos = buscar(body, INVENTARIO)

    if productos:
        ultimos_resultados[user] = productos
        resp.message(lista_productos(productos))
    else:
        resp.message("❌ No encontré productos con ese nombre.")

    return str(resp)

@app.route("/")
def home():
    return "Bot de tienda funcionando"

