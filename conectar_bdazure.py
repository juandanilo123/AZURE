from getpass import getpass
import pyodbc

SERVIDOR = "sql-retail-data.database.windows.net"
BASE_DATOS = "databasecomercio"
USUARIO = "databaseadmin"

password = getpass("Contraseña de Azure SQL: ")

cadena_conexion = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER=tcp:{SERVIDOR},1433;"
    f"DATABASE={BASE_DATOS};"
    f"UID={USUARIO};"
    f"PWD={password};"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)

try:
    conexion = pyodbc.connect(cadena_conexion)

    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            DB_NAME() AS base_actual,
            GETDATE() AS fecha_servidor
    """)

    base_actual, fecha_servidor = cursor.fetchone()

    print("Conexión exitosa")
    print("Base:", base_actual)
    print("Fecha del servidor:", fecha_servidor)

    cursor.close()
    conexion.close()

except pyodbc.Error as error:
    print("Error al conectar con Azure SQL:")
    print(error)