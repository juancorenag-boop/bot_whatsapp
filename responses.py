def saludo():
    return (
        "👋 Bienvenido a la tienda\n\n"
        "Escribe el producto que buscas:\n"
        "Ej: arroz, leche, roa, diana"
    )

def lista_productos(productos):
    msg = "🛒 Productos disponibles:\n\n"
    for i, p in enumerate(productos, start=1):
        msg += (
            f"{i}. {p['tipo'].title()} {p['marca'].title()} "
            f"- ${p['precio']} (Stock: {p['stock']})\n"
        )
    msg += "\nResponde con el número para agregarlo."
    return msg
