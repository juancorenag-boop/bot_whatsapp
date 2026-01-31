from flask import Flask, request, render_template_string, session
import re

from inventory import INVENTARIO  # Asegúrate de que inventory.py tenga todos los productos
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
            subtotal = p.get("subtotal", 0)
            texto += f"- {p['cantidad']} lb {p['tipo'].title()} = ${int(subtotal)}\n"
        else:
            subtotal = p.get("precio", 0) * p.get("cantidad", 0)
            texto += f"- {p['cantidad']} x {p['tipo'].title()} {p.get('marca','').title()} = ${subtotal}\n"
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
            nombre = f"{p['tipo']} {p.get('marca','')}".lower()
            if producto_txt in nombre:
                if p["cantidad"] > cantidad:
                    p["cantidad"] -= cantidad
                    if p.get("unidad") == "libra":
                        p["subtotal"] = p["cantidad"] * p.get("precio",0)
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
            # Map para reconocer expresiones de libra
            mapping = {
                "media libra": 0.5,
                "una libra": 1,
                "libra": 1,
                "libra y media": 1.5,
                "dos libras": 2
            }

            text_normalizado = text.lower().strip()
            cantidad = mapping.get(text_normalizado)

            if cantidad is None:
                try:
                    cantidad = float(text.replace(",", "."))
                    if cantidad <= 0:
                        raise ValueError
                except ValueError:
                    return (
                        "❌ Escribe una cantidad válida.\n"
                        "0.5 (media libra)\n"
                        "1 (una libra)\n"
                        "1.5 (libra y media)\n"
                        "2 (dos libras)"
                    )

            producto["cantidad"] = cantidad
            producto["subtotal"] = cantidad * producto.get("precio", 0)
            orders.setdefault(user, []).append(producto)
            pending_product.pop(user)

            return (
                f"✅ {cantidad} lb de {producto['tipo'].title()} agregado\n"
                f"💰 Subtotal: ${int(producto['subtotal'])}\n\n"
                "👉 Escribe otro producto\n"
                "👉 O escribe *ok* para finalizar"
            )

        # Cantidad por unidades normales
        if text.isdigit():
            producto["cantidad"] = int(text)
            producto["subtotal"] = producto["cantidad"] * producto.get("precio",0)  # <-- agregar esto
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
            if "subtotal" not in prod:
                prod["subtotal"] = prod.get("precio",0)
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

            return f"¿Cuántas unidades de {prod['tipo'].title()} {prod.get('marca','').title()} deseas?"

    # ---- BÚSQUEDA ----
    try:
        resultados = buscar(text_lower)
        if resultados:
            last_results[user] = resultados
            return lista_productos(resultados)
    except Exception as e:
        print(f"Error en búsqueda: {e}")
        resultados = []

    # Si no hay resultados o hubo error
    return "❌ No encontramos ese producto. Por favor intenta con otro."

def resumen_pedido(user):
    pedido = orders.get(user, [])
    if not pedido:
        return "🛒 Tu pedido está vacío"

    resumen = "🧾 *Resumen de tu pedido:*\n\n"
    total = 0

    for i, p in enumerate(pedido, start=1):
        subtotal = p.get("subtotal") or p.get("precio",0) * p.get("cantidad",1)
        if p.get("unidad") == "libra":
            resumen += f"{i}. {p['cantidad']} lb {p['tipo'].title()} — ${int(subtotal)}\n"
        else:
            resumen += f"{i}. {p['cantidad']} x {p['tipo'].title()} {p.get('marca','').title()} — ${int(subtotal)}\n"
        total += subtotal

    resumen += f"\n💰 *Total:* ${int(total)}\n\n"
    resumen += "👉 confirmar\n👉 quitar 0.5 de tomate/ 1 de leche"
    return resumen

# =========================
# 🌐 RUTAS CON CHAT WEB
# =========================
@app.route("/", methods=["GET"])
def home():
    return "Bot activo 🚀"

# Página de chat interactivo
CHAT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Chat Bot</title>
    <style>
        body { font-family: Arial; margin: 20px; }
        #chat-box { border:1px solid #ccc; padding:10px; height:400px; overflow-y:auto; margin-bottom:10px; }
        #user-input { width:80%; padding:10px; }
        #send-btn { padding:10px; }
        .user-msg { color: blue; }
        .bot-msg { color: green; }
    </style>
</head>
<body>
    <h2>Chat Bot</h2>
    <div id="chat-box"></div>
    <input type="text" id="user-input" placeholder="Escribe un mensaje"/>
    <button id="send-btn">Enviar</button>

    <script>
        const chatBox = document.getElementById("chat-box");
        const input = document.getElementById("user-input");
        const button = document.getElementById("send-btn");

        function appendMessage(text, cls) {
            const p = document.createElement("p");
            p.className = cls;
            p.textContent = text;
            chatBox.appendChild(p);
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        button.onclick = () => {
            const msg = input.value.trim();
            if(!msg) return;
            appendMessage("Tú: " + msg, "user-msg");
            input.value = "";

            fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: `From=web_user&Body=${encodeURIComponent(msg)}`
            })
            .then(res => res.text())
            .then(text => appendMessage("Bot: " + text, "bot-msg"));
        }

        input.addEventListener("keypress", function(e){
            if(e.key === "Enter") button.click();
        });
    </script>
</body>
</html>
"""

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if request.method == "POST":
        user = request.form.get("From", "web_user")
        text = request.form.get("Body", "")
        return process_message(text, user)
    else:
        return render_template_string(CHAT_HTML)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
