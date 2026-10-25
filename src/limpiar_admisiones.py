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
from datetime import datetime

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

# Formatos de fecha presentes en el CSV (cubren el 100% de los casos vistos)
FORMATOS_FECHA = (
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %I:%M %p",
    "%d/%m/%Y %I:%M:%S %p",
    "%d/%m/%Y %H:%M",
    "%Y/%m/%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S",
    "%d-%m-%Y %H:%M:%S",
    "%d-%m-%Y %I:%M %p",
)


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


def parse_fecha(val):
    """
    Devuelve datetime o None. Sin dateutil: solo strptime con formatos conocidos.
    """
    if _is_null_token(val):
        return None
    s = str(val).strip()
    if s.upper() in {"NULL", "N/D", "NONE"}:
        return None
    for fmt in FORMATOS_FECHA:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    # Formato no previsto -> None (se puede auditar en rechazos si interesa)
    log.debug("Fecha no parseable: %r", s)
    return None


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
    df["timestamp_llegada"]   = df["timestamp_llegada"].map(parse_fecha)
    df["timestamp_alta"]      = df["timestamp_alta"].map(parse_fecha)
    df["frecuencia_cardiaca"] = df["frecuencia_cardiaca"].map(parse_frecuencia)
    df["tension_arterial"]    = df["tension_arterial"].map(parse_tension)
    df["destino_alta"]        = df["destino_alta"].map(normalizar_destino)

    mask_sin_id   = df["id_episodio"].isna()
    mask_sin_fech = df["timestamp_llegada"].isna() & df["timestamp_alta"].isna()

    rechazos = df[mask_sin_id | mask_sin_fech].copy()
    if len(rechazos):
        rechazos["_motivo_rechazo"] = pd.NA
        rechazos.loc[mask_sin_id, "_motivo_rechazo"]   = "sin_id_episodio"
        rechazos.loc[mask_sin_fech, "_motivo_rechazo"] = "sin_fechas_validas"
        log.info("Filas rechazadas: %d", len(rechazos))
    else:
        log.info("Filas rechazadas: 0")

    df = df[~(mask_sin_id | mask_sin_fech)].copy()
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
