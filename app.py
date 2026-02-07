from flask import Flask, request, render_template_string, session
import re
import requests

from inventory import INVENTARIO
from search import buscar
from responses import saludo, lista_productos

app = Flask(__name__)
app.secret_key = "chat-dev-secret"

# =========================
# 🔐 WHATSAPP CLOUD API
# =========================
VERIFY_TOKEN = "julia0111"
WHATSAPP_TOKEN = "EAAKqZBJod3WQBQltZANeJKNH6HHUA4ZCENq2nPJ30aClT7ZCu6W2eqBSnLvau2btce9NdMMI9gCefbLPVIAixchdluMH2J95RykUgtTXVZAP9QxaWZBYZA2IVYpqZCR0RAhHsEG39HZCzDrXSln4Tg3m4ml6cYuSRZBf30SsgoERmfRkQvLjmxRxv1Jszr1DyynZB0AdQnFNwQg5dZA7trZBVlWqmqzlBrpZCuZAiCSakXjNS1BuIw5XTzuqyoUKiVWjnopE69fxjrM69taYd4bsn2LQrZBR8pZBu"
PHONE_NUMBER_ID = "1020609241124975"

BUSINESS_PHONE = "+573216642926"

# =========================
# ===== MEMORIA =====
# =========================
orders = {}
last_results = {}
pending_product = {}
awaiting_confirmation = set()
awaiting_address = set()
awaiting_payment = set()
awaiting_change = set()
awaiting_comments = set()
awaiting_change_amount = set()
order_comments = {}

# ➕ NUEVO: palabras para quitar productos
QUITAR_PALABRAS = ["quitar", "eliminar", "borra", "sacar"]

# ➕ NUEVO: cantidades en libras
CANTIDADES_LB = {
    "media libra": 0.5,
    "media lb": 0.5,
    "una libra": 1,
    "1 libra": 1,
    "1 lb": 1,
    "libra y media": 1.5,
    "1.5 lb": 1.5,
    "dos libras": 2,
    "2 libras": 2,
    "2 lb": 2
}

BANK_INFO = (
    "🏦 *Datos para transferencia:*\n\n"
    "Banco: Bancolombia\n"
    "Cuenta: 123456789\n"
    "Tipo: Ahorros\n"
    "Nombre: Tienda XYZ\n\n"
    "Cuando realices el pago envía el comprobante 📸"
)

PROMO_MSG = (
    "\n\n📣 *¿Te gustaría este sistema para tu negocio?*\n"
    "Ahorra tiempo y evita confusiones entre pedidos.\n"
    "📞 Contáctanos: +57 3216642926"
)

# =========================
# 📤 ENVÍO SIMULADO NEGOCIO
# =========================
def send_order_to_business(phone, resumen):
    print("\n==============================")
    print("📦 NUEVO PEDIDO PARA EL NEGOCIO")
    print(f"📞 Enviar a: {phone}")
    print(resumen)
    print("==============================\n")

# =========================
# 📦 RESUMEN
# =========================
def resumen_para_negocio(user):
    pedido = orders.get(user, [])
    if not pedido:
        return None

    texto = "🛒 NUEVO PEDIDO\n\n"
    total = 0

    for p in pedido:
        subtotal = p.get("subtotal", 0)
        texto += f"- {p['cantidad']} {p['tipo'].title()} = ${int(subtotal)}\n"
        total += subtotal

    if user in order_comments:
        texto += f"\n📝 Comentarios:\n{order_comments[user]}"

    texto += f"\n\n💰 TOTAL: ${int(total)}"
    return texto

def extraer_cantidad(text):
    text = text.lower()
    palabras = {
        "media": 0.5,
        "media libra": 0.5,
        "una": 1,
        "un": 1,
        "uno": 1,
        "dos": 2,
        "tres": 3,
        "cuatro": 4,
        "cinco": 5
    }

    for k, v in palabras.items():
        if k in text:
            return v, None

    m = re.search(r"(\d+(?:[.,]\d+)?)", text)
    if m:
        return float(m.group(1).replace(",", ".")), None

    return 1, None

# =========================
# 🧠 LÓGICA DEL BOT
# =========================
def process_message(text, user):
    text_lower = text.lower().strip()

    if not text_lower or text_lower in ["hola", "buenas", "menu", "inicio"]:
        return saludo()

    # ➖ QUITAR PRODUCTOS
    if any(p in text_lower for p in QUITAR_PALABRAS):
        pedido = orders.get(user, [])
        if not pedido:
            return "🛒 Tu pedido está vacío."

        cant_quitar, _ = extraer_cantidad(text_lower)

        for p in pedido:
            if p["tipo"].lower() in text_lower:
                p["cantidad"] -= cant_quitar

                if p["cantidad"] <= 0:
                    pedido.remove(p)
                    msg = f"🗑️ Quité completamente *{p['tipo']}* del pedido."
                else:
                    p["subtotal"] = p["cantidad"] * p.get("precio", 0)
                    msg = f"➖ Quité *{cant_quitar}* de *{p['tipo']}*."

                resumen = resumen_para_negocio(user)
                if resumen:
                    send_order_to_business(BUSINESS_PHONE, resumen)

                return msg + "\n\n" + resumen_pedido(user)

        return "❌ Ese producto no está en tu pedido."

    # 📝 COMENTARIOS → PEDIDO FINAL
    if user in awaiting_comments:
        order_comments[user] = text
        awaiting_comments.discard(user)

        resumen = resumen_para_negocio(user)
        if resumen:
            send_order_to_business(BUSINESS_PHONE, resumen)

        orders.pop(user, None)
        return "✅ Pedido registrado correctamente 🙌" + PROMO_MSG

    if user in awaiting_change:
        awaiting_change.discard(user)
        awaiting_change_amount.add(user)
        return "💵 ¿Para cuánto es el billete? (ej: 20000, 50000)"

    if user in awaiting_change_amount:
        awaiting_change_amount.discard(user)
        order_comments[user] = f"Cambio para ${text}"
        awaiting_comments.add(user)
        return "📝 ¿Deseas agregar algún comentario a tu pedido?"

    if user in awaiting_payment:
        if text_lower in ["transferencia", "1"]:
            awaiting_payment.discard(user)
            awaiting_comments.add(user)
            return BANK_INFO + "\n\n📝 ¿Deseas agregar algún comentario?"
        if text_lower in ["efectivo", "2"]:
            awaiting_payment.discard(user)
            awaiting_change.add(user)
            return "💵 ¿Necesitas cambio?"
        return "❌ Opción inválida."

    if user in awaiting_address:
        awaiting_address.discard(user)
        awaiting_payment.add(user)
        return "💳 Método de pago:\n1️⃣ Transferencia\n2️⃣ Efectivo"

    if text_lower == "confirmar" and user in awaiting_confirmation:
        awaiting_confirmation.discard(user)
        awaiting_address.add(user)
        return "📍 Escribe la dirección de entrega"

    if text_lower == "ok":
        awaiting_confirmation.add(user)
        return resumen_pedido(user)

    if user in pending_product:
        producto = pending_product[user]
        cantidad = None

        for k, v in CANTIDADES_LB.items():
            if k in text_lower:
                cantidad = v
                break

        if cantidad is not None:
            producto["cantidad"] = cantidad
        elif text.isdigit():
            producto["cantidad"] = int(text)
        else:
            return "❌ Cantidad inválida."

        producto["subtotal"] = producto["cantidad"] * producto.get("precio", 0)
        orders.setdefault(user, []).append(producto)
        pending_product.pop(user)
        return "✅ Producto agregado.\n👉 Otro producto o *ok*"

    if text.isdigit() and user in last_results:
        idx = int(text) - 1
        productos = last_results[user]
        if 0 <= idx < len(productos):
            pending_product[user] = productos[idx].copy()
            return "¿Cuántas unidades deseas?"

    resultados = buscar(text_lower)
    if resultados:
        last_results[user] = resultados
        return lista_productos(resultados)

    return "❌ No encontramos ese producto."

def resumen_pedido(user):
    pedido = orders.get(user, [])
    if not pedido:
        return "🛒 Tu pedido está vacío"

    resumen = "🧾 *Resumen de tu pedido:*\n\n"
    total = 0

    for i, p in enumerate(pedido, 1):
        subtotal = p.get("subtotal", 0)
        resumen += f"{i}. {p['cantidad']} {p['tipo'].title()} — ${int(subtotal)}\n"
        total += subtotal

    resumen += f"\n💰 Total: ${int(total)}\n\n👉 confirmar"
    return resumen

# =========================
# 🌐 WEB CHAT
# =========================
@app.route("/", methods=["GET"])
def home():
    return "Bot activo 🚀"

@app.route("/chat", methods=["POST"])
def chat():
    user = request.form.get("From", "web_user")
    text = request.form.get("Body", "")
    return process_message(text, user)

# =========================
# 📲 WHATSAPP WEBHOOK
# =========================
@app.route("/webhook", methods=["GET", "POST"])
def whatsapp_webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Forbidden", 403

    data = request.json
    try:
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
        user = msg["from"]
        text = msg.get("text", {}).get("body", "")

        respuesta = process_message(text or "Hola", user)
        enviar_whatsapp(user, respuesta)

    except Exception as e:
        print("ERROR:", e)

    return "OK", 200

def enviar_whatsapp(to, text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

