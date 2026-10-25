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