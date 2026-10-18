
"""
Lectura inicial de partes_clinicos.json mediante pandas.
Inspecciona el número de registros y la estructura de los datos.
"""

from pathlib import Path

import pandas as pd


def main():
    # Localizar el archivo JSON desde la ubicación del script.
    ruta_archivo = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "partes_clinicos.json"
    )

    print(f"Archivo: {ruta_archivo}")

    # Leer el JSON y cargar los registros en un DataFrame.
    df = pd.read_json(ruta_archivo, encoding="utf-8-sig")

    print(f"\nNúmero de registros: {len(df)}")
    print(f"Número de columnas: {len(df.columns)}")

    # Mostrar las columnas y sus tipos de datos.
    print("\nColumnas del DataFrame:")
    print(df.dtypes.to_string())

    # Mostrar los primeros registros.
    print("\nPrimeros 5 registros:")
    print(df.head().to_string())

    # Mostrar valores nulos por columna.
    print("\nValores nulos por columna:")
    print(df.isna().sum().to_string())


if __name__ == "__main__":
    main()
