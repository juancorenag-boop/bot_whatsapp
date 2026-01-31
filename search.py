# search.py
from inventory import INVENTARIO

def buscar(texto):
    texto = texto.lower().strip()
    resultados = []

    for prod in INVENTARIO:
        tipo = prod["tipo"].lower()
        marca = prod.get("marca", "").lower()
        # Coincidencia parcial en tipo o marca (marca vacía no bloquea)
        if texto in tipo or (marca and texto in marca):
            resultados.append(prod)
    return resultados
