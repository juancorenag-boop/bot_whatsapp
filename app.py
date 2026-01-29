from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

from inventory import INVENTARIO
from search import buscar
from responses import saludo, lista_productos

app = Flask(__name__)

# memoria simple
orders = {}

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    body = request.form.get("Body", "").strip().lower()
    from_number = request.form.get("From")

    resp = MessagingResponse()

    # ===== INICIO =====
    if body in ["hola", "menu", "inicio"]:
        orders[from_number] = {
            "step": "buscar",
            "cart": [],
            "total": 0,
            "resultados": []
        }
        resp.message(saludo())
        return str(resp)

    # inicializar sesión si no existe
    if from_number not in orders:
        orders[from_number] = {
            "step": "buscar",
            "cart": [],
            "total": 0,
            "resultados": []
        }

    order = orders[from_number]

    # ===== PASO 1: BUSCAR PRODUCTOS =====
    if order["step"] == "buscar":
        resultados = buscar(body, INVENTARIO)

        if not resultados:
            resp.message("❌ No encontré productos con eso. Intenta otra palabra.")
            return str(resp)

        order["resultados"] = resultados
        order["step"] = "seleccionar"

        resp.message(
            lista_productos(resultados) +
            "\n✍️ Escribe el *nombre exacto* del producto que deseas."
        )
        return str(resp)

    # ===== PASO 2: SELECCIONAR PRODUCTO =====
    if order["step"] == "seleccionar":
        for p in order["resultados"]:
            if p["nombre"].lower() == body:
                order["cart"].append(p)
                order["total"] += p["precio"]
                order["step"] = "mas"

                resp.message(
                    f"✅ *{p['nombre']}* agregado.\n"
                    f"💰 Total actual: ${order['total']}\n\n"
                    "¿Necesitas algo más?\n"
                    "✍️ Escribe qué necesitas (ej: leche)\n"
                    "✔️ O escribe *ok* para continuar"
                )
                return str(resp)

        resp.message("❌ No reconocí ese producto. Escríbelo exactamente como aparece.")
        return str(resp)

    # ===== PASO 3: ¿ALGO MÁS? =====
    if order["step"] == "mas":
        if body == "ok":
            resumen = "🧾 *Resumen de tu pedido:*\n\n"
            for p in order["cart"]:
                resumen += f"- {p['nombre']} ${p['precio']}\n"
            resumen += f"\n💰 Total: ${order['total']}\n\n"
            resumen += "¿Confirmas el pedido? (sí / no)"

            order["step"] = "confirmar"
            resp.message(resumen)
            return str(resp)

        # si escribe otra cosa, vuelve a buscar
        resultados = buscar(body, INVENTARIO)

        if not resultados:
            resp.message("❌ No encontré productos con eso.")
            return str(resp)

        order["resultados"] = resultados
        order["step"] = "seleccionar"

        resp.message(
            lista_productos(resultados) +
            "\n✍️ Escribe el *nombre exacto* del producto."
        )
        return str(resp)

    # ===== PASO 4: CONFIRMAR =====
    if order["step"] == "confirmar":
        if body in ["si", "sí", "confirmo"]:
            order["step"] = "direccion"
            resp.message("📍 Perfecto. Escríbeme la dirección de entrega:")
            return str(resp)

        resp.message("❌ Pedido cancelado. Escribe *hola* para empezar de nuevo.")
        orders.pop(from_number)
        return str(resp)

    # ===== PASO 5: DIRECCIÓN =====
    if order["step"] == "direccion":
        direccion = body

        resp.message(
            "🎉 *Pedido confirmado*\n\n"
            f"📍 Dirección: {direccion}\n"
            f"💰 Total: ${order['total']}\n\n"
            "¡Gracias por tu compra!"
        )

        orders.pop(from_number)
        return str(resp)

    return str(resp)

@app.route("/")
def home():
    return "Bot de tienda funcionando 🚀"
