"""
LIMPIEZA DE partes_clinicos.json
--------------------------------
Objetivo:
    Leer el fichero original, limpiarlo y guardarlo como
    'partes_clinicos_limpio.json' SIN modificar el original.

Requisito clave:
    El fichero de salida debe tener la MISMA ESTRUCTURA que el original
    (una lista de objetos con subdocumentos anidados) para poder unirlo
    después con el fichero de otro compañero.

Estrategia:
    1. Leer el JSON original.
    2. Aplanarlo a una tabla (DataFrame) para poder limpiarlo cómodamente.
    3. Limpiar la tabla (duplicados, textos, tipos, valores imposibles, nulos).
    4. Reconstruir la estructura anidada original.
    5. Guardar el JSON limpio.
    6. Verificar que la estructura de salida es compatible con la de entrada.
"""

import json
from pathlib import Path

import pandas as pd

# ============================================================
# 0. RUTAS DE LOS FICHEROS
# ============================================================
# BASE es la carpeta del proyecto (dos niveles arriba de este script).
BASE = Path(__file__).resolve().parent.parent
RUTA_ORIGEN = BASE / "data" / "partes_clinicos.json"
RUTA_DESTINO = BASE / "data" / "partes_clinicos_limpio.json"


# ============================================================
# 1. LEER EL JSON ORIGINAL
# ============================================================
def leer_json(ruta: Path) -> list:
    """Devuelve la lista de partes clínicos del fichero original."""
    with open(ruta, encoding="utf-8-sig") as f:
        return json.load(f)


# ============================================================
# 2. UTILIDADES
# ============================================================
def normalizar_a_lista(valor):
    """
    Convierte cualquier valor a una lista de strings en minúsculas.
    Se usa para 'alergias' y 'antecedentes', que en el fichero original
    aparecen de formas muy distintas:
        - como lista:  ["leche", "metamizol"]
        - como string: "polen"
        - como nulo:   null
    Si el valor era nulo, devolvemos lista vacía (información válida:
    "sin alergias registradas").
    """
    if valor is None:
        return []
    if isinstance(valor, list):
        return [str(x).strip().lower() for x in valor if str(x).strip()]
    if isinstance(valor, str):
        texto = valor.strip().lower()
        return [texto] if texto else []
    return []


def copia_serializada(df: pd.DataFrame) -> pd.DataFrame:
    """
    Devuelve una copia del DataFrame en la que las listas y diccionarios
    se convierten temporalmente en texto. Se usa SOLO para comparar filas
    (drop_duplicates no puede hashear listas). El DataFrame original
    no se modifica.
    """
    copia = df.copy()
    for col in copia.columns:
        copia[col] = copia[col].apply(
            lambda v: json.dumps(v, sort_keys=True, ensure_ascii=False)
            if isinstance(v, (list, dict))
            else v
        )
    return copia


# ============================================================
# 3. LIMPIAR LA TABLA (DataFrame)
# ============================================================
def limpiar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica las reglas de limpieza sobre el DataFrame aplanado.
    Cada bloque está comentado con lo que hace y por qué.
    """
    df = df.copy()

    # --------------------------------------------------------
    # 3.1. ELIMINAR DUPLICADOS
    # --------------------------------------------------------
    # drop_duplicates() no puede comparar columnas con listas (por ejemplo
    # 'alergias' o 'antecedentes'). Por eso se hace una copia serializada
    # (listas/dicts → texto), se calcula la máscara sobre esa copia y se
    # aplica al DataFrame original.

    # 3.1.a. Duplicados exactos (todas las columnas iguales)
    copia = copia_serializada(df)
    mascara = copia.duplicated(keep="first")
    df = df.loc[~mascara].reset_index(drop=True)

    # 3.1.b. Duplicados por clave '_id_parte'
    copia = copia_serializada(df)          # se refresca por si cambió el tamaño
    mascara = copia.duplicated(subset=["_id_parte"], keep="first")
    df = df.loc[~mascara].reset_index(drop=True)

    # --------------------------------------------------------
    # 3.2. NORMALIZAR TEXTO EN COLUMNAS CATEGÓRICAS
    # --------------------------------------------------------
    # Se pasa a minúsculas y se quitan espacios sobrantes.
    # Así 'Cardiovascular' y 'cardiovascular' se consideran iguales.
    columnas_categoricas = [
        "triaje_manchester.color",
        "triaje_manchester.categoria_patologia",
        "modulo_traumatologia.mecanismo_lesion",
        "modulo_traumatologia.zona_afectada",
        "modulo_digestivo.localizacion_dolor",
        "modulo_cardiologia.ritmo",
        "modulo_neurologia.reactividad_pupilar",
        "modulo_respiratorio.auscultacion",
        "modulo_urologia.puno_percusion_renal",
        "modulo_psiquiatria.riesgo_autolitico",
    ]
    for col in columnas_categoricas:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip().str.lower()

    # --------------------------------------------------------
    # 3.3. NORMALIZAR 'alergias' Y 'antecedentes' A LISTA
    # --------------------------------------------------------
    # En el original vienen como lista, como string suelto o como nulo.
    # Los unificamos siempre a lista de strings en minúsculas.
    for col in ["alergias", "antecedentes"]:
        if col in df.columns:
            df[col] = df[col].apply(normalizar_a_lista)

    # --------------------------------------------------------
    # 3.4. CONVERTIR 'edad' Y CONSTANTES A NÚMERO
    # --------------------------------------------------------
    # En el JSON hay edades como texto ("37", "15"...). Las convertimos
    # a número entero. Si alguna no se puede convertir, queda como nulo.
    if "edad" in df.columns:
        df["edad"] = pd.to_numeric(df["edad"], errors="coerce").astype("Int64")

    for col in [
        "constantes.temperatura_c",
        "constantes.frecuencia_cardiaca_triaje",
        "constantes.saturacion_o2",
        "constantes.glucemia_mg_dl",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # --------------------------------------------------------
    # 3.5. APLICAR REGLAS DE DOMINIO (valores imposibles)
    # --------------------------------------------------------
    # Un valor fuera de estos rangos es fisiológicamente imposible
    # (por ejemplo, temperatura 395 °C, saturación 105 %...).
    # Lo convertimos en nulo.
    # NO borramos la fila: el resto de sus columnas sigue siendo válido.
    reglas_dominio = {
        "edad":                                  (0, 110),
        "constantes.temperatura_c":              (30, 45),
        "constantes.frecuencia_cardiaca_triaje": (30, 220),
        "constantes.saturacion_o2":              (50, 100),
        "constantes.glucemia_mg_dl":             (20, 600),
        "triaje_manchester.nivel":               (1, 5),
        "modulo_neurologia.glasgow_coma_scale":  (3, 15),
        "modulo_neurologia.escala_nihss":        (0, 42),
        "modulo_infeccioso.puntuacion_qsofa":    (0, 3),
    }
    for col, (minimo, maximo) in reglas_dominio.items():
        if col in df.columns:
            fuera = df[col].notna() & ((df[col] < minimo) | (df[col] > maximo))
            df.loc[fuera, col] = pd.NA

    # --------------------------------------------------------
    # 3.6. IMPUTAR NULOS EN 'edad' CON LA MEDIANA
    # --------------------------------------------------------
    # La mediana es robusta frente a valores extremos (mejor que la media).
    if "edad" in df.columns and df["edad"].isna().any():
        df["edad"] = df["edad"].fillna(df["edad"].median()).astype("Int64")

    # NOTA IMPORTANTE:
    # El resto de columnas fisiológicas (temperatura, saturación, glucemia...)
    # NO se imputan. Un valor ausente en clínica es información: significa que
    # esa prueba no se realizó. Inventar un valor falsearía los datos.

    return df


# ============================================================
# 4. RECONSTRUIR LA ESTRUCTURA ANIDADA ORIGINAL
# ============================================================
def reconstruir_anidado(df: pd.DataFrame) -> list:
    """
    Convierte la tabla plana (columnas con puntos: 'a.b.c')
    en la estructura anidada original (diccionarios dentro de diccionarios).
    Los valores nulos se omiten para que el JSON quede limpio.
    """
    documentos = []
    for _, fila in df.iterrows():
        documento = {}
        for columna, valor in fila.items():
            # Detectar nulos con pandas (incluye pd.NA, None, NaN, NaT).
            # Se protegen listas/dicts porque pd.isna devuelve un array en ellos.
            if not isinstance(valor, (list, dict)) and pd.isna(valor):
                valor = None
            elif hasattr(valor, "item"):
                # numpy / pandas scalar → tipo nativo de Python
                valor = valor.item()

            # Si el valor es nulo, no lo guardamos
            if valor is None:
                continue

            # 'a.b.c' → documento['a']['b']['c']
            partes = columna.split(".")
            ref = documento
            for parte in partes[:-1]:
                ref = ref.setdefault(parte, {})
            ref[partes[-1]] = valor

        documentos.append(documento)
    return documentos


# ============================================================
# 5. VERIFICAR QUE LA ESTRUCTURA DE SALIDA ES COMPATIBLE
# ============================================================
def verificar(original: list, limpio: list) -> None:
    """
    Comprueba que el fichero limpio mantiene la MISMA ESTRUCTURA
    que el original, para que luego se puedan unir sin problemas.
    """
    print("\n--- VERIFICACIÓN ---")

    # 1) Ambos son listas
    assert isinstance(original, list), "El original no es una lista"
    assert isinstance(limpio, list), "El limpio no es una lista"
    print(f"Original: lista con {len(original)} partes")
    print(f"Limpio  : lista con {len(limpio)} partes")

    # 2) Las claves de primer nivel del original también están en el limpio
    claves_original = set()
    for doc in original:
        claves_original.update(doc.keys())
    claves_limpio = set()
    for doc in limpio:
        claves_limpio.update(doc.keys())
    faltan = claves_original - claves_limpio
    assert not faltan, f"Faltan claves de primer nivel: {faltan}"
    print("Todas las claves de primer nivel están presentes ✅")

    # 3) Los subdocumentos son diccionarios y las listas son listas
    for doc in limpio:
        for clave, valor in doc.items():
            if clave in ("triaje_manchester", "constantes") or clave.startswith("modulo_"):
                assert isinstance(valor, dict), f"'{clave}' debería ser dict"
            if clave in ("antecedentes", "alergias"):
                # Puede no aparecer (era nulo y se descartó) o ser lista.
                # Lo que NO puede pasar es que sea un string suelto.
                assert isinstance(valor, list), (
                    f"'{clave}' debería ser list, no {type(valor).__name__}"
                )
    print("Subdocumentos y listas tienen el tipo correcto ✅")

    # 4) Resumen final
    print("Estructura compatible con el original ✅")
    print("--------------------\n")


# ============================================================
# 6. PROGRAMA PRINCIPAL
# ============================================================
def main() -> None:
    # 1) Leer el original
    datos_originales = leer_json(RUTA_ORIGEN)
    print(f"Leídos {len(datos_originales)} partes del fichero original.")

    # 2) Aplanar: lista de dicts → tabla con columnas 'a.b.c'
    df = pd.json_normalize(datos_originales, sep=".")

    # 3) Limpiar la tabla
    df_limpio = limpiar(df)
    print(f"Quedan {len(df_limpio)} partes tras la limpieza.")

    # 4) Volver a la estructura anidada
    datos_limpios = reconstruir_anidado(df_limpio)

    # 5) Guardar el JSON limpio (el original NO se toca)
    with open(RUTA_DESTINO, "w", encoding="utf-8") as f:
        json.dump(datos_limpios, f, ensure_ascii=False, indent=2)
    print(f"Fichero limpio guardado en: {RUTA_DESTINO}")

    # 6) Verificar que la estructura es compatible con la del original
    verificar(datos_originales, datos_limpios)


if __name__ == "__main__":
    main()