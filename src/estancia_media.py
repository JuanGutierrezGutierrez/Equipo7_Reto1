"""
estancia_media.py
-----------------
Calcula el tiempo medio de estancia (en minutos) por categoria de triaje
y guarda el resultado en el archivo data/estancia_media_por_categoria.csv

Como se usa (desde la carpeta src):
    python estancia_media.py
"""
import csv
from pathlib import Path

from pymongo import MongoClient

# ---------------------------------------------------------------------------
# 1. Datos de conexion a MongoDB
# ---------------------------------------------------------------------------
USUARIO = "root"
PASSWORD = "secret"   # <- escribe aqui la contraseña del usuario root
SERVIDOR = "mongo"           # nombre del servicio de Mongo en docker-compose

# El archivo de resultado se guarda en la carpeta data (al lado de src)
CARPETA_DATA = Path(__file__).resolve().parent.parent / "data"
ARCHIVO_SALIDA = CARPETA_DATA / "estancia_media_por_categoria.csv"

# ---------------------------------------------------------------------------
# 2. Conectar con la base de datos y elegir la coleccion
# ---------------------------------------------------------------------------
cliente = MongoClient(
    SERVIDOR, 27017,
    username=USUARIO,
    password=PASSWORD,
    authSource="admin",
)
coleccion = cliente["urgencias_medicas"]["episodios_urgencias"]

# ---------------------------------------------------------------------------
# 3. La consulta (se hace por pasos, uno detras de otro)
# ---------------------------------------------------------------------------
consulta = [
    # Paso 1: quedarnos solo con los episodios que tienen hora de llegada,
    # hora de alta y categoria. Si falta alguna, no se puede calcular la estancia.
    {"$match": {
        "timestamp_llegada": {"$type": "date"},
        "timestamp_alta": {"$type": "date"},
        "triaje_manchester.categoria_patologia": {"$type": "string"},
    }},

    # Paso 2: calcular la estancia de cada episodio en minutos
    # (alta menos llegada da milisegundos; se divide entre 60000 para pasar a minutos)
    {"$addFields": {
        "estancia_min": {
            "$divide": [
                {"$subtract": ["$timestamp_alta", "$timestamp_llegada"]},
                60000,
            ]
        }
    }},

    # Paso 3: descartar las estancias que no tienen sentido (cero o negativas)
    {"$match": {"estancia_min": {"$gt": 0}}},

    # Paso 4: agrupar por categoria, calcular la media y contar los episodios
    {"$group": {
        "_id": {"$toLower": {"$trim": {"input": "$triaje_manchester.categoria_patologia"}}},
        "estancia_media_min": {"$avg": "$estancia_min"},
        "episodios": {"$sum": 1},
    }},

    # Paso 5: dejar las columnas con buen nombre y la media con un decimal
    {"$project": {
        "_id": 0,
        "categoria": "$_id",
        "estancia_media_min": {"$round": ["$estancia_media_min", 1]},
        "episodios": 1,
    }},

    # Paso 6: ordenar de mayor a menor estancia media
    {"$sort": {"estancia_media_min": -1}},
]

resultado = list(coleccion.aggregate(consulta))
cliente.close()

# ---------------------------------------------------------------------------
# 4. Guardar el resultado en un archivo CSV
# ---------------------------------------------------------------------------
CARPETA_DATA.mkdir(exist_ok=True)

with open(ARCHIVO_SALIDA, "w", newline="", encoding="utf-8") as archivo:
    escritor = csv.writer(archivo)
    escritor.writerow(["categoria", "estancia_media_min", "episodios"])
    for fila in resultado:
        escritor.writerow([fila["categoria"], fila["estancia_media_min"], fila["episodios"]])

# ---------------------------------------------------------------------------
# 5. Mostrar el resultado por pantalla
# ---------------------------------------------------------------------------
print("Estancia media por categoria de triaje (minutos)\n")
for fila in resultado:
    print(f"{fila['categoria']:<16} {fila['estancia_media_min']:>7}  ({fila['episodios']} episodios)")

print(f"\nResultado guardado en: {ARCHIVO_SALIDA}")