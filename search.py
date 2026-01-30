from inventory import INVENTARIO

def buscar(texto):
    texto = texto.lower()
    resultados = []

    for p in INVENTARIO:
        if (
            texto in p["tipo"].lower()
            or texto in p["marca"].lower()
        ) and p["stock"] > 0:
            resultados.append(p)

    return resultados
