import requests
import pandas as pd
import time

# Endpoint de la API de urgencias
URL = "http://10.201.59.248:28000/api/v1/urgencias/novedades"
# procesar_datos(df)
def Procesar_datos(df):
    pd.set_option('display.max_rows', None) 
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
 
    datos = df.loc[0, "respuesta"]
    datos_ni = datos['nuevos_ingresos']
    datos_pa = datos['pacientes_alta']
    print(datos_ni) 
    print(datos_pa)
    return datos_ni, datos_pa


while True:
    try:
        # Realiza la petición a la API
        respuesta = requests.get(URL)
        respuesta.raise_for_status()

        # Convierte la respuesta JSON a un diccionario Python
        
        datos = respuesta.json()

        # Crea un DataFrame con una única fila.
        # La columna "respuesta" contiene toda la información
        # devuelta por la API en esta consulta.
        df = pd.DataFrame([{
            "timestamp": pd.Timestamp.now(),
            "respuesta": datos
        }])

        print(df)

        # Aquí se llamaría a la función de PABLO
        Procesar_datos(df)
        print(df['respuesta'].to_string())

    except Exception as e:
        print(f"Error: {e}")

    # Espera 5 segundos antes de la siguiente consulta
    time.sleep(5)