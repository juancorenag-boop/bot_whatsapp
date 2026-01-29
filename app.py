from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

from inventory import INVENTARIO
from search import buscar
from responses import saludo, lista_productos

app = Flask(__name__)

# ================= MEMORIA SIMPLE =================
orders = {}

# ================= WEBHOOK =================
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    from_number = request.form.get("From")
    body = request.form.get("Body", "").strip().lower()

    resp = MessagingResponse()

    # Inicializar pedido si no existe
    if from_number not in orders:
        orders[from_number] = {
            "step": "inicio",
            "cart": [],
            "total": 0,
            "producto_actual": None,
            "resultados": []
        }

    order = orders[from_number]

    # ===== SALUDO / INICIO =====
    if body in ["hola", "menu", "inicio"]:
        order["step"] = "busqueda"
        resp.message(saludo())
        return str(resp)

    # ===== FINALIZAR PEDIDO =====
    if body in ["terminar", "finalizar", "checkout"]:
        if not order["cart"]:
            resp.message("❌ Tu carrito está vacío. Agrega productos antes de finalizar.")
            return str(resp)

        resumen = "🧾 *Resumen de tu pedido:*\n\n"
        for p in order["cart"]:
            resumen += f"- {p['nombre']} x{p['cantidad']} = ${p['subtotal']}\n"

        resumen += f"\n💰 *Total:* ${order['total']}"
        if "direccion" in order:
            resumen += f"\n📍 *Dirección:* {order['direccion']}"
        resumen += "\n\n✅ *Pedido confirmado*. ¡Gracias por tu compra! 🎉"

        resp.message(resumen)
        orders.pop(from_number)
        return str(resp)

    # ===== BÚSQUEDA DE PRODUCTOS =====
    if order["step"] in ["inicio", "busqueda"]:
        productos = buscar(body, INVENTARIO)
        if not productos:
            resp.message("❌ No encontré ese producto. Intenta con otro nombre.")
            return str(resp)

        order["resultados"] = productos
        order["step"] = "confirmar_producto"
        resp.message(lista_productos(productos) + "\n\n✍️ Escribe el *nombre exacto* del producto que deseas.")
        return str(resp)

    # ===== CONFIRMAR PRODUCTO =====
    if order["step"] == "confirmar_producto":
        for p in order["resultados"]:
            if body == p["nombre"].lower():
                order["producto_actual"] = p
                order["step"] = "cantidad"
                resp.message(f"🛒 ¿Cuántas unidades de *{p['nombre']}* deseas?")
                return str(resp)

        resp.message("❌ No reconocí ese producto. Escríbelo exactamente como aparece en la lista.")
        return str(resp)

    # ===== CANTIDAD =====
    if order["step"] == "cantidad":
        if not body.isdigit() or int(body) <= 0:
            resp.message("❗ Escribe una cantidad válida (número).")
            return str(resp)

        cantidad = int(body)
        producto = order["producto_actual"]

        if cantidad > producto["cantidad"]:
            resp.message(f"⚠️ Solo hay {producto['cantidad']} unidades disponibles.")
            return str(resp)

        subtotal = cantidad * producto["precio"]

        # Verificar si el producto ya está en el carrito
        for item in order["cart"]:
            if item["nombre"] == producto["nombre"]:
                item["cantidad"] += cantidad
                item["subtotal"] += subtotal
                break
        else:
            order["cart"].append({
                "nombre": producto["nombre"],
                "cantidad": cantidad,
                "precio": producto["precio"],
                "subtotal": subtotal
            })

        order["total"] += subtotal
        order["step"] = "mas"
        resp.message(
            f"✅ *{producto['nombre']}* agregado ({cantidad} uds)\n"
            f"💵 Subtotal: ${subtotal}\n\n"
            "¿Deseas agregar otro producto? Escribe *sí* para continuar o *terminar* para finalizar tu pedido."
        )
        return str(resp)

    # ===== AGREGAR MÁS PRODUCTOS =====
    if order["step"] == "mas":
        if body in ["si", "sí"]:
            order["step"] = "busqueda"
            resp.message("🛍️ Perfecto, escribe el producto que deseas buscar.")
            return str(resp)

        if body in ["no", "terminar", "finalizar"]:
            order["step"] = "direccion"
            resp.message("📍 Por favor escribe la *dirección de entrega*:")  
            return str(resp)

        resp.message("❓ Responde *sí* para agregar más productos o *terminar* para finalizar tu pedido.")
        return str(resp)

    # ===== DIRECCIÓN =====
    if order["step"] == "direccion":
        order["direccion"] = body
        resumen = "🧾 *Resumen de tu pedido:*\n\n"
        for p in order["cart"]:
            resumen += f"- {p['nombre']} x{p['cantidad']} = ${p['subtotal']}\n"
        resumen += f"\n💰 *Total:* ${order['total']}"
        resumen += f"\n📍 *Dirección:* {order['direccion']}"
        resumen += "\n\n✅ *Pedido confirmado*. ¡Gracias por tu compra! 🎉"

        resp.message(resumen)
        orders.pop(from_number)
        return str(resp)

    # ===== CASO POR DEFECTO =====
    resp.message("❓ No entendí tu mensaje. Escribe *hola* para comenzar o *terminar* para finalizar tu pedido.")
    return str(resp)


# ================= HOME =================
@app.route("/")
def home():
    return "Bot de tienda funcionando 🚀"
