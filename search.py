from inventory import INVENTARIO

def buscar(texto):
    texto = texto.lower().strip()
    resultados = []

    for prod in INVENTARIO:
        tipo = prod["tipo"].lower()
        # Ignoramos marca y stock, buscamos solo por tipo
        if texto in tipo:
            resultados.append(prod)

    return resultados
