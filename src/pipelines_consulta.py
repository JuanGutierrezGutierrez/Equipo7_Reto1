import pandas as pd
from pymongo import MongoClient

def main():
    connection_string = "mongodb://root:secret@mongo:27017/?authSource=admin" 
    client = MongoClient(connection_string)

    
    db = client["urgencias_medicas"]
    collection = db["episodios_urgencias"]


    # 2. Definir el pipeline de agregación (por ejemplo, el tiempo medio de estancia)
    pipeline = [
        {"$match": {"timestamp_alta": {"$ne": None}, "timestamp_llegada": {"$ne": None}}},
        {
            "$project": {
                "categoria_patologia": "$triaje_manchester.categoria_patologia",
                "estancia_minutos": {
                    "$divide": [
                        {
                            "$subtract": [
                                {"$toDate": "$timestamp_alta"},
                                {"$toDate": "$timestamp_llegada"},
                            ]
                        },
                        60000,
                    ]
                },
            }
        },
        {
            "$group": {
                "_id": "$categoria_patologia",
                "tiempo_medio_estancia_min": {"$avg": "$estancia_minutos"},
                "total_episodios": {"$sum": 1},
            }
        },
        {"$sort": {"tiempo_medio_estancia_min": -1}},
    ]

    # 3. Ejecutar la agregación
    cursor = collection.aggregate(pipeline)

    # Opción A: Convertir el resultado directamente a un DataFrame de Pandas (Recomendado)
    df_resultado = pd.DataFrame(list(cursor))
    print("--- Resultados en DataFrame ---")
    print(df_resultado)

    

    client.close()

if __name__ == "__main__":
    main()
