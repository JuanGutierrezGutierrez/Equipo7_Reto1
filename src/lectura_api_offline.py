import pandas as pd
import time
import requests
import redis
import json
from pathlib import Path
from datetime import datetime, timezone
from pymongo import MongoClient


def inicializar_boxes():
    """Asegura que los 5 boxes existan en Redis como Hashes."""
    for i in range(1, TOTAL_BOXES + 1):
        box_key = f"box:{i}"
        if not r.exists(box_key):
            r.hset(box_key, mapping={"estado": "libre", "id_episodio": "", "hora_entrada": 0.0})

def obtener_boxes_libres():
    """Devuelve una lista con los identificadores de los boxes libres."""
    libres = []
    for i in range(1, TOTAL_BOXES + 1):
        box_key = f"box:{i}"
        if r.hget(box_key, "estado") == "libre":
            libres.append(box_key)
    return libres

def asignar_box_a_paciente(box_key, id_episodio):
    """Ocupa un box con un paciente específico."""
    r.hset(box_key, mapping={
        "estado": "ocupado",
        "id_episodio": id_episodio,
        "hora_entrada": time.time()
    })

def liberar_box_por_episodio(id_episodio):
    """Libera el box que esté ocupado por el episodio dado."""
    for i in range(1, TOTAL_BOXES + 1):
        box_key = f"box:{i}"
        if r.hget(box_key, "id_episodio") == id_episodio:
            r.hset(box_key, mapping={"estado": "libre", "id_episodio": "", "hora_entrada": 0.0})
            return box_key
    return None

def procesar_novedades(datos):
    try:
        # 1. Gestionar NUEVOS INGRESOS
        nuevos_ingresos = datos.get("nuevos_ingresos", [])
        for paciente in nuevos_ingresos:
            id_episodio = paciente["id_episodio"]
            timestamp_llegada = paciente["datos_admision"]["timestamp_llegada"]
            tiempo_max_espera_min = paciente["datos_triaje"]["tiempo_max_espera_min"]
            
            # Cálculo del score EDF (Deadline absoluto en segundos)
            score_edf = timestamp_llegada + (tiempo_max_espera_min * 60)
            
            # Guardar el JSON completo en Redis temporalmente
            r.set(f"paciente:{id_episodio}", json.dumps(paciente))
            
            # Añadir a la cola de espera de Redis (Sorted Set)
            r.zadd(COLA_ESPERA_KEY, {id_episodio: score_edf})
            print(f"[INGRESO] Paciente {id_episodio} añadido a la cola con EDF score: {score_edf}")

        # 2. Gestionar PACIENTES DE ALTA
        pacientes_alta = datos.get("pacientes_alta", [])
        for alta in pacientes_alta:
            id_episodio = alta["id_episodio"]
            timestamp_alta = alta["timestamp_alta"]
            fecha_hora_alta = alta["fecha_hora_alta"]
            destino_alta = alta["destino_alta"]
            
            # Localizar y liberar el box del paciente dado de alta
            box_liberado = liberar_box_por_episodio(id_episodio)
            if box_liberado:
                print(f"[ALTA] Paciente {id_episodio} liberó el {box_liberado}")
            
            # Recuperar datos clínicos temporales desde Redis
            paciente_data_str = r.get(f"paciente:{id_episodio}")
            
            if paciente_data_str:
                paciente_original = json.loads(paciente_data_str)
                
                # --- APLANAR ESTRUCTURA PARA MONGODB ---
                # Creamos un documento plano combinando todas las características al mismo nivel
                paciente_a_subir = {
                    "id_episodio": paciente_original.get("id_episodio"),
                    "sip_paciente": paciente_original.get("datos_admision", {}).get("sip_paciente"),
                    "timestamp_llegada": datetime.fromtimestamp(paciente_original.get("datos_admision", {}).get("timestamp_llegada"), tz=timezone.utc),
                    "timestamp_alta": datetime.fromtimestamp(timestamp_alta, tz=timezone.utc),
                    "motivo_consulta": paciente_original.get("datos_admision", {}).get("motivo_consulta"),
                    "frecuencia_cardiaca": paciente_original.get("datos_triaje", {}).get("constantes", {}).get("frecuencia_cardiaca"),
                    "tension_arterial": paciente_original.get("datos_triaje").get("constantes", {}).get("tension_arterial"),
                    "destino_alta": destino_alta,
                    "id_parte": paciente_original.get("id_episodio").replace("EP", "CLIN", 1),
                    "edad": paciente_original.get("datos_admision", {}).get("edad"),
                    "antecedentes": paciente_original.get("datos_triaje", {}).get("antecedentes"),
                    "alergias": paciente_original.get("datos_triaje", {}).get("alergias"),
                    "notas_triaje": paciente_original.get("datos_triaje", {}).get("notas_triaje"),
                    "triaje_manchester": {
                        "nivel": paciente_original.get("datos_triaje", {}).get("nivel_manchester"),
                        "color": paciente_original.get("datos_triaje", {}).get("color"),
                        "categoria_patologia": paciente_original.get("datos_triaje", {}).get("categoria_patologia"),
                        "tiempo_max_espera_min": paciente_original.get("datos_triaje", {}).get("tiempo_max_espera_min"),
                    },
                    "constantes": paciente_original.get("datos_triaje", {}).get("constantes"),
                    "modulo_traumatologia": paciente_original.get("datos_triaje", {}).get("modulo_traumatologia"),
                    "modulo_digestivo": paciente_original.get("datos_triaje", {}).get("modulo_digestivo"),
                    "modulo_cardiologia": paciente_original.get("datos_triaje", {}).get("modulo_cardiologia"),
                    "modulo_infeccioso": paciente_original.get("datos_triaje", {}).get("modulo_infeccioso"),
                    "modulo_neurologia": paciente_original.get("datos_triaje", {}).get("modulo_neurologia"),
                    "modulo_urologia": paciente_original.get("datos_triaje", {}).get("modulo_urologia"),
                    "modulo_psiquiatria": paciente_original.get("datos_triaje", {}).get("modulo_psiquiatria"),
                    "modulo_respiratorio": paciente_original.get("datos_triaje", {}).get("modulo_respiratorio"),
                    "modulo_pediatria": paciente_original.get("datos_triaje", {}).get("modulo_pediatria")
                }
                
                
                # Insertar el documento plano completo en MongoDB
                coleccion_episodios.insert_one(paciente_a_subir)
                print(f"[MONGODB] Episodio aplanado {id_episodio} guardado en MongoDB.")
                
                # Borrar por completo de Redis los datos temporales
                r.delete(f"paciente:{id_episodio}")
            
            # Eliminar de la cola de espera si seguía presente
            r.zrem(COLA_ESPERA_KEY, id_episodio)

        # 3. ASIGNACIÓN DE BOXES LIBRES USANDO EDF (ZPOPMIN)
        boxes_libres = obtener_boxes_libres()
        while boxes_libres:
            siguiente_paciente = r.zpopmin(COLA_ESPERA_KEY, count=1)
            
            if not siguiente_paciente:
                break
                
            id_episodio = siguiente_paciente[0][0]
            box_asignado = boxes_libres.pop(0)
            
            asignar_box_a_paciente(box_asignado, id_episodio)
            print(f"[ASIGNACIÓN] Paciente prioritario {id_episodio} asignado al {box_asignado}")

    except Exception as e:
        print(f"[EXCEPCIÓN] Ocurrió un error en el ciclo de proceso: {e}")


def Procesar_datos():
    df = pd.read_json(RUTA_ORIGEN)
    datos = df.loc[0, "respuesta"]
    datos_ni = datos['nuevos_ingresos']
    datos_pa = datos['pacientes_alta']

    for i in range(48):
        procesar_novedades(df.loc[i, "respuesta"])
    


# Conexión a Redis
r = redis.Redis(host='redis', port=6379, decode_responses=True)
# Constantes del sistema
TOTAL_BOXES = 5
COLA_ESPERA_KEY = "urgencias:cola_espera"

# Conexión a MongoDB 
connection_string = "mongodb://root:secret@mongo:27017/?authSource=admin" 
mongo_client = MongoClient(connection_string)
db = mongo_client["urgencias_medicas"]
coleccion_episodios = db["episodios_urgencias"]

BASE = Path(__file__).resolve().parent.parent
RUTA_ORIGEN = BASE / "data" / "ejemplo_offline_api.json"

Procesar_datos()

