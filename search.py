def buscar(texto, inventario):
    texto = texto.lower()
    palabras = texto.split()

    resultados = []

    for p in inventario:
        score = 0
        for palabra in palabras:
            if palabra in p["tipo"]:
                score += 2
            if palabra in p["marca"]:
                score += 3
            if palabra == "barato":
                score += max(0, 5000 - p["precio"]) / 1000

        if score > 0:
            resultados.append((score, p))

    resultados.sort(reverse=True, key=lambda x: x[0])
    return [p for _, p in resultados]
