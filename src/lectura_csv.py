import pandas as pd
from pathlib import Path



#  Leer el fichero CSV
def main():
    # Localizar el archivo csv desde la ubicación del script.
    ruta_archivo = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "admisiones_historico.csv"
    )

    print(f"Archivo: {ruta_archivo}")
    df = pd.read_csv(ruta_archivo, encoding="utf-8-sig")



#  Mostrar los primeros registros
print("PRIMEROS CINCO REGISTROS")
print(df.head())

#  Consultar dimensiones
print("\nDIMENSIONES")
print("Filas:", df.shape[0])
print("Columnas:", df.shape[1])

#  Consultar los tipos de datos
print("\nTIPOS DE DATOS")
print(df.dtypes)

#  Consultar información general
print("\nINFORMACIÓN GENERAL")
df.info()

#  Seleccionar dos columnas
print("\nEPISODIOS Y MOTIVOS")
print(df[["id_episodio", "motivo_consulta"]].head())

#  Seleccionar las primeras cinco filas
print("\nPRIMERAS CINCO FILAS")
print(df.iloc[0:5])

#  Convertir la frecuencia cardíaca a números
df["frecuencia_cardiaca"] = pd.to_numeric(
    df["frecuencia_cardiaca"],
    errors="coerce"
)

#  Filtrar frecuencias cardíacas superiores a 100
filtro = df["frecuencia_cardiaca"] > 100

resultado = df.loc[
    filtro,
    ["id_episodio", "frecuencia_cardiaca"]
]

print("\nFRECUENCIAS CARDÍACAS SUPERIORES A 100")
print(resultado.head(10))
