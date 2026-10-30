import requests
import pandas as pd
import time

# Endpoint de la API de urgencias
URL = "http://10.201.59.248:28000/api/v1/urgencias/novedades"

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
        # procesar_datos(df)

    except Exception as e:
        print(f"Error: {e}")

    # Espera 5 segundos antes de la siguiente consulta
    time.sleep(5)