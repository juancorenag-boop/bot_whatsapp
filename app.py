from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import re

from search import buscar
from responses import saludo, lista_productos

app = Flask(__name__)

orders = {}
last_results = {}
pending_product = {}
awaiting_confirmation = set()
awaiting_address = set()
addresses = {}

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

    # ---- RECIBIR DIRECCIÓN ----
    if user in awaiting_address:
        addresses[user] = text
        pedido = orders.get(user, [])

        resumen = "✅ *Pedido confirmado*\n\n📍 *Dirección:*\n"
        resumen += f"{text}\n\n🧾 *Detalle del pedido:*\n"

        total = 0
        for i, p in enumerate(pedido, start=1):
            subtotal = p["precio"] * p["cantidad"]
            resumen += (
                f"{i}. {p['cantidad']} x {p['tipo'].title()} {p['marca'].title()} "
                f"- ${subtotal}\n"
            )
            total += subtotal

        resumen += f"\n💰 *Total:* ${total}\n\n🙌 Gracias por tu compra"

        # limpiar todo
        orders.pop(user, None)
        last_results.pop(user, None)
        pending_product.pop(user, None)
        awaiting_confirmation.discard(user)
        awaiting_address.discard(user)
        addresses.pop(user, None)

        msg.body(resumen)
        return str(resp)

    # ---- CONFIRMAR PEDIDO ----
    if text_lower == "confirmar" and user in awaiting_confirmation:
        awaiting_confirmation.discard(user)
        awaiting_address.add(user)
        msg.body("📍 Por favor escribe tu *dirección de entrega*")
        return str(resp)

    # ---- QUITAR PRODUCTO ----
    match_quitar = re.match(r"quitar\s+(\d+)\s+de\s+(.+)", text_lower)

    if match_quitar and user in awaiting_confirmation:
        cantidad = int(match_quitar.group(1))
        producto_txt = match_quitar.group(2)

        pedido = orders.get(user, [])
        encontrado = False

        for p in pedido:
            if producto_txt in p["tipo"]:
                if p["cantidad"] > cantidad:
                    p["cantidad"] -= cantidad
                else:
                    pedido.remove(p)
                encontrado = True
                break

        if not encontrado:
            msg.body("❌ No encontré ese producto en tu pedido.")
            return str(resp)

        if not pedido:
            msg.body("🛒 Tu pedido quedó vacío.")
            awaiting_confirmation.discard(user)
            return str(resp)

        resumen = "🧾 Pedido actualizado:\n\n"
        total = 0
        for i, p in enumerate(pedido, start=1):
            subtotal = p["precio"] * p["cantidad"]
            resumen += (
                f"{i}. {p['cantidad']} x {p['tipo'].title()} {p['marca'].title()} "
                f"- ${subtotal}\n"
            )
            total += subtotal

        resumen += f"\n💰 Total: ${total}\n"
        resumen += "\n👉 confirmar\n👉 quitar 1 de producto"

        msg.body(resumen)
        return str(resp)

    # ---- MOSTRAR RESUMEN ----
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

        resumen += f"\n💰 *Total:* ${total}\n\n"
        resumen += "👉 Escribe *confirmar* para continuar\n"
        resumen += "👉 O *quitar 1 de producto*"

        awaiting_confirmation.add(user)
        msg.body(resumen)
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
