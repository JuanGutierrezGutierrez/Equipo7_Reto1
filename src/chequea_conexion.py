# ============================================================
# Script para comprobar que Python puede hablar con MongoDB y Redis
# desde dentro de la red de Docker.
# ============================================================

from pymongo import MongoClient   # Para hablar con MongoDB
import redis                      # Para hablar con Redis


# ============ PARTE 1: MONGODB ============

print("== MongoDB ==")

# Nos conectamos a MongoDB con las credenciales del archivo .env:
#   usuario: root
#   contraseña: secret
#   host: mongo  (nombre del servicio en docker-compose.yml)
#   authSource=admin  (el usuario root vive en la BD "admin")
cliente_mongo = MongoClient("mongodb://root:secret@mongo:27017/?authSource=admin")

# Probando el ping para Mongo
cliente_mongo.admin.command("ping")
print("  Ping de MongoDB: correcto")

# Elegimos la base de datos "test" y la colección "prueba".
db = cliente_mongo["test"]
coleccion = db["prueba"]

# Escribimos un documento de prueba.
coleccion.insert_one({"mensaje": "hola mongo"})
print("  Escrito en Mongo: hola mongo")

# Lo leemos de vuelta.
documento = coleccion.find_one({"mensaje": "hola mongo"})
print("  Leído de Mongo:", documento["mensaje"])

# Lo borramos para no dejar basura.
coleccion.delete_one({"mensaje": "hola mongo"})
print("  Borrado de Mongo")


# ============ PARTE 2: REDIS ============

print("== Redis ==")

# Nos conectamos a Redis (sin contraseña, según tu redis.conf).
cliente_redis = redis.Redis(host="redis", port=6379)

#Probando el ping para Redis
if cliente_redis.ping():
    print("  Ping de Redis: correcto")

# Escribimos un dato de prueba.
cliente_redis.set("prueba", "hola redis")
print("  Escrito en Redis: hola redis")

# Lo leemos de vuelta. Redis devuelve bytes, así que .decode().
valor = cliente_redis.get("prueba").decode()
print("  Leído de Redis:", valor)

# Lo borramos.
cliente_redis.delete("prueba")
print("  Borrado de Redis")


# ============ FIN ============

print("Todo correcto: Python habla con Mongo y con Redis.")