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
    body = request.form.get("Body", "").strip().lower()
    user = user_id(request)

    resp = MessagingResponse()

    # CONFIRMACIÓN
    if body in ["si", "sí", "no"] and user in seleccion_pendiente:
        p = seleccion_pendiente.pop(user)
        if body in ["si", "sí"]:
            resp.message(f"{p['nombre']} agregado al pedido.")
        else:
            resp.message("Producto no agregado.")
        return str(resp)

    # SELECCIÓN POR NÚMERO
    if body.isdigit():
        if user not in ultimos_resultados:
            resp.message("Primero busca un producto.")
            return str(resp)

        idx = int(body) - 1
        productos = ultimos_resultados[user]

        if 0 <= idx < len(productos):
            p = productos[idx]
            seleccion_pendiente[user] = p
            resp.message(
                f"¿Quieres agregar {p['nombre']} por ${p['precio']}? (si/no)"
            )
        else:
            resp.message("Número inválido.")
        return str(resp)

    # SALUDO
    if body in ["hola", "menu", "inicio"]:
        resp.message(saludo())
        return str(resp)

    # BÚSQUEDA
    productos = buscar(body, INVENTARIO)

    if productos:
        ultimos_resultados[user] = productos
        resp.message(lista_productos(productos))
    else:
        resp.message("No encontré productos con ese nombre.")

    return str(resp)

@app.route("/")
def home():
    return "Bot de tienda funcionando"
