from pathlib import Path

import pandas as pd
from pymongo import MongoClient
import json


def main():

    CSV_LIMPIO = Path(__file__).resolve().parent.parent / "data" / "admisiones_historico_limpio.csv"
    JSON_LIMPIO = Path(__file__).resolve().parent.parent / "data" / "partes_clinicos_limpio.json"

    connection_string = "mongodb://root:secret@mongo:27017/?authSource=admin" 
    client = MongoClient(connection_string)

    
    db = client["urgencias_medicas"]
    collection = db["episodios_urgencias"]


    df_admisiones = pd.read_csv(CSV_LIMPIO)

    with open(JSON_LIMPIO, "r", encoding="utf-8") as f:
        partes_clinicos = json.load(f)
    df_partes = pd.DataFrame(partes_clinicos)


    df_unido = pd.merge(df_admisiones, df_partes, on="id_episodio", how="inner", suffixes=("", "_dup"))
    registros = df_unido.to_dict(orient="records")

    # 5. Insertar los documentos combinados en MongoDB
    if registros:
      # Opcional: limpiar la colección antes de realizar una carga limpia
      collection.delete_many({})

      resultado = collection.insert_many(registros)
    else:
      print("No se encontraron coincidencias para unir ambos conjuntos de datos.")

    
    client.close()


if __name__ == "__main__":
    main()
