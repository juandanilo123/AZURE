from pathlib import Path
import numpy as np
import pandas as pd
from faker import Faker

# =========================================================
# CONFIGURACIÓN
# =========================================================

SEED = 2026
np.random.seed(SEED)
Faker.seed(SEED)
fake = Faker("es_CO")

OUT = Path("datos_registro_retail")
(OUT / "csv").mkdir(parents=True, exist_ok=True)
(OUT / "parquet").mkdir(parents=True, exist_ok=True)

N_ART = 5_000
N_PROV = 800
N_TIEN = 150
N_CLI = 50_000
N_VENT = 1_000_000
N_INV = 750_000
N_DEV = 50_000

fechas = pd.date_range("2025-01-01", "2025-12-31")
paises = ["Colombia", "México", "Chile", "Perú", "Ecuador"]
ciudades = ["Bogotá", "Medellín", "Cali", "Ciudad de México",
            "Santiago", "Lima", "Quito"]
categorias = ["Alimentos", "Cuidado personal", "Hogar",
              "Electrónica", "Ropa", "Bebés"]
canales = ["Tienda física", "Web", "App", "Marketplace"]


def guardar(df, nombre):
    df.to_csv(OUT / "csv" / f"{nombre}.csv", index=False)
    df.to_parquet(
        OUT / "parquet" / f"{nombre}.parquet",
        index=False,
        compression="snappy"
    )
    print(f"{nombre}: {len(df):,}")


# =========================================================
# 1. PROVEEDORES
# =========================================================

proveedores = pd.DataFrame({
    "id_proveedor": np.arange(1, N_PROV + 1),
    "razon_social": [f"Proveedor {i:04d} S.A.S." for i in range(1, N_PROV + 1)],
    "pais_origen": np.random.choice(paises, N_PROV),
    "tiempo_repo_dias": np.random.randint(1, 31, N_PROV),
    "calificacion_calidad": np.round(np.random.uniform(1, 5, N_PROV), 2),
    "activo": np.random.choice([True, False], N_PROV, p=[0.95, 0.05])
})


# =========================================================
# 2. ARTÍCULOS
# =========================================================

articulos = pd.DataFrame({
    "art_id": np.arange(1, N_ART + 1),
    "cod_barra": [f"770{i:010d}" for i in range(1, N_ART + 1)],
    "desc_art": [f"Artículo Retail {i:05d}" for i in range(1, N_ART + 1)],
    "id_categ_n1": np.random.choice(categorias, N_ART),
    "id_categ_n2": np.random.choice([f"Subcategoría {i}" for i in range(1, 21)], N_ART),
    "id_categ_n3": np.random.choice([f"Línea {i}" for i in range(1, 51)], N_ART),
    "id_proveedor": np.random.randint(1, N_PROV + 1, N_ART),
    "precio_lista": np.round(np.random.lognormal(10, 1, N_ART), 2),
    "peso_kg": np.round(np.random.uniform(0.1, 30, N_ART), 2),
    "unid_medida": "UNIDAD",
    "activo": np.random.choice([True, False], N_ART, p=[0.97, 0.03]),
    "fec_alta": np.random.choice(fechas, N_ART)
})


# =========================================================
# 3. TIENDAS
# =========================================================

tiendas = pd.DataFrame({
    "id_tienda": np.arange(1, N_TIEN + 1),
    "nom_tienda": [f"RetailMax {i:03d}" for i in range(1, N_TIEN + 1)],
    "tipo_tienda": np.random.choice(
        ["Hipermercado", "Supermercado", "Conveniencia"], N_TIEN
    ),
    "id_ciudad": np.random.choice(ciudades, N_TIEN),
    "id_pais": np.random.choice(paises, N_TIEN),
    "metros_cuadrados": np.random.randint(200, 15000, N_TIEN),
    "activo": np.random.choice([True, False], N_TIEN, p=[0.97, 0.03]),
    "fec_apertura": np.random.choice(fechas, N_TIEN)
})


# =========================================================
# 4. CLIENTES
# =========================================================

clientes = pd.DataFrame({
    "id_miembro": np.arange(1, N_CLI + 1),
    "fec_registro": np.random.choice(fechas, N_CLI),
    "id_ciudad": np.random.choice(ciudades, N_CLI),
    "genero": np.random.choice(["M", "F", "No informado"], N_CLI),
    "rango_edad": np.random.choice(
        ["18-25", "26-35", "36-45", "46-60", "+60"], N_CLI
    ),
    "canal_pref": np.random.choice(canales, N_CLI),
    "activo": np.random.choice([True, False], N_CLI, p=[0.90, 0.10]),
    "fec_ultima_compra": np.random.choice(fechas, N_CLI)
})


# =========================================================
# 5. VENTAS
# =========================================================

ventas = pd.DataFrame({
    "id_trans": np.arange(1, N_VENT + 1),
    "id_miembro": np.random.randint(1, N_CLI + 1, N_VENT),
    "id_tienda": np.random.randint(1, N_TIEN + 1, N_VENT),
    "art_id": np.random.randint(1, N_ART + 1, N_VENT),
    "fec_trans": np.random.choice(fechas, N_VENT),
    "hra_trans": [
        f"{h:02d}:{m:02d}:00"
        for h, m in zip(
            np.random.choice(
                range(8, 23),
                N_VENT,
                p=np.array([1, 1, 2, 3, 5, 6, 4, 3, 4, 5, 6, 5, 3, 1, 1]) / 50
            ),
            np.random.randint(0, 60, N_VENT)
        )
    ],
    "qty_vendida": np.random.choice(
        [1, 2, 3, 4, 5], N_VENT, p=[0.50, 0.25, 0.13, 0.08, 0.04]
    ),
    "precio_unitario_venta": np.round(
        np.random.lognormal(10, 1, N_VENT), 2
    ),
    "descuento_aplicado": np.round(
        np.random.choice([0, 5000, 10000, 20000], N_VENT,
                         p=[0.70, 0.15, 0.10, 0.05]), 2
    ),
    "tipo_pago": np.random.choice(
        ["Efectivo", "Débito", "Crédito", "PSE", "Billetera"], N_VENT
    ),
    "canal_venta": np.random.choice(
        canales, N_VENT, p=[0.55, 0.20, 0.17, 0.08]
    )
})


# =========================================================
# 6. INVENTARIO
# =========================================================

stock_min = np.random.randint(5, 50, N_INV)
stock_max = stock_min + np.random.randint(50, 500, N_INV)
stock_fisico = np.random.randint(0, 500, N_INV)

inventario = pd.DataFrame({
    "id_snapshot": np.arange(1, N_INV + 1),
    "art_id": np.random.randint(1, N_ART + 1, N_INV),
    "id_tienda": np.random.randint(1, N_TIEN + 1, N_INV),
    "fec_snapshot": np.random.choice(fechas, N_INV),
    "stock_fisico": stock_fisico,
    "stock_transito": np.random.randint(0, 100, N_INV),
    "stock_reservado": np.minimum(
        stock_fisico, np.random.randint(0, 50, N_INV)
    ),
    "stock_minimo_config": stock_min,
    "stock_maximo_config": stock_max
})


# =========================================================
# 7. DEVOLUCIONES
# =========================================================

ids_ventas_dev = np.random.choice(
    ventas["id_trans"], N_DEV, replace=False
)

ventas_dev = (
    ventas.set_index("id_trans")
    .loc[ids_ventas_dev]
    .reset_index()
)

devoluciones = pd.DataFrame({
    "id_devolucion": np.arange(1, N_DEV + 1),
    "id_trans_origen": ventas_dev["id_trans"],
    "art_id": ventas_dev["art_id"],
    "id_tienda": ventas_dev["id_tienda"],
    "fec_devolucion": np.random.choice(fechas, N_DEV),
    "qty_devuelta": np.random.choice([1, 2, 3], N_DEV, p=[0.75, 0.20, 0.05]),
    "motivo_cod": np.random.choice(
        ["DEFECTO", "INCORRECTO", "TALLA", "EXPECTATIVA", "TRANSPORTE"],
        N_DEV
    ),
    "canal_devolucion": np.random.choice(canales, N_DEV),
    "estado_devolucion": np.random.choice(
        ["Solicitada", "Aprobada", "Rechazada", "Reembolsada"], N_DEV
    ),
    "vr_reembolso": np.round(
        np.random.uniform(5000, 500000, N_DEV), 2
    )
})


# =========================================================
# NULOS CONTROLADOS: 5 %
# =========================================================

for df, columna in [
    (proveedores, "calificacion_calidad"),
    (articulos, "peso_kg"),
    (clientes, "rango_edad"),
    (ventas, "tipo_pago"),
    (devoluciones, "canal_devolucion")
]:
    indices = np.random.choice(
        df.index,
        int(len(df) * 0.05),
        replace=False
    )
    df.loc[indices, columna] = None


# =========================================================
# ANOMALÍAS INTENCIONALES
# =========================================================

# Cantidades negativas
ventas.loc[0:4, "qty_vendida"] = -1

# Fechas fuera del periodo
ventas.loc[5:9, "fec_trans"] = pd.Timestamp("2030-01-01")

# Descuentos superiores a la venta
ventas.loc[10:14, "descuento_aplicado"] = 9_999_999

# Stock reservado superior al stock físico
inventario.loc[0:4, "stock_reservado"] = (
    inventario.loc[0:4, "stock_fisico"] + 100
)


# =========================================================
# GUARDAR CSV Y PARQUET
# =========================================================

tablas = {
    "MSTR_ARTICULOS": articulos,
    "MSTR_PROVEEDORES": proveedores,
    "MSTR_TIENDAS": tiendas,
    "CRM_MIEMBROS": clientes,
    "TRANS_VENTAS": ventas,
    "INV_STOCK_DIARIO": inventario,
    "POST_DEVOLUCIONES": devoluciones
}

for nombre, tabla in tablas.items():
    guardar(tabla, nombre)


# =========================================================
# VALIDAR RESULTADO
# =========================================================

total = sum(len(tabla) for tabla in tablas.values())

print("-" * 55)
print(f"TOTAL GENERADO: {total:,}")
print(f"TOTAL ESPERADO: {1_855_950:,}")

assert total == 1_855_950
assert articulos["id_proveedor"].isin(proveedores["id_proveedor"]).all()
assert ventas["art_id"].isin(articulos["art_id"]).all()
assert ventas["id_tienda"].isin(tiendas["id_tienda"]).all()
assert ventas["id_miembro"].isin(clientes["id_miembro"]).all()
assert devoluciones["id_trans_origen"].isin(ventas["id_trans"]).all()

print("Integridad referencial: CORRECTA")
print("Archivos CSV y Parquet creados en:", OUT.resolve())