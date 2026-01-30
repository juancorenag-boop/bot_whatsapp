def saludo():
    return (
        "👋 Bienvenido a la tienda\n\n"
        "Escribe lo que buscas:\n"
        "1) arroz\n"
        "2) leche barata\n"
        "3) marca"
    )

def lista_productos(productos):
    texto = "🛒 Productos disponibles:\n\n"

    for i, p in enumerate(productos, start=1):
        texto += f"{i}) {p['nombre']}\n"
        texto += f"   Precio: ${p['precio']} | Stock: {p['stock']}\n\n"

    texto += "Responde SOLO con el número para agregar al pedido\n"
    texto += "O escribe otro producto para seguir buscando"

    return texto
