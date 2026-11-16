# EQUIPO 7 -- RETO 1:Sistema de triaje y trazabilidad de urgencias hospitalarias

## DESCRIPCIÓN:

Es un proyecto de procesamiento y gestión de información de urgencias hospitalariasdonde se combina la preparación de datos históricos de admisiones y partes clínicos con la recepción de novedades de una API. Se utiliza MongoDB para almacenar episodios de urgencias y Redis para gestionar temporalmente la ocupación de boxes y la cola de espera.

El repositorio incluye también consultas para analizar la estancia media por categoría de patología.

## OBJETIVOS

- Limpiar y normalizar registros históricos en formatos CSV y JSON.
- Integrar las admisiones y los partes clínicos mediante el identificador del episodio.
- Guardar los episodios integrados en MongoDB.
- Procesar nuevos ingresos y altas recibidos desde una API, o desde un archivo de ejemplo sin conexión.
- Administrar cinco boxes y una cola de espera con Redis.
- Obtener indicadores de duración de las estancias mediante agregaciones de MongoDB.

## TECNOLOGÍAS DEL PROYECTO

| Tecnología | Función |
| --- | --- |
| Python 3.12 | Ejecución de los scripts en el contenedor Python |
| Pandas | Lectura, limpieza, transformación y combinación de datos |
| Requests | Consultas HTTP a la API de urgencias |
| PyMongo / MongoDB 6 | Almacenamiento y consulta de episodios |
| Redis 7.2 | Estado de boxes, cola de espera y datos temporales |
| Docker Compose | Despliegue coordinado de los servicios |
| Mongo Express | Interfaz web para inspeccionar MongoDB |

Las versiones concretas de las bibliotecas Python se encuentran en `requirements.txt`.

## Funcionamiento general

Carga histórica: `admisiones_historico.csv` y `partes_clinicos.json` → scripts de limpieza → archivos limpios → unión por `id_episodio` → colección `urgencias_medicas.episodios_urgencias` en MongoDB.

API de urgencias (o archivo JSON de prueba) → procesamiento de ingresos y altas → gestión de boxes y cola de espera en Redis → almacenamiento de episodios en MongoDB al procesar las altas.

La implementación utiliza cinco boxes (`box:1` a `box:5`). La cola de espera se almacena en la clave ordenada `urgencias:cola_espera`; la asignación de pacientes utiliza `ZPOPMIN` para extraer el siguiente episodio según su puntuación de prioridad.

## ESTRUCTURA DEL PROYECO

```text
Equipo7_Reto1/ 
├── data/                         # Datos de entrada, datos limpios y resultados
├── docker/
│   ├── docker-compose.yml        # MongoDB, Mongo Express, Python y Redis
│   ├── redis.conf                # Configuración de Redis
│   └── .env                      # Variables locales de configuración
├── src/
│   ├── menu.py                  # Menú interactivo para ejecutar las operaciones
│   ├── chequea_conexion.py       # Prueba de conexión a MongoDB y Redis
│   ├── lectura_csv.py            # Exploración del CSV de admisiones
│   ├── limpiar_admisiones.py     # Limpieza de admisiones históricas
│   ├── limpiar_partes_clinicos.py# Limpieza de partes clínicos JSON
│   ├── insercion_historica_mongo.py # Integración e inserción histórica
│   ├── lectura_api.py            # Lectura periódica de novedades de la API
│   ├── lectura_api_offline.py    # Procesamiento de novedades de ejemplo
│   ├── pipelines_consulta.py     # Consulta de estancia media
│   └── estancia_media.py         # Exportación de estancia media a CSV
├── requirements.txt
└── README.md
```


## PREPARACIÓN DEL ENTORNO.

Requisitos: Docker con Docker Compose y acceso a una terminal.

1. Clonar o descargar el repositorio y situarse en la carpeta `docker`.
2. Configurar las variables necesarias en `docker/.env` para MongoDB y Mongo Express. No publicar contraseñas reales en Git.
3. Crear la red externa requerida por el archivo Compose, si todavía no existe:

   ```bash
   docker network create shared-network
   ```

4. Levantar los servicios:

   ```bash
   docker compose up -d
   ```

5. Comprobar que se han iniciado:

   ```bash
   docker compose ps
   ```

El contenedor de Python instala las dependencias de `requirements.txt` al arrancar. Mongo Express se publica, por defecto, en `http://localhost:8081`, sujeto a la configuración local.

**Importante:** varios scripts usan directamente las credenciales de ejemplo `root` / `secret`. Para ejecutarlos sin modificarlos, la configuración de MongoDB debe ser coherente con esas credenciales. En un despliegue real deben sustituirse por variables de entorno y evitarse las contraseñas incrustadas en el código.

## Menú interactivo (`src/menu.py`)

El proyecto incluye un menú de consola que reúne las operaciones principales. Se ejecuta **en el equipo anfitrión**, desde la carpeta `src/`, y utiliza comandos `docker` para lanzar los scripts dentro del contenedor `python_container`.

Desde la raíz del repositorio:

```bash
cd src
python3 menu.py
```

En Windows, si Python se invoca mediante `python` en lugar de `python3`, utilizar `python menu.py`. El menú está preparado principalmente para una terminal tipo Linux: emplea el comando `clear` para limpiar la pantalla.

| Opción | Acción | Resultado o comportamiento |
| --- | --- | --- |
| 1 | Levantar contenedores | Ejecuta `docker compose up -d` desde `docker/`. |
| 2 | Comprobar MongoDB y Redis | Ejecuta `chequea_conexion.py`. |
| 3 | Limpiar partes clínicos | Ejecuta `limpiar_partes_clinicos.py` y genera `partes_clinicos_limpio.json`. |
| 4 | Limpiar admisiones | Ejecuta `limpiar_admisiones.py` y genera `admisiones_historico_limpio.csv`. |
| 5 | Carga histórica en MongoDB | Ejecuta `insercion_historica_mongo.py`. **Reemplaza los documentos existentes en la colección de episodios**. |
| 6 | Calcular estancia media | Ejecuta `estancia_media.py` y genera `estancia_media_por_categoria.csv`. |
| 7 | Leer API en tiempo real | Ejecuta `lectura_api.py`; detener con `Ctrl+C`. Requiere acceso al servidor privado de la API. |
| 8 | Leer datos sin conexión | Ejecuta `lectura_api_offline.py` con un JSON de ejemplo, sin acceder a la API real. |
| 0 | Salir | Finaliza el menú. |

### Orden recomendado para la primera ejecución

1. Seleccionar 1 para iniciar los servicios Docker.
2. Seleccionar 2 para comprobar las conexiones.
3. Seleccionar 3 y después 4 para preparar los dos conjuntos de datos históricos.
4. Seleccionar 5 para insertar los registros limpios en MongoDB.
5. Seleccionar 6 para calcular y exportar la estancia media.
6. Seleccionar 8 para probar las novedades sin conexión o 7 si la API real está disponible.
7. Seleccionar 0 para terminar.

No es necesario repetir toda la carga histórica cada vez que se consulta la API. Las opciones 2 a 8 requieren que el contenedor `python_container` esté iniciado. Los comandos del menú dependen de ejecutarlo desde `src/`, tal como indica el propio script.

## Ejecución paso a paso (alternativa manual)

Si se prefiere no utilizar el menú, los siguientes comandos permiten ejecutar cada fase manualmente desde la carpeta `docker/`.

### 1. Comprobar las conexiones

```bash
docker compose exec python python src/chequea_conexion.py
```

El script prueba operaciones de escritura, lectura y borrado tanto en MongoDB como en Redis. Si todo funciona, muestra un mensaje final de comprobación correcta.

### 2. Limpiar los datos históricos

```bash
docker compose exec python python src/limpiar_admisiones.py
docker compose exec python python src/limpiar_partes_clinicos.py
```

- `limpiar_admisiones.py` normaliza registros del CSV, comprueba identificadores, fechas y campos, y genera `data/admisiones_historico_limpio.csv` y un archivo de rechazos para auditoría.
- `limpiar_partes_clinicos.py` elimina duplicados, normaliza categorías y valores, trata datos faltantes y reconstruye el JSON anidado sin modificar el archivo original. Genera `data/partes_clinicos_limpio.json`.

### 3. Cargar los datos históricos en MongoDB

```bash
docker compose exec python python src/insercion_historica_mongo.py
```

Este script une los archivos limpios mediante `id_episodio` y carga el resultado en `urgencias_medicas.episodios_urgencias`.

### 4. Procesar novedades

Opción A: datos de ejemplo sin API externa*

```bash
docker compose exec python python src/lectura_api_offline.py
```

Lee `data/ejemplo_offline_api.json` y procesa los registros previstos en el script. Esta opción permite probar la lógica sin depender del servidor de la API.

Opción B: API en funcionamiento

```bash
docker compose exec python python src/lectura_api.py
```

Consulta periódicamente el endpoint de urgencias definido en el código, procesa `nuevos_ingresos` y `pacientes_alta`, y espera cinco segundos entre consultas. El endpoint configurado utiliza una dirección de red privada, por lo que **solo funcionará si ese servidor es accesible desde el entorno de ejecución**. Para detener el proceso continuo, usar `Ctrl+C`.

### 5. Consultar la estancia media

```bash
docker compose exec python python src/pipelines_consulta.py
docker compose exec python python src/estancia_media.py
```

El primer script muestra un DataFrame con resultados de una agregación. El segundo calcula la estancia media en minutos por categoría de patología y genera `data/estancia_media_por_categoria.csv`, con las columnas `categoria`, `estancia_media_min` y `episodios`.

## Archivos de datos principales

| Archivo | Utilidad |
| --- | --- |
| `data/admisiones_historico.csv` | Admisiones originales |
| `data/partes_clinicos.json` | Información clínica original |
| `data/admisiones_historico_limpio.csv` | Admisiones normalizadas |
| `data/partes_clinicos_limpio.json` | Partes clínicos normalizados |
| `data/ejemplo_offline_api.json` | Datos para la prueba sin conexión |
| `data/estancia_media_por_categoria.csv` | Resultado del análisis de estancias |

## Consideraciones y limitaciones

- El acceso a la API depende de la disponibilidad de un servidor privado.
- El número de boxes está fijado en cinco en los scripts de procesamiento.
- El menú interactivo presupone una terminal compatible con `clear` y un Docker accesible desde el equipo anfitrión.
- Los scripts contienen credenciales de ejemplo incrustadas que conviene externalizar.
- La carga histórica reemplaza el contenido previo de la colección de episodios.
- Los datos clínicos requieren especial cuidado: usar datos ficticios o debidamente anonimizados y no publicar información identificable de pacientes.
- El directorio `docker/mongo_data/` contiene datos persistentes locales de MongoDB y no debería incluirse en el control de versiones.

## equipo

Desarrollado por: 

1. Jose María Honrado 
2. Juan Gutierrez Gutierrez 
3. Pablo Mendoza Mayo
