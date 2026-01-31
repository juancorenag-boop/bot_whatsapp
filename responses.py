# responses.py

def saludo():
    return "👋 Bienvenido a la tienda Escribe el producto que buscas: Ej: arroz, leche, tomate"

def lista_productos(productos):
    # Filtrar productos con stock > 0
    disponibles = [p for p in productos if p.get("stock", 0) > 0]
    if not disponibles:
        return "❌ No encontramos ese producto con stock disponible."

    texto = "🛒 Productos disponibles:\n"
    for i, p in enumerate(disponibles, start=1):
        marca = f" {p.get('marca','')}" if p.get('marca') else ""
        texto += f"{i}. {p['tipo'].title()}{marca} - ${p['precio']}\n"
    texto += "Responde con el número para agregarlo."
    return texto

