from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

from search import buscar
from responses import saludo, lista_productos

app = Flask(__name__)

orders = {}
last_results = {}

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    text = request.values.get("Body", "").strip()
    user = request.values.get("From")

    resp = MessagingResponse()
    msg = resp.message()

    text_lower = text.lower()

    # SALUDO
    if text_lower in ["hola", "buenas", "hello"]:
        msg.body(saludo())
        return str(resp)

    # SELECCIÓN NUMÉRICA
    if text.isdigit() and user in last_results:
        idx = int(text) - 1
        productos = last_results[user]

        if 0 <= idx < len(productos):
            producto = productos[idx]
            orders.setdefault(user, []).append(producto)

            msg.body(
                f"✅ Agregado:\n"
                f"{producto['tipo'].title()} {producto['marca'].title()} "
                f"- ${producto['precio']}"
            )
        else:
            msg.body("❌ Número inválido.")
        return str(resp)

    # BÚSQUEDA POR TEXTO
    resultados = buscar(text_lower)

    if resultados:
        last_results[user] = resultados
        msg.body(lista_productos(resultados))
    else:
        msg.body("❌ No encontré productos con ese nombre.")

    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
