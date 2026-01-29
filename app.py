from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

from inventory import INVENTARIO
from search import buscar
from responses import saludo, lista_productos

app = Flask(__name__)

# memoria simple (en producción usarías Redis o base de datos)
orders = {}

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    body = request.form.get("Body", "").strip().lower()
    from_number = request.form.get("From")

    resp = MessagingResponse()

    # ===== INICIO / REINICIO =====
    if body in ["hola", "menu", "inicio", "empezar"]:
        orders[from_number] = {
            "step": "buscar",
            "cart": [],           # ahora cada item tendrá: {"nombre", "precio", "cantidad"}
            "total": 0,
            "resultados": []
        }
        resp.message(saludo())
        return str(resp)

    # Inicializar sesión si no existe
    if from_number not in orders:
        orders[from_number] = {
            "step": "buscar",
            "cart": [],
            "total": 0,
            "resultados": []
        }

    order = orders[from_number]

    # ===== MANEJO DE ELIMINAR =====
    if body.startswith(("eliminar ", "quitar ", "borrar ", "sacar ")):
        comando = body.split(" ", 1)[0]
        resto = body.split(" ", 1)[1] if len(body.split()) > 1 else ""

        if resto in ["todo", "todos", "carrito", "todo el carrito"]:
            order["cart"] = []
            order["total"] = 0
            resp.message("🗑️ Carrito vaciado completamente.\n¿Qué necesitas ahora?")
            return str(resp)

        if resto == "último" or resto == "ultimo":
            if order["cart"]:
                ultimo = order["cart"].pop()
                order["total"] -= ultimo["precio"] * ultimo["cantidad"]
                resp.message(f"🗑️ Eliminado: {ultimo['cantidad']} × {ultimo['nombre']}\nTotal ahora: ${order['total']}")
            else:
                resp.message("El carrito está vacío.")
            return str(resp)

        # Buscar coincidencia parcial o exacta
        encontrado = False
        for i, item in enumerate(order["cart"]):
            if resto in item["nombre"].lower() or item["nombre"].lower() in resto:
                cantidad_eliminar = item["cantidad"]
                order["total"] -= item["precio"] * cantidad_eliminar
                del order["cart"][i]
                encontrado = True
                resp.message(f"🗑️ Eliminado: {cantidad_eliminar} × {item['nombre']}\nTotal ahora: ${order['total']}")
                break

        if not encontrado:
            resp.message(f"No encontré '{resto}' en tu carrito.\nEscribe 'ver carrito' para ver lo que tienes.")
        return str(resp)

    # ===== VER CARRITO =====
    if body in ["ver carrito", "carrito", "ver pedido", "qué tengo", "lista"]:
        if not order["cart"]:
            resp.message("🛒 Tu carrito está vacío.\nEscribe algo para buscar productos.")
        else:
            mensaje = "🛒 Tu carrito actual:\n\n"
            for item in order["cart"]:
                sub = item["cantidad"] * item["precio"]
                mensaje += f"• {item['cantidad']} × {item['nombre']} — ${sub}\n"
            mensaje += f"\n💰 Total: ${order['total']}\n\n"
            mensaje += "• Escribe 'ok' para confirmar\n• Escribe 'eliminar [producto]' para quitar algo"
            resp.message(mensaje)
        return str(resp)

    # ===== PASO 1: BUSCAR PRODUCTOS =====
    if order["step"] == "buscar":
        resultados = buscar(body, INVENTARIO)

        if not resultados:
            resp.message("❌ No encontré productos con eso. Intenta otra palabra o escribe 'hola' para reiniciar.")
            return str(resp)

        order["resultados"] = resultados
        order["step"] = "seleccionar"

        resp.message(
            lista_productos(resultados) +
            "\n\n✍️ Escribe el nombre (o cantidad + nombre)\nEjemplos:\n• leche\n• 3 huevos\n• pan 2"
        )
        return str(resp)

    # ===== PASO 2: SELECCIONAR / AGREGAR =====
    if order["step"] == "seleccionar":
        cantidad = 1
        texto = body.strip()

        # Extraer posible cantidad al inicio o al final
        partes = texto.split()
        if partes and partes[0].isdigit():
            cantidad = int(partes[0])
            texto = " ".join(partes[1:]).strip()
        elif partes and partes[-1].isdigit():
            cantidad = int(partes[-1])
            texto = " ".join(partes[:-1]).strip()

        producto_encontrado = None
        for p in order["resultados"]:
            if p["nombre"].lower() == texto.lower():
                producto_encontrado = p
                break

        if producto_encontrado:
            # Agregar o sumar si ya existe
            encontrado_en_carrito = False
            for item in order["cart"]:
                if item["nombre"].lower() == producto_encontrado["nombre"].lower():
                    item["cantidad"] += cantidad
                    encontrado_en_carrito = True
                    break

            if not encontrado_en_carrito:
                order["cart"].append({
                    "nombre": producto_encontrado["nombre"],
                    "precio": producto_encontrado["precio"],
                    "cantidad": cantidad
                })

            order["total"] += producto_encontrado["precio"] * cantidad
            order["step"] = "mas"

            resp.message(
                f"✅ Agregado: {cantidad} × {producto_encontrado['nombre']}\n"
                f"💰 Total actual: ${order['total']}\n\n"
                "¿Algo más?\n"
                "Ej: 2 arroz, huevos, ok, ver carrito, eliminar leche"
            )
            return str(resp)

        # Si no encontró → nueva búsqueda
        resultados = buscar(body, INVENTARIO)
        if not resultados:
            resp.message("❌ No reconocí ese producto.\nIntenta con el nombre exacto o escribe otra cosa.")
            return str(resp)

        order["resultados"] = resultados
        order["step"] = "seleccionar"
        resp.message(
            lista_productos(resultados) +
            "\n✍️ Escribe cantidad + nombre (ej: 3 leche) o solo el nombre."
        )
        return str(resp)

    # ===== PASO 3: ¿ALGO MÁS? =====
    if order["step"] == "mas":
        if body in ["ok", "finalizar", "terminar", "listo"]:
            if not order["cart"]:
                resp.message("Tu carrito está vacío. Escribe algo para agregar productos.")
                return str(resp)

            resumen = "🧾 Resumen de tu pedido:\n\n"
            for item in order["cart"]:
                sub = item["cantidad"] * item["precio"]
                resumen += f"• {item['cantidad']} × {item['nombre']} — ${sub}\n"
            resumen += f"\n💰 Total: ${order['total']}\n\n"
            resumen += "¿Confirmas el pedido? (sí / no)"
            order["step"] = "confirmar"
            resp.message(resumen)
            return str(resp)

        # Si escribe otra cosa → intenta buscar/agregar
        resultados = buscar(body, INVENTARIO)
        if not resultados:
            resp.message("Escribe 'ok' para finalizar, 'ver carrito', 'eliminar [producto]' o busca otro producto.")
            return str(resp)

        order["resultados"] = resultados
        order["step"] = "seleccionar"
        resp.message(
            lista_productos(resultados) +
            "\n✍️ Escribe cantidad + nombre o solo el nombre."
        )
        return str(resp)

    # ===== PASO 4: CONFIRMAR =====
    if order["step"] == "confirmar":
        if body in ["si", "sí", "confirmo", "confirmar", "acepto"]:
            order["step"] = "direccion"
            resp.message("📍 Perfecto. Escríbeme la dirección de entrega (puedes escribir lo que quieras):")
            return str(resp)

        resp.message("❌ Pedido cancelado.\nEscribe hola para empezar de nuevo.")
        orders.pop(from_number, None)
        return str(resp)

    # ===== PASO 5: DIRECCIÓN =====
    if order["step"] == "direccion":
        direccion = body.strip() or "No especificada"

        mensaje_final = (
            "🎉 ¡Pedido confirmado!\n\n"
            f"📍 Dirección: {direccion}\n"
            f"💰 Total: ${order['total']}\n\n"
            "En breve nos pondremos en contacto. ¡Gracias por comprar con nosotros!"
        )

        # Aquí podrías guardar en base de datos, enviar notificación al negocio, etc.

        orders.pop(from_number, None)
        resp.message(mensaje_final)
        return str(resp)

    # Fallback
    resp.message("No entendí muy bien 😅\nEscribe hola para ver el menú o ver carrito para revisar tu pedido.")
    return str(resp)


@app.route("/")
def home():
    return "Bot de tienda por WhatsApp funcionando 🚀"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
