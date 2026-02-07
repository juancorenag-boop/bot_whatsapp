# Negocios.py
BUSINESSES = {
    "1": {
        "name": "Tienda La Esquina",
        "type": "store",
        "phone": "573216642926",
        "payment_info": (
            "🏦 *Pago Tienda La Esquina*\n"
            "Banco: Bancolombia\n"
            "Cuenta: 111222333\n"
            "Tipo: Ahorros\n"
            "Nombre: Tienda La Esquina"
        ),
        "inventory": [
            # ===== ABARROTES =====
            {"tipo": "arroz", "marca": "roa", "precio": 4500, "stock": 10},
            {"tipo": "arroz", "marca": "diana", "precio": 5000, "stock": 10},

            {"tipo": "leche", "marca": "ciledco", "precio": 2000, "stock": 5},
            {"tipo": "leche", "marca": "karen", "precio": 3000, "stock": 2},
            {"tipo": "leche", "marca": "alqueria", "precio": 4000, "stock": 3},

            # ===== VERDURAS (POR LIBRA) =====
            {"tipo": "tomate", "marca": "", "precio": 1800, "unidad": "libra", "stock": 10},
            {"tipo": "papa", "marca": "", "precio": 1200, "unidad": "libra", "stock": 20},
            {"tipo": "cebolla", "marca": "", "precio": 1500, "unidad": "libra", "stock": 20},
            {"tipo": "zanahoria", "marca": "", "precio": 1300, "unidad": "libra", "stock": 15},
            {"tipo": "banano", "marca": "", "precio": 1200, "unidad": "libra", "stock": 13},
        ]
    },
# ======================= RESTAURANTES ===================================================================

    "2": {
        "name": "Restaurante Donde Kati",
        "type": "restaurant",
        "phone": "573104567890",
        "payment_info": (
            "🏦 *Pago Restaurante Donde Kati*\n"
            "Banco: Nequi\n"
            "Número: 3104567890\n"
            "Nombre: Donde Kati"
        ),
        "menu": [
            {"tipo": "carne asada", "precio": 20000},
            {"tipo":"cerdo asado", "precio":18000},
            {"tipo": "gaseosa", "precio": 5000},
        ]
    }
}

