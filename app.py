from flask import Flask, request, session
import re

from search import buscar
from responses import saludo, lista_productos

app = Flask(__name__)
app.secret_key = "chat-dev-secret"

BUSINESS_PHONE = "+573216642926"

# ===== MEMORIA =====
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

# =========================
# 📤 ENVÍO SIMULADO
# =========================
def send_order_to_business(phone, resumen):
    print("\n==============================")
    print("📦 NUEVO PEDIDO PARA EL NEGOCIO")
    print(f"📞 Enviar a: {phone}")
    print(resumen)
    print("==============================\n")

def resumen_para_negocio(user):
    pedido = orders.get(user, [])
    if not pedido:
        return None

    texto = "🛒 NUEVO PEDIDO\n\n"
    total = 0

    for p in pedido:
        if p.get("unidad") == "libra":
            subtotal = p["subtotal"]
            texto += f"- {p['cantidad']} lb {p['tipo'].title()} = ${int(subtotal)}\n"
        else:
            subtotal = p["precio"] * p["cantidad"]
            texto += f"- {p['cantidad']} x {p['tipo'].title()} {p['marca'].title()} = ${subtotal}\n"
        total += subtotal

    texto += f"\n💰 TOTAL: ${int(total)}"
    return texto

# =========================
# 🧠 LÓGICA DEL BOT
# =========================
def process_message(text, user):
    text_lower = text.lower().strip()

    # ---- SALUDO ----
    if text_lower in ["hola", "buenas", "hello", "menu", "inicio"]:
        return saludo()

    # ---- CAMBIO ----
    if user in awaiting_change:
        resumen = resumen_para_negocio(user)
        if resumen:
            send_order_to_business(BUSINESS_PHONE, resumen)

        awaiting_change.discard(user)
        orders.pop(user, None)
        return "✅ Pedido registrado correctamente 🙌"

    # ---- MÉTODO DE PAGO ----
    if user in awaiting_payment:
        if text_lower in ["transferencia", "1"]:
            resumen = resumen_para_negocio(user)
            if resumen:
                send_order_to_business(BUSINESS_PHONE, resumen)

            awaiting_payment.discard(user)
            orders.pop(user, None)
            return BANK_INFO

        if text_lower in ["efectivo", "2"]:
            awaiting_payment.discard(user)
            awaiting_change.add(user)
            return "💵 ¿Necesitas cambio?\nEj: tengo 50.000 o escribe *exacto*"

        return "❌ Opción inválida."

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

    # ---- QUITAR PRODUCTO ----
    match_quitar = re.match(r"quitar\s+([\d\.]+)\s+de\s+(.+)", text_lower)
    if match_quitar and user in awaiting_confirmation:
        cantidad = float(match_quitar.group(1))
        producto_txt = match_quitar.group(2)

        pedido = orders.get(user, [])
        for p in pedido:
            nombre = f"{p['tipo']} {p['marca']}".lower()
            if producto_txt in nombre:
                if p["cantidad"] > cantidad:
                    p["cantidad"] -= cantidad
                    if p.get("unidad") == "libra":
                        p["subtotal"] = p["cantidad"] * p["precio"]
                else:
                    pedido.remove(p)
                break

        return resumen_pedido(user)

    # ---- MOSTRAR RESUMEN ----
    if text_lower == "ok":
        awaiting_confirmation.add(user)
        return resumen_pedido(user)

    # ---- CANTIDAD ----
    if user in pending_product:
        producto = pending_product[user]

        if producto.get("unidad") == "libra":
            try:
                libras = float(text.replace(",", "."))
                if libras <= 0:
                    raise ValueError
            except ValueError:
                return (
                    "❌ Escribe una cantidad válida.\n"
                    "0.5 (media libra)\n"
                    "1 (una libra)\n"
                    "1.5 (libra y media)\n"
                    "2 (dos libras)"
                )

            producto["cantidad"] = libras
            producto["subtotal"] = libras * producto["precio"]
            orders.setdefault(user, []).append(producto)
            pending_product.pop(user)

            return (
                f"✅ {libras} lb de {producto['tipo'].title()} agregado\n"
                f"💰 Subtotal: ${int(producto['subtotal'])}\n\n"
                "👉 Escribe otro producto\n"
                "👉 O escribe *ok* para finalizar"
            )

        if text.isdigit():
            producto["cantidad"] = int(text)
            orders.setdefault(user, []).append(producto)
            pending_product.pop(user)
            return (
                "✅ Producto agregado.\n\n"
                "👉 Escribe otro producto\n"
                "👉 O escribe *ok* para finalizar"
            )

        return "❌ Escribe un número válido."

    # ---- SELECCIÓN ----
    if text.isdigit() and user in last_results:
        idx = int(text) - 1
        productos = last_results[user]
        if 0 <= idx < len(productos):
            prod = productos[idx]
            pending_product[user] = prod.copy()

            if prod.get("unidad") == "libra":
                return (
                    f"💰 Precio: ${prod['precio']} por libra\n\n"
                    "¿Cuántas libras necesitas?\n"
                    "0.5 (media libra)\n"
                    "1 (una libra)\n"
                    "1.5 (libra y media)\n"
                    "2 (dos libras)"
                )

            return f"¿Cuántas unidades de {prod['tipo'].title()} {prod['marca'].title()} deseas?"

    # ---- BÚSQUEDA ----
    resultados = buscar(text_lower)
    if resultados:
        last_results[user] = resultados
        return lista_productos(resultados)

    return "❌ No entendí tu mensaje."

def resumen_pedido(user):
    pedido = orders.get(user, [])
    if not pedido:
        return "🛒 Tu pedido está vacío"

    resumen = "🧾 *Resumen de tu pedido:*\n\n"
    total = 0

    for i, p in enumerate(pedido, start=1):
        if p.get("unidad") == "libra":
            resumen += f"{i}. {p['cantidad']} lb {p['tipo'].title()} — ${int(p['subtotal'])}\n"
            total += p["subtotal"]
        else:
            subtotal = p["precio"] * p["cantidad"]
            resumen += f"{i}. {p['cantidad']} x {p['tipo'].title()} {p['marca'].title()} — ${subtotal}\n"
            total += subtotal

    resumen += f"\n💰 *Total:* ${int(total)}\n\n"
    resumen += "👉 confirmar\n👉 quitar 0.5 de tomate"
    return resumen

# =========================
# 🌐 RUTAS
# =========================
@app.route("/", methods=["GET"])
def home():
    return "Bot activo 🚀"

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if request.method == "POST":
        # mensaje real del usuario
        user = request.form.get("From", "web_user")
        text = request.form.get("Body", "")
        return process_message(text, user)
    else:  # GET
        # prueba en navegador
        return (
            "Ruta /chat activa 🚀\n"
            "Para probarla correctamente, envía un POST con los campos:\n"
            "- From (usuario)\n"
            "- Body (mensaje)\n\n"
            "Ejemplo con cURL:\n"
            "curl -X POST https://tu-bot.onrender.com/chat -d 'From=web_user' -d 'Body=Hola'"
        )

