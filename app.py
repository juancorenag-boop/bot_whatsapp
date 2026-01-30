from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

from search import buscar
from responses import saludo, lista_productos

app = Flask(__name__)

orders = {}             # pedidos finales
last_results = {}       # últimos resultados mostrados
pending_product = {}    # producto seleccionado esperando cantidad

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    text = request.values.get("Body", "").strip()
    user = request.values.get("From")

    resp = MessagingResponse()
    msg = resp.message()

    text_lower = text.lower()

    # ---- SALUDO ----
    if text_lower in ["hola", "buenas", "hello", "menu", "inicio"]:
        msg.body(saludo())
        return str(resp)

    # ---- FINALIZAR PEDIDO ----
    if text_lower == "ok":
        pedido = orders.get(user, [])

        if not pedido:
            msg.body("🛒 Tu pedido está vacío.")
            return str(resp)

        resumen = "🧾 *Resumen de tu pedido:*\n\n"
        total = 0

        for i, p in enumerate(pedido, start=1):
            subtotal = p["precio"] * p["cantidad"]
            resumen += (
                f"{i}. {p['cantidad']} x {p['tipo'].title()} {p['marca'].title()} "
                f"- ${subtotal}\n"
            )
            total += subtotal

        resumen += f"\n💰 *Total:* ${total}\n"
        resumen += "\nGracias por tu compra 🙌"

        msg.body(resumen)

        orders.pop(user, None)
        last_results.pop(user, None)
        pending_product.pop(user, None)

        return str(resp)

    # ---- ESPERANDO CANTIDAD ----
    if user in pending_product and text.isdigit():
        cantidad = int(text)
        producto = pending_product.pop(user)
        producto["cantidad"] = cantidad

        orders.setdefault(user, []).append(producto)

        msg.body(
            f"✅ Agregado:\n"
            f"{cantidad} x {producto['tipo'].title()} {producto['marca'].title()} "
            f"- ${producto['precio']} c/u\n\n"
            "¿Deseas agregar algo más?\n"
            "👉 Escribe el producto\n"
            "👉 O escribe *ok* para finalizar"
        )
        return str(resp)

    # ---- SELECCIÓN POR NÚMERO ----
    if text.isdigit() and user in last_results:
        idx = int(text) - 1
        productos = last_results[user]

        if 0 <= idx < len(productos):
            pending_product[user] = productos[idx].copy()
            msg.body(
                f"¿Cuántas unidades de "
                f"{productos[idx]['tipo'].title()} {productos[idx]['marca'].title()} deseas?"
            )
        else:
            msg.body("❌ Número inválido.")
        return str(resp)

    # ---- BÚSQUEDA ----
    resultados = buscar(text_lower)

    if resultados:
        last_results[user] = resultados
        msg.body(lista_productos(resultados))
    else:
        msg.body("❌ No encontré productos con ese nombre.")

    return str(resp)

@app.route("/")
def home():
    return "Bot de tienda funcionando 🚀"
