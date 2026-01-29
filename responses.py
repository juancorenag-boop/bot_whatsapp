def saludo():
    return (
        "👋 *Bienvenido a la tienda*\n\n"
        "Escribe lo que buscas:\n"
        "• arroz\n"
        "• leche barata\n"
        "• marca\n"
    )

def lista_productos(productos):
    if not productos:
        return "❌ No encontré ese producto."

    msg = "🛒 *Productos disponibles:*\n\n"
    for p in productos[:5]:
        msg += (
            f"• {p['tipo'].title()} {p['marca'].title()}\n"
            f"  💰 ${p['precio']} | 📦 {p['stock']}\n\n"
        )

    msg += "✍️ Escribe otro producto para seguir buscando"
    return msg
