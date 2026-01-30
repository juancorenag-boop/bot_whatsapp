from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import re

from search import buscar
from responses import saludo, lista_productos

app = Flask(__name__)

# memoria simple
orders = {}
pending_product = {}
awaiting_confirmation = set()
awaiting_address = set()
awaiting_payment = set()

def limpiar_usuario(user_id):
    orders.pop(user_id, None)
    pending_product.pop(user_id, None)
    awaiting_confirmation.discard(user_id)
    awaiting_address.discard(user_id)
    awaiting_payment.discard(user_id)

def resumen_pedido(user_id):
    pedido = orders.get(user_id, [])
    if not pedido:
        return "🛒 *Tu pedido está vacío*"

    total = 0
    texto = "🧾 *Resumen de tu pedido*\n\n"

    for i, p in enumerate(pedido, 1):
        subtotal = p["cantidad"] * p["precio"]
        total += subtotal
        texto += f"{i}. {p['cantidad']} x {p['nombre']} — ${subtotal}\n"

    texto += f"\n💰 *Total:* ${total}\n\n"
    texto += "👉 Escribe *confirmar*\n"
    texto += "👉 O *quitar 1* / *quitar arroz diana*\n"
    texto += "👉 O *borrar* para empezar de nuevo"

    return texto

@app.route("/chat", methods=["POST"])
def chat():
    msg = MessagingResponse()
    text = request.form.get("Body", "").strip().lower()
    user_id = request.form.get("From")

    # 🔴 BORRAR CONVERSACIÓN
    if text in ["borrar", "cancelar", "reiniciar"]:
        limpiar_usuario(user_id)
        msg.message("🧹 Conversación borrada.\n\n" + saludo())
        return str(msg)

    # saludo inicial
    if user_id not in orders:
        orders[user_id] = []
        msg.message(saludo())
        return str(msg)

    # 📍 dirección
    if user_id in awaiting_address:
        orders[user_id].append({"direccion": text})
        awaiting_address.remove(user_id)
        awaiting_payment.add(user_id)
        msg.message(
            "💳 *Método de pago*\n\n"
            "1️⃣ Transferencia\n"
            "2️⃣ Efectivo"
        )
        return str(msg)

    # 💳 pago
    if user_id in awaiting_payment:
        awaiting_payment.remove(user_id)
        msg.message(
            "✅ *Pedido recibido*\n\n"
            "📦 El negocio fue notificado\n"
            "🙏 Gracias por tu compra"
        )
        limpiar_usuario(user_id)
        return str(msg)

    # 🛑 quitar producto
    if text.startswith("quitar"):
        pedido = orders.get(user_id, [])
        eliminado = False

        # quitar por número
        m = re.search(r"quitar\s+(\d+)", text)
        if m:
            idx = int(m.group(1)) - 1
            if 0 <= idx < len(pedido):
                pedido.pop(idx)
                eliminado = True

        else:
            # quitar por nombre
            for p in pedido[:]:
                if p["nombre"].lower() in text:
                    p["cantidad"] -= 1
                    if p["cantidad"] <= 0:
                        pedido.remove(p)
                    eliminado = True
                    break

        if not eliminado:
            msg.message("⚠️ No encontré ese producto para quitar")
        else:
            msg.message(resumen_pedido(user_id))
        return str(msg)

    # ✅ confirmar
    if text == "confirmar":
        awaiting_confirmation.discard(user_id)
        awaiting_address.add(user_id)
        msg.message("📍 Por favor escribe la *dirección de entrega*")
        return str(msg)

    # 🛒 finalizar compra
    if text == "ok":
        msg.message(resumen_pedido(user_id))
        return str(msg)

    # 🔍 buscar producto
    resultados = buscar(text)
    if resultados:
        pending_product[user_id] = resultados
        msg.message(lista_productos(resultados))
        return str(msg)

    # 🧮 seleccionar producto
    if text.isdigit() and user_id in pending_product:
        idx = int(text) - 1
        productos = pending_product[user_id]
        if 0 <= idx < len(productos):
            producto = productos[idx]
            pending_product[user_id] = producto
            msg.message(f"¿Cuántas unidades de *{producto['nombre']}* deseas?")
            return str(msg)

    # 📦 cantidad
    if text.isdigit() and isinstance(pending_product.get(user_id), dict):
        producto = pending_product[user_id]
        orders[user_id].append({
            "nombre": producto["nombre"],
            "precio": producto["precio"],
            "cantidad": int(text)
        })
        pending_product.pop(user_id)
        msg.message(
            "✅ Producto agregado\n\n"
            "👉 Escribe otro producto\n"
            "👉 O escribe *ok* para finalizar"
        )
        return str(msg)

    msg.message("❓ No entendí, escribe el nombre del producto")
    return str(msg)
