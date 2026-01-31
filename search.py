# search.py
from inventory import INVENTARIO

def buscar(texto):
    texto = texto.lower().strip()
    resultados = []

    for prod in INVENTARIO:
        tipo = prod.get("tipo", "").lower().strip()
        # Siempre incluimos el producto si el tipo coincide, sin importar marca
        if texto in tipo:
            resultados.append(prod)

    return resultados
