# responses.py

def saludo():
    return "👋 Bienvenido a la tienda Escribe el producto que buscas: Ej: arroz, leche, tomate"

def lista_productos(resultados):
    texto = "🛒 Productos disponibles:\n"
    contador = 1
    for p in resultados:
        stock = p.get("stock", 0)
        if stock <= 0:
            continue  # ignoramos productos sin stock

        marca = p.get("marca","")
        if marca:
            texto += f"{contador}. {p['tipo'].title()} {marca.title()} - ${p['precio']}\n"
        else:
            texto += f"{contador}. {p['tipo'].title()} - ${p['precio']}\n"
        contador += 1

    if contador == 1:
        return "❌ No encontramos ese producto con stock disponible."
    texto += "Responde con el número para agregarlo."
    return texto

