from flask import Flask, request, session, render_template_string
import re

from search import buscar
from responses import saludo, lista_productos

app = Flask(__name__)
app.secret_key = "chat-dev-secret"

# ===== MEMORIA DEL BOT =====
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

# =====================================================
# 🧠 LÓGICA CENTRAL DEL BOT (WHATSAPP / CHAT / FUTURO)
# =====================================================
def process_message(text, user):
    text_lower = text.lower().strip()

    # ---- SALUDO ----
    if text_lower in ["hola", "buenas", "hello", "menu", "inicio"]:
        return saludo()

    # ---- CAMBIO ----
    if user in awaiting_change:
        awaiting_change.discard(user)
        orders.pop(user, None)
        return (
            "✅ Pedido registrado correctamente 🙌\n"
            "En breve te contactamos para la entrega 🚚"
        )

    # ---- MÉTODO DE PAGO ----
    if user in awaiting_payment:
        if text_lower in ["transferencia", "1"]:
            awaiting_payment.discard(user)
            orders.pop(user, None)
            return BANK_INFO

        if text_lower in ["efectivo", "2"]:
            awaiting_payment.discard(user)
            awaiting_change.add(user)
            return "💵 ¿Necesitas cambio?\nEj: tengo 50.000 o escribe *exacto*"

        return "❌ Opción inválida. Escribe *transferencia* o *efectivo*."

    # ---- DIRECCIÓN ----
    if user in awaiting_address:
        awaiting_address.discard(user)
        awaiting_payment.add(user)
        return (
            "💳 ¿Cuál será tu método de pago?\n"
            "1️⃣ Transferencia\n"
            "2️⃣ Efectivo"
        )

    # ---- CONFIRMAR ----
    if text_lower == "confirmar" and user in awaiting_confirmation:
        awaiting_confirmation.discard(user)
        awaiting_address.add(user)
        return "📍 Por favor escribe la dirección de entrega"

    # ---- QUITAR ----
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

        return resumen_pedido(user)

    # ---- MOSTRAR RESUMEN ----
    if text_lower == "ok":
        awaiting_confirmation.add(user)
        return resumen_pedido(user)

    # ---- CANTIDAD ----
    if user in pending_product and text.isdigit():
        producto = pending_product.pop(user)
        producto["cantidad"] = int(text)
        orders.setdefault(user, []).append(producto)
        return (
            "✅ Producto agregado.\n\n"
            "¿Deseas agregar algo más?\n"
            "👉 Escribe el producto\n"
            "👉 O escribe *ok* para finalizar"
        )

    # ---- SELECCIÓN ----
    if text.isdigit() and user in last_results:
        idx = int(text) - 1
        productos = last_results[user]
        if idx < 0 or idx >= len(productos):
            return "❌ Opción inválida"
        pending_product[user] = productos[idx].copy()
        return (
            f"¿Cuántas unidades de "
            f"{productos[idx]['tipo'].title()} {productos[idx]['marca'].title()} deseas?"
        )

    # ---- BÚSQUEDA ----
    resultados = buscar(text_lower)
    if resultados:
        last_results[user] = resultados
        return lista_productos(resultados)

    return "❌ No encontré productos con ese nombre."


def resumen_pedido(user):
    pedido = orders.get(user, [])
    if not pedido:
        return "🛒 Tu pedido está vacío"

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
    return resumen


# ===========================
# 💬 CHAT WEB DE PRUEBAS
# ===========================
CHAT_HTML = """
<!doctype html>
<html>
<head>
  <title>Chat de Pruebas</title>
  <style>
    body { font-family: Arial; background:#f4f4f4; }
    .chat { max-width:600px; margin:40px auto; background:#fff; padding:20px; }
    .msg { margin:10px 0; }
    .user { font-weight:bold; }
    input { width:80%; padding:8px; }
    button { padding:8px; }
  </style>
</head>
<body>
  <div class="chat">
    {% for m in messages %}
      <div class="msg"><span class="user">{{ m.sender }}:</span> {{ m.text }}</div>
    {% endfor %}
    <form method="post">
      <input name="message" autofocus required>
      <button>Enviar</button>
    </form>
  </div>
</body>
</html>
"""

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "messages" not in session:
        session["messages"] = []

    if request.method == "POST":
        text = request.form["message"]
        user = "web-user"

        session["messages"].append({"sender": "Tú", "text": text})
        reply = process_message(text, user)
        session["messages"].append({"sender": "Bot", "text": reply})
        session.modified = True

    return render_template_string(CHAT_HTML, messages=session["messages"])


@app.route("/")
def home():
    return "Bot funcionando 🚀 — entra a /chat"

