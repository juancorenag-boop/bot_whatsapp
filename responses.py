# responses.py

def saludo():
    return "👋 Bienvenido a la tienda Escribe el producto que buscas: Ej: arroz, leche, tomate"

def lista_productos(resultados):
    texto = "🛒 Productos disponibles:\n"
    for i, p in enumerate(resultados, start=1):
        marca = p.get("marca","")
        if marca:
            texto += f"{i}. {p['tipo'].title()} {marca.title()} - ${p['precio']} (Stock: {p.get('stock', 0)})\n"
        else:
            texto += f"{i}. {p['tipo'].title()} - ${p['precio']} (Stock: {p.get('stock', 0)})\n"
    texto += "Responde con el número para agregarlo."
    return texto
