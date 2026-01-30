from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from inventory import INVENTARIO

app = Flask(__name__)

usuarios = {}

def buscar_producto(texto):
    return [p for p in INVENTARIO if p["tipo"] == texto]

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    msg = request.form.get("Body").lower().strip()
    user = request.form.get("From")

    if user not in usuarios:
        usuarios[user] = {
            "estado": "inicio",
            "pedido": [],
            "opciones": [],
            "seleccion": None
        }

    u = usuarios[user]
    resp = MessagingResponse()
    r = resp.message()

    # SALUDO
    if msg in ["hola", "buenas"]:
        r.body("Hola 👋 ¿Qué producto necesitas?")
        return str(resp)

    # BUSCAR PRODUCTO
    if u["estado"] == "inicio":
        productos = buscar_producto(msg)
        if productos:
            u["opciones"] = productos
            u["estado"] = "seleccion"
            texto = "Elige una opción:\n"
            for i, p in enumerate(productos, 1):
                texto += f"{i}. {p['tipo'].capitalize()} {p['marca'].capitalize()} - ${p['precio']}\n"
            r.body(texto)
        else:
            r.body("No encontré ese producto, intenta de nuevo")
        return str(resp)

    # SELECCIÓN
    if u["estado"] == "seleccion":
        if msg.isdigit():
            idx = int(msg) - 1
            if idx < len(u["opciones"]):
                u["seleccion"] = u["opciones"][idx]
                u["estado"] = "cantidad"
                r.body("¿Cuántos deseas?")
            else:
                r.body("Opción inválida")
        return str(resp)

    # CANTIDAD
    if u["estado"] == "cantidad":
        if msg.isdigit():
            cantidad = int(msg)
            prod = u["seleccion"]
            u["pedido"].append({
                "tipo": prod["tipo"],
                "marca": prod["marca"],
                "precio": prod["precio"],
                "cantidad": cantidad
            })
            u["estado"] = "agregar_mas"
            u["seleccion"] = None
            r.body("Producto agregado ✅\n¿Deseas algo más?\nEscribe el producto o OK para finalizar")
        return str(resp)

    # AGREGAR MÁS
    if u["estado"] == "agregar_mas":
        if msg == "ok":
            texto = "🧾 Pedido:\n"
            for p in u["pedido"]:
                texto += f"- {p['cantidad']} x {p['tipo']} {p['marca']}\n"
            texto += "\nEscribe OK para confirmar o:\nquitar 1 arroz"
            u["estado"] = "confirmar"
            r.body(texto)
        else:
            u["estado"] = "inicio"
            return whatsapp()
        return str(resp)

    # CONFIRMAR / QUITAR
    if u["estado"] == "confirmar":
        if msg == "ok":
            u["estado"] = "direccion"
            r.body("📍 Escribe tu dirección")
        elif msg.startswith("quitar"):
            partes = msg.split()
            if len(partes) >= 3 and partes[1].isdigit():
                cantidad = int(partes[1])
                tipo = partes[2]
                for p in u["pedido"]:
                    if p["tipo"] == tipo:
                        p["cantidad"] -= cantidad
                u["pedido"] = [p for p in u["pedido"] if p["cantidad"] > 0]
                r.body("Producto actualizado. Escribe OK para confirmar")
        return str(resp)

    # DIRECCIÓN
    if u["estado"] == "direccion":
        u["direccion"] = msg
        u["estado"] = "pago"
        r.body("💰 Método de pago: transferencia o efectivo")
        return str(resp)

    # PAGO
    if u["estado"] == "pago":
        if msg == "transferencia":
            r.body("💳 Bancolombia\nCuenta: 123456789\nEnvía el comprobante")
        elif msg == "efectivo":
            r.body("¿Necesitas cambio?")
        return str(resp)

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)

