if order["step"] == "seleccionar":
    body_norm = normalizar(body)

    for p in order["resultados"]:
        nombre_norm = normalizar(p["nombre"])

        if body_norm == nombre_norm:
            order["cart"].append(p)
            order["total"] += p["precio"]
            order["step"] = "mas"

            resp.message(
                f"✅ *{p['nombre']}* agregado.\n"
                f"💰 Total actual: ${order['total']}\n\n"
                "¿Necesitas algo más?\n"
                "✍️ Escribe qué necesitas (ej: arroz)\n"
                "✔️ O escribe *ok* para continuar"
            )
            return str(resp)

    resp.message("❌ Escríbelo exactamente como aparece en la lista.")
    return str(resp)
