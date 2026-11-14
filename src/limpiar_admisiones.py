#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
limpiar_admisiones.py
---------------------
Lee admisiones_historico.csv, lo limpia y escribe:
    - admisiones_historico_limpio.csv      (listo para integrar)
    - admisiones_historico_rechazos.csv    (filas descartadas, para auditoría)

Dependencias: SOLO pandas.
"""

import re
import logging

import pandas as pd

from pathlib import Path

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
CSV_ENTRADA  = Path(__file__).resolve().parent.parent / "data" / "admisiones_historico.csv"
CSV_SALIDA   = Path(__file__).resolve().parent.parent / "data" / "admisiones_historico_limpio.csv"
CSV_RECHAZOS = Path(__file__).resolve().parent.parent / "data" / "admisiones_historico_rechazo.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("limpieza")

NULL_TOKENS = {
    "", "n/d", "nd", "null", "none", "nan", "s/d", "sd",
    "pendiente", "normal", "error", "n.a.", "na",
}

DESTINO_MAP = {
    "ingreso_planta":         "ingreso_planta",
    "ingreso_pediatria":      "ingreso_pediatria",
    "observacion":            "observacion",
    "domicilio":              "domicilio",
    "alta":                   "alta",
    "alta_domicilio":         "alta",
    "alta_observacion":       "alta_observacion",
    "alta_ingreso_planta":    "alta_ingreso_planta",
    "alta_ingreso_pediatria": "alta_ingreso_pediatria",
    "traslado_uci":           "traslado_uci",
    "alta_traslado_uci":      "traslado_uci",
    "fallecimiento":          "fallecimiento",
}

FC_MIN, FC_MAX   = 20, 250
PAS_MIN, PAS_MAX = 50, 300
PAD_MIN, PAD_MAX = 20, 200


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def _is_null_token(val) -> bool:
    if val is None:
        return True
    if isinstance(val, float) and pd.isna(val):
        return True
    return str(val).strip().lower() in NULL_TOKENS


def _clean_str(val):
    return None if _is_null_token(val) else str(val).strip()


def estandarizar_fechas(serie):
    """
    Convierte una columna de texto con fechas en varios formatos a datetime.
    Lo que no se pueda leer (N/D, NULL, vacio, corrupto) queda como NaT.

    Se leen en dos grupos porque dayfirst afecta a todo el grupo:
      - las que empiezan por el año (2026-09-08, 2026/09/08)  -> dayfirst=False
      - las que empiezan por el dia (08/09/2026, 08-09-2026)  -> dayfirst=True
    """
    s = serie.astype("string").str.strip().str.replace("Z", "", regex=False)
    empieza_por_anio = s.str[:4].str.isdigit().fillna(False)

    con_anio = pd.to_datetime(s.where(empieza_por_anio),
                              format="mixed", errors="coerce")
    con_dia = pd.to_datetime(s.where(~empieza_por_anio),
                             format="mixed", dayfirst=True, errors="coerce")
    return con_anio.fillna(con_dia)


def parse_frecuencia(val):
    if _is_null_token(val):
        return None
    try:
        n = int(float(str(val).strip()))
    except (ValueError, TypeError):
        return None
    return n if FC_MIN <= n <= FC_MAX else None


def parse_tension(val):
    if _is_null_token(val):
        return None
    nums = re.findall(r"\d+", str(val).strip())
    if len(nums) < 2:
        return None
    sist, diast = int(nums[0]), int(nums[1])
    if not (PAS_MIN <= sist <= PAS_MAX):
        return None
    if not (PAD_MIN <= diast <= PAD_MAX):
        return None
    if sist <= diast:
        return None
    return f"{sist}/{diast}"


def normalizar_destino(val):
    s = _clean_str(val)
    if s is None:
        return None
    key = s.lower().replace(" ", "_").replace("-", "_")
    return DESTINO_MAP.get(key, key)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
def limpiar_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    log.info("Filas leídas: %d", len(df))

    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    df.columns = [c.strip() for c in df.columns]

    antes = len(df)
    df = df.drop_duplicates(subset=["id_episodio"], keep="first")
    log.info("Duplicados por id_episodio eliminados: %d", antes - len(df))

    df["id_episodio"]         = df["id_episodio"].map(_clean_str)
    df["sip_paciente"]        = df["sip_paciente"].map(_clean_str)
    df["motivo_consulta"]     = df["motivo_consulta"].map(_clean_str)
    df["timestamp_llegada"]   = estandarizar_fechas(df["timestamp_llegada"])
    df["timestamp_alta"]      = estandarizar_fechas(df["timestamp_alta"])
    df["frecuencia_cardiaca"] = df["frecuencia_cardiaca"].map(parse_frecuencia)
    df["tension_arterial"]    = df["tension_arterial"].map(parse_tension)
    df["destino_alta"]        = df["destino_alta"].map(normalizar_destino)

    mask_sin_id   = df["id_episodio"].isna()
    mask_sin_fech = df["timestamp_llegada"].isna() & df["timestamp_alta"].isna()

    # Solo se rechaza lo que no se puede identificar (sin id_episodio).
    # Un episodio sin fechas se conserva: sigue aportando datos validos y
    # cada consulta excluye por su cuenta lo que no puede usar.
    log.info("Filas sin ninguna fecha valida (se conservan): %d",
             (mask_sin_fech & ~mask_sin_id).sum())

    # Alta anterior a la llegada: las fechas son incoherentes y no sabemos cual
    # de las dos es la erronea. Se anulan las dos y el episodio se conserva.
    mask_incoherente = df["timestamp_alta"] < df["timestamp_llegada"]
    log.info("Episodios con alta anterior a la llegada (fechas anuladas): %d",
             mask_incoherente.sum())
    df.loc[mask_incoherente, ["timestamp_llegada", "timestamp_alta"]] = pd.NaT

    rechazos = df[mask_sin_id].copy()
    if len(rechazos):
        rechazos["_motivo_rechazo"] = "sin_id_episodio"
        log.info("Filas rechazadas: %d", len(rechazos))
    else:
        log.info("Filas rechazadas: 0")

    df = df[~mask_sin_id].copy()
    df = df[[
        "id_episodio",
        "sip_paciente",
        "timestamp_llegada",
        "timestamp_alta",
        "motivo_consulta",
        "frecuencia_cardiaca",
        "tension_arterial",
        "destino_alta",
    ]].reset_index(drop=True)

    log.info("Filas limpias: %d", len(df))
    return df, rechazos


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    df = pd.read_csv(CSV_ENTRADA, dtype=str, keep_default_na=False)
    df_limpio, df_rechazos = limpiar_dataframe(df)

    df_limpio.to_csv(
        CSV_SALIDA,
        index=False,
        date_format="%Y-%m-%d %H:%M:%S",
        na_rep="",
        encoding="utf-8",
    )
    log.info("CSV limpio escrito en %s", CSV_SALIDA)

    if len(df_rechazos):
        df_rechazos.to_csv(
            CSV_RECHAZOS,
            index=False,
            date_format="%Y-%m-%d %H:%M:%S",
            na_rep="",
            encoding="utf-8",
        )
        log.info("CSV de rechazos escrito en %s", CSV_RECHAZOS)


if __name__ == "__main__":
    main()
