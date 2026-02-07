# responses.py

def saludo():
    return "👋 Bienvenido a la tienda Escribe el producto que buscas: Ej: arroz, leche, tomate"

def lista_productos(items):
    texto = ""
    hay_stock = False

    for i, p in enumerate(items, 1):
        # 🏪 TIENDA → respeta stock
        if "stock" in p:
            if p.get("stock", 0) > 0:
                hay_stock = True
                texto += f"{i}. {p['tipo']} - ${p['precio']}\n"
        # 🍽️ RESTAURANTE → ignora stock
        else:
            texto += f"{i}. {p['tipo']} - ${p['precio']}\n"

    if texto:
        return texto

    return "❌ No encontramos ese producto con stock disponible."

