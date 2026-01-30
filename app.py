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
awaiting_payment = set()
awaiting_change = set()

BANK_INFO = (
    "🏦 *Datos para transferencia:*\n\n"
    "Banco: Bancolombia\n"
    "Cuenta: 123456789\n"
    "Tipo: Ahorros\n"
    "Nombre: Tienda XYZ\n\n"
    "Cuando realices el pago envía el comprobante 📸"
)

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    resp = MessagingResponse()
    resp.message("Webhook vivo desde Render ✅")
    return str(resp)
    
    # ---- SALUDO ----
    if text_lower in ["hola", "buenas", "hello", "menu", "inicio"]:
        msg.body(saludo())
        return str(resp)

    # ---- CAMBIO EN EFECTIVO ----
    if user in awaiting_change:
        msg.body(
            "✅ Pedido registrado correctamente 🙌\n"
            "En breve te contactamos para la entrega 🚚"
        )
        awaiting_change.discard(user)
        orders.pop(user, None)
        return str(resp)

    # ---- MÉTODO DE PAGO ----
    if user in awaiting_payment:
        if text_lower in ["transferencia", "1"]:
            msg.body(BANK_INFO)
            awaiting_payment.discard(user)
            orders.pop(user, None)
            return str(resp)

        if text_lower in ["efectivo", "2"]:
            msg.body(
                "💵 ¿Necesitas cambio?\n"
                "Ej: tengo 50.000 o escribe *exacto*"
            )
            awaiting_payment.discard(user)
            awaiting_change.add(user)
            return str(resp)

        msg.body("❌ Opción inválida. Escribe *transferencia* o *efectivo*.")
        return str(resp)

    # ---- DIRECCIÓN ----
    if user in awaiting_address:
        msg.body(
            "💳 ¿Cuál será tu método de pago?\n"
            "1️⃣ Transferencia\n"
            "2️⃣ Efectivo"
        )
        awaiting_address.discard(user)
        awaiting_payment.add(user)
        return str(resp)

    # ---- CONFIRMAR PEDIDO ----
    if text_lower == "confirmar" and user in awaiting_confirmation:
        msg.body("📍 Por favor escribe la dirección de entrega")
        awaiting_confirmation.discard(user)
        awaiting_address.add(user)
        return str(resp)

    # ---- QUITAR PRODUCTOS ----
    match_quitar = re.match(r"quitar\s+(\d+)\s+de\s+(.+)", text_lower)

    if match_quitar and user in awaiting_confirmation:
        cantidad = int(match_quitar.group(1))
        producto_txt = match_quitar.group(2)

        pedido = orders.get(user, [])
        for p in pedido:
            if producto_txt in p["tipo"]:
                if p["cantidad"] > cantidad:
                    p["cantidad"] -= cantidad
                else:
                    pedido.remove(p)
                break

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
        resumen += "👉 confirmar\n👉 quitar 1 de producto"

        awaiting_confirmation.add(user)
        msg.body(resumen)
        return str(resp)

    # ---- ESPERANDO CANTIDAD ----
    if user in pending_product and text.isdigit():
        producto = pending_product.pop(user)
        producto["cantidad"] = int(text)
        orders.setdefault(user, []).append(producto)

        msg.body(
            "✅ Producto agregado.\n\n"
            "¿Deseas agregar algo más?\n"
            "👉 Escribe el producto\n"
            "👉 O escribe *ok* para finalizar"
        )
        return str(resp)

    # ---- SELECCIÓN ----
    if text.isdigit() and user in last_results:
        idx = int(text) - 1
        productos = last_results[user]
        pending_product[user] = productos[idx].copy()
        msg.body(
            f"¿Cuántas unidades de "
            f"{productos[idx]['tipo'].title()} {productos[idx]['marca'].title()} deseas?"
        )
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
