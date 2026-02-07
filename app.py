from flask import Flask, request
import re
import requests

from businesses import BUSINESSES
from responses import saludo, lista_productos

app = Flask(__name__)
app.secret_key = "chat-dev-secret"

# =========================
# 🔐 WHATSAPP CLOUD API
# =========================
VERIFY_TOKEN = "julia0111"
WHATSAPP_TOKEN = "EAAKqZBJod3WQBQgoarPZCKe45bPv3QJE8uytcgvIc2MtarhsES3OF2WzqwzUQKWZCoqGb8s0BnGMLsYw6gAwXBCy77wZCVjqmE1YRzKQqVA0p5QMZCHvBsSZC1ykWOKTdkhdBOHW4hTOq8GAZBsZAwKGdHMpP3p7jdQlhs0VN3IpaZAQQrSZAZCThqReng1AU90dsXk1eZBhYh2aZBnycQ8UjfZAMC8rkzDPwsa0pVCDwPBpcmKs417jVHKLtrZBVqZBOmC2ZAGCQrHqbPYeaMC9yNerWM3kULIeU"
PHONE_NUMBER_ID = "1020609241124975"

# =========================
# 🧠 MEMORIA
# =========================
orders = {}
last_results = {}
pending_product = {}
awaiting_confirmation = set()
awaiting_comments = set()
order_comments = {}
user_business = {}

QUITAR_PALABRAS = ["quitar", "eliminar", "borra", "sacar"]

CANTIDADES_LB = {
    "media libra": 0.5,
    "una libra": 1,
    "libra y media": 1.5,
    "dos libras": 2,
}

# =========================
# 📤 ENVÍO AL NEGOCIO
# =========================
def send_order_to_business(phone, resumen):
    enviar_whatsapp(phone, resumen)

# =========================
# 📦 RESUMEN NEGOCIO
# =========================
def resumen_para_negocio(user):
    pedido = orders.get(user, [])
    if not pedido:
        return None

    texto = "🛒 *NUEVO PEDIDO*\n\n"
    total = 0

    for p in pedido:
        texto += f"- {p['cantidad']} {p['tipo']} = ${int(p['subtotal'])}\n"
        total += p["subtotal"]

    if user in order_comments:
        texto += f"\n📝 {order_comments[user]}"

    texto += f"\n\n💰 TOTAL: ${int(total)}"
    return texto

# =========================
# 🔢 CANTIDAD
# =========================
def extraer_cantidad(text):
    text = text.lower()

    for k, v in CANTIDADES_LB.items():
        if k in text:
            return v

    m = re.search(r"(\d+(?:[.,]\d+)?)", text)
    if m:
        return float(m.group(1).replace(",", "."))

    return 1

# =========================
# 🧠 BOT
# =========================
def process_message(text, user):
    text = text.strip()
    text_lower = text.lower()

    # 1️⃣ SELECCIÓN DE NEGOCIO
    if user not in user_business:
        if text.isdigit() and text in BUSINESSES:
            user_business[user] = text
            negocio = BUSINESSES[text]

            if negocio["type"] == "restaurant":
                last_results[user] = negocio["menu"]
                return (
                    f"🍽️ *{negocio['name']}*\n\n"
                    "📋 *Menú:*\n\n"
                    + lista_productos(negocio["menu"])
                    + "\nResponde con el número del plato"
                )

            return (
                f"🛒 *{negocio['name']}*\n\n"
                "Escribe el producto que te interesa.\n"
                "Ej: arroz, tomate, papa"
            )

        opciones = "🏪 *Elige un negocio:*\n\n"
        for k, b in BUSINESSES.items():
            opciones += f"{k}. {b['name']}\n"
        opciones += "\nResponde con el número"
        return opciones

    negocio = BUSINESSES[user_business[user]]
    items = negocio["inventory"] if negocio["type"] == "store" else negocio["menu"]

    # ➖ QUITAR PRODUCTOS
    if any(p in text_lower for p in QUITAR_PALABRAS):
        pedido = orders.get(user, [])
        cant = extraer_cantidad(text_lower)

        for p in pedido:
            if p["tipo"] in text_lower:
                p["cantidad"] -= cant
                if p["cantidad"] <= 0:
                    pedido.remove(p)
                else:
                    p["subtotal"] = p["cantidad"] * p["precio"]

                resumen = resumen_para_negocio(user)
                if resumen:
                    send_order_to_business(negocio["phone"], resumen)

                return resumen_pedido(user)

        return "❌ Ese producto no está en tu pedido"

    # 📝 COMENTARIOS
    if user in awaiting_comments:
        order_comments[user] = text
        awaiting_comments.discard(user)

        resumen = resumen_para_negocio(user)
        send_order_to_business(negocio["phone"], resumen)

        orders.pop(user, None)
        user_business.pop(user, None)

        return "✅ Pedido enviado al negocio 🙌"

    # 📦 AGREGAR PRODUCTO
    if user in pending_product:
        producto = pending_product[user]
        cantidad = extraer_cantidad(text)

        producto["cantidad"] = cantidad
        producto["subtotal"] = cantidad * producto["precio"]

        orders.setdefault(user, []).append(producto)
        pending_product.pop(user)

        return "✅ Producto agregado\n👉 Otro producto o *ok*"

    if text_lower == "ok":
        return resumen_pedido(user)

    if text_lower == "confirmar":
        awaiting_comments.add(user)
        return "📝 ¿Deseas agregar un comentario?"

    # 🔍 BUSCAR / SELECCIONAR
    if text.isdigit() and user in last_results:
        idx = int(text) - 1
        if 0 <= idx < len(last_results[user]):
            pending_product[user] = last_results[user][idx].copy()
            return "¿Cuántas unidades deseas?"

    # 🔍 BUSCAR SOLO PARA TIENDAS
    if negocio["type"] == "store":
    resultados = [i for i in items if text_lower in i["tipo"]]

    if resultados:
        last_results[user] = resultados
        return lista_productos(resultados)

    return "❌ No encontramos ese producto"

# 🍽️ RESTAURANTE: NO BUSCA TEXTO
return "❌ Responde con el número del plato"

# =========================
# 📋 RESUMEN USUARIO
# =========================
def resumen_pedido(user):
    pedido = orders.get(user, [])
    if not pedido:
        return "🛒 Pedido vacío"

    total = 0
    texto = "🧾 *Tu pedido:*\n\n"

    for p in pedido:
        texto += f"- {p['cantidad']} {p['tipo']} = ${int(p['subtotal'])}\n"
        total += p["subtotal"]

    texto += f"\n💰 Total: ${int(total)}\n\n👉 confirmar"
    return texto

# =========================
# 🌐 WEBHOOK
# =========================
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Forbidden", 403

    data = request.json
    msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
    user = msg["from"]
    text = msg.get("text", {}).get("body", "")

    respuesta = process_message(text, user)
    enviar_whatsapp(user, respuesta)

    return "OK"

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
    app.run(port=5000)

