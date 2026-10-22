## Cómo reproducir la prueba de conectividad

1. Clonar el repositorio.
2. Desde `docker/`, levantar los servicios:
   docker compose up -d
   (el contenedor `python` instalará automáticamente las dependencias
    declaradas en `requirements.txt`)
3. Ejecutar el script de comprobación:
   docker compose exec python python src/chequea_conexion.py
4. Salida esperada: mensajes de escritura, lectura y borrado en MongoDB
   y Redis, terminando con "Todo correcto".

Si en el futuro se añade una librería nueva a `requirements.txt`,
basta con recrear el contenedor de Python:
   docker compose up -d --force-recreate python

El script de limpieza de json "limpiar_limpiar_partes.clinicos.py" hace seis cosas en orden:

Leer el JSON original sin tocarlo.

Aplanarlo a tabla con json_normalize, para poder limpiarlo con pandas.

Limpiar la tabla con seis reglas: quitar duplicados (con una copia serializada porque hay listas que no se pueden hashear), normalizar textos categóricos, unificar alergias y antecedentes a lista, convertir edad y constantes a número, aplicar reglas de dominio (valores fisiológicamente imposibles → nulo), e imputar solo edad con la mediana.

Reconstruir la anidación original ('a.b.c' → {'a':{'b':{'c':...}}}), omitiendo los nulos.

Guardar el fichero limpio sin modificar el original.

Verificar que la estructura de salida es compatible con la de entrada: misma lista de objetos, mismas claves de primer nivel, subdocumentos como diccionario, listas como listas, y que el JSON se recarga sin errores.

