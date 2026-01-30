from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import re

from search import buscar
from responses import saludo, lista_productos

app = Flask(__name__)

orders = {}         # pedidos por usuario
last_results = {}   # últimos resultados mostrados

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

        # limpiar estado
        orders.pop(user, None)
        last_results.pop(user, None)

        return str(resp)

    # ---- CANTIDAD EXPLÍCITA (ej: 2 de arroz) ----
    match = re.match(r"^\s*(\d+)\s+de\s+(.+)", text_lower)

    if match:
        cantidad = int(match.group(1))
        producto_txt = match.group(2)

        resultados = buscar(producto_txt)

        if not resultados:
            msg.body("❌ No encontré ese producto.")
            return str(resp)

        producto = resultados[0].copy()
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
            producto = productos[idx].copy()
            producto["cantidad"] = 1

            orders.setdefault(user, []).append(producto)

            msg.body(
                f"✅ *{producto['tipo'].title()} {producto['marca'].title()}* agregado.\n\n"
                "¿Deseas agregar algo más?\n"
                "👉 Escribe el nombre del producto\n"
                "👉 O escribe *ok* para finalizar"
            )
        else:
            msg.body("❌ Número inválido.")

        return str(resp)

    # ---- BÚSQUEDA POR TEXTO ----
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

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
