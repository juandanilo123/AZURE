
from pathlib import Path
from getpass import getpass

import pandas as pd
import pyodbc


# ============================================================
# CONFIGURACIÓN DE CONEXIÓN
# ============================================================

SERVIDOR = "sql-retail-data.database.windows.net"
BASE_DATOS = "databasecomercio"
USUARIO = "databaseadmin"

# Carpeta donde están los archivos CSV
CARPETA_CSV = Path("datos_registro_retail/csv")

# Solicitar contraseña sin mostrarla
password = getpass("Contraseña de Azure SQL: ")

# Cadena de conexión
cadena_conexion = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER=tcp:{SERVIDOR},1433;"
    f"DATABASE={BASE_DATOS};"
    f"UID={USUARIO};"
    f"PWD={password};"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=60;"
)


# ============================================================
# ORDEN DE CARGA
# ============================================================
# Las tablas se cargan en este orden para respetar las
# relaciones entre tablas y las claves foráneas.
# ============================================================

TABLAS = [
    "MSTR_PROVEEDORES",
    "MSTR_ARTICULOS",
    "MSTR_TIENDAS",
    "CRM_MIEMBROS",
    "TRANS_VENTAS",
    "INV_STOCK_DIARIO",
    "POST_DEVOLUCIONES",
]


# ============================================================
# COLUMNAS DE TIPO FECHA
# ============================================================

COLUMNAS_FECHA = {
    "MSTR_PROVEEDORES": [],
    "MSTR_ARTICULOS": [
        "fec_alta",
    ],
    "MSTR_TIENDAS": [
        "fec_apertura",
    ],
    "CRM_MIEMBROS": [
        "fec_registro",
        "fec_ultima_compra",
    ],
    "TRANS_VENTAS": [
        "fec_trans",
    ],
    "INV_STOCK_DIARIO": [
        "fec_snapshot",
    ],
    "POST_DEVOLUCIONES": [
        "fec_devolucion",
    ],
}


# ============================================================
# BUSCAR ARCHIVO CSV
# ============================================================

def buscar_archivo(tabla):
    """
    Busca el archivo CSV correspondiente a una tabla
    en diferentes ubicaciones posibles.
    """

    posibles_rutas = [
        CARPETA_CSV / f"{tabla}.csv",
        Path("datos_registro_retail") / f"{tabla}.csv",
        Path("datos_retail/csv") / f"{tabla}.csv",
    ]

    for ruta in posibles_rutas:
        if ruta.exists():
            return ruta

    raise FileNotFoundError(
        f"No se encontró el archivo {tabla}.csv"
    )


# ============================================================
# LIMPIAR DATOS
# ============================================================

def limpiar_lote(df, tabla):
    """
    Limpia y transforma un lote de datos antes de enviarlo
    a Azure SQL.
    """

    # --------------------------------------------------------
    # Convertir columnas de fecha
    # --------------------------------------------------------

    for columna in COLUMNAS_FECHA[tabla]:

        if columna in df.columns:

            df[columna] = pd.to_datetime(
                df[columna],
                errors="coerce",
            ).dt.date

    # --------------------------------------------------------
    # Convertir hora de transacción a texto
    # --------------------------------------------------------

    if tabla == "TRANS_VENTAS":

        if "hra_trans" in df.columns:
            df["hra_trans"] = df["hra_trans"].astype(str)

    # --------------------------------------------------------
    # Convertir columna activo a 1 / 0
    # --------------------------------------------------------

    if "activo" in df.columns:

        df["activo"] = (
            df["activo"]
            .astype(str)
            .str.strip()
            .str.lower()
            .map(
                {
                    "true": 1,
                    "false": 0,
                    "1": 1,
                    "0": 0,
                }
            )
        )

    # --------------------------------------------------------
    # Convertir NaN y NaT a None
    # para que SQL Server los interprete como NULL
    # --------------------------------------------------------

    df = df.astype(object).where(
        pd.notna(df),
        None,
    )

    return df


# ============================================================
# VACIAR TABLAS
# ============================================================

def vaciar_tablas(conexion):
    """
    Elimina los datos existentes respetando el orden
    de las relaciones entre tablas.
    """

    orden = [
        "POST_DEVOLUCIONES",
        "INV_STOCK_DIARIO",
        "TRANS_VENTAS",
        "CRM_MIEMBROS",
        "MSTR_TIENDAS",
        "MSTR_ARTICULOS",
        "MSTR_PROVEEDORES",
    ]

    cursor = conexion.cursor()

    for tabla in orden:

        cursor.execute(
            f"DELETE FROM dbo.{tabla}"
        )

        conexion.commit()

        print(f"Tabla vaciada: {tabla}")

    cursor.close()


# ============================================================
# CARGAR UNA TABLA
# ============================================================

def cargar_tabla(conexion, tabla):
    """
    Lee el CSV por lotes y carga los registros
    en la tabla correspondiente de Azure SQL.
    """

    archivo = buscar_archivo(tabla)

    print("\n" + "=" * 65)
    print(f"Cargando: {tabla}")
    print(f"Archivo: {archivo.resolve()}")
    print("=" * 65)

    total = 0

    # --------------------------------------------------------
    # Leer CSV por lotes
    # --------------------------------------------------------

    lector = pd.read_csv(
        archivo,
        chunksize=10_000,
        encoding="utf-8-sig",
        low_memory=False,
    )

    cursor = conexion.cursor()

    # Mejora el rendimiento de inserción
    cursor.fast_executemany = True

    # --------------------------------------------------------
    # Procesar cada lote
    # --------------------------------------------------------

    for numero_lote, lote in enumerate(
        lector,
        start=1,
    ):

        lote = limpiar_lote(
            lote,
            tabla,
        )

        # ----------------------------------------------------
        # Obtener columnas del CSV
        # ----------------------------------------------------

        columnas = list(lote.columns)

        # ----------------------------------------------------
        # Crear nombres de columnas para SQL
        # ----------------------------------------------------

        columnas_sql = ", ".join(
            f"[{columna}]"
            for columna in columnas
        )

        # ----------------------------------------------------
        # Crear parámetros ?
        # ----------------------------------------------------

        parametros = ", ".join(
            "?"
            for _ in columnas
        )

        # ----------------------------------------------------
        # Crear INSERT dinámico
        # ----------------------------------------------------

        consulta = (
            f"INSERT INTO dbo.[{tabla}] "
            f"({columnas_sql}) "
            f"VALUES ({parametros})"
        )

        # ----------------------------------------------------
        # Convertir DataFrame a lista de tuplas
        # ----------------------------------------------------

        registros = [
            tuple(fila)
            for fila in lote.itertuples(
                index=False,
                name=None,
            )
        ]

        # ----------------------------------------------------
        # Insertar registros
        # ----------------------------------------------------

        cursor.executemany(
            consulta,
            registros,
        )

        conexion.commit()

        total += len(registros)

        print(
            f"{tabla}: "
            f"lote {numero_lote}, "
            f"total {total:,}"
        )

    cursor.close()

    print(
        f"{tabla}: carga finalizada con "
        f"{total:,} registros"
    )


# ============================================================
# MOSTRAR CONTEOS
# ============================================================

def mostrar_conteos(conexion):
    """
    Muestra la cantidad de registros existentes
    en cada tabla de Azure SQL.
    """

    consulta = """
        SELECT 'MSTR_PROVEEDORES', COUNT_BIG(*)
        FROM dbo.MSTR_PROVEEDORES

        UNION ALL

        SELECT 'MSTR_ARTICULOS', COUNT_BIG(*)
        FROM dbo.MSTR_ARTICULOS

        UNION ALL

        SELECT 'MSTR_TIENDAS', COUNT_BIG(*)
        FROM dbo.MSTR_TIENDAS

        UNION ALL

        SELECT 'CRM_MIEMBROS', COUNT_BIG(*)
        FROM dbo.CRM_MIEMBROS

        UNION ALL

        SELECT 'TRANS_VENTAS', COUNT_BIG(*)
        FROM dbo.TRANS_VENTAS

        UNION ALL

        SELECT 'INV_STOCK_DIARIO', COUNT_BIG(*)
        FROM dbo.INV_STOCK_DIARIO

        UNION ALL

        SELECT 'POST_DEVOLUCIONES', COUNT_BIG(*)
        FROM dbo.POST_DEVOLUCIONES;
    """

    cursor = conexion.cursor()

    cursor.execute(consulta)

    resultados = cursor.fetchall()

    total = 0

    print("\n" + "=" * 55)
    print("CONTEOS EN AZURE SQL")
    print("=" * 55)

    for tabla, registros in resultados:

        registros = int(registros)

        total += registros

        print(
            f"{tabla:<30}"
            f"{registros:>15,}"
        )

    print("-" * 55)

    print(
        f"{'TOTAL':<30}"
        f"{total:>15,}"
    )

    cursor.close()


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def main():

    try:

        # ----------------------------------------------------
        # Conectar con Azure SQL
        # ----------------------------------------------------

        conexion = pyodbc.connect(
            cadena_conexion
        )

        print("\nConexión correcta con Azure SQL")

        # ----------------------------------------------------
        # Preguntar si se deben eliminar datos anteriores
        # ----------------------------------------------------

        respuesta = input(
            "\n¿Deseas eliminar datos anteriores? "
            "Escribe SI: "
        ).strip().upper()

        if respuesta == "SI":

            print("\nEliminando datos anteriores...")

            vaciar_tablas(conexion)

        # ----------------------------------------------------
        # Cargar todas las tablas
        # ----------------------------------------------------

        for tabla in TABLAS:

            cargar_tabla(
                conexion,
                tabla,
            )

        # ----------------------------------------------------
        # Mostrar conteos finales
        # ----------------------------------------------------

        mostrar_conteos(conexion)

        # ----------------------------------------------------
        # Cerrar conexión
        # ----------------------------------------------------

        conexion.close()

        print(
            "\nProceso terminado correctamente."
        )

    except pyodbc.Error as error:

        print(
            "\nERROR DE AZURE SQL / PYODBC:"
        )

        print(error)

    except FileNotFoundError as error:

        print(
            "\nERROR DE ARCHIVO:"
        )

        print(error)

    except Exception as error:

        print(
            "\nERROR GENERAL:"
        )

        print(error)


# ============================================================
# EJECUTAR PROGRAMA
# ============================================================

if __name__ == "__main__":
    main()

