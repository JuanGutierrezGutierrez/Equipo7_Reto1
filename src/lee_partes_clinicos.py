
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

    # Inspeccionar los campos internos de las constantes.
    print("\nCampos de constantes:")
    campos_constantes = set()

    for constantes in df["constantes"].dropna():
        if isinstance(constantes, dict):
            campos_constantes.update(constantes.keys())

    print(sorted(campos_constantes))

    # 1. Resumen estructural: tipos asignados y uso de memoria real
    print()
    print("********************** USO DE MEMORIA **********************")
    df.info(memory_usage="deep")
    
    # 2. Resumen estadístico de variables numéricas y categóricas
    print()
    print("********************** RESUMEN ESTADÍSTICO **********************")
    print(df.describe(include="all"))
    
    # 3. Diagnóstico exhaustivo de valores ausentes (conteo y porcentaje relativo)
    print()
    print("********************** NULOS **********************")
    nulos_resumen = pd.DataFrame(
            {
                "conteo_nulos": df.isna().sum(),
                "porcentaje_nulos": (df.isna().mean() * 100).round(2),
            }
        ).sort_values(by="porcentaje_nulos", ascending=False)
    
    print(nulos_resumen)    

if __name__ == "__main__":
    main()
