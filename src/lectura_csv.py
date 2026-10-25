import pandas as pd
from pathlib import Path

# Localizar el archivo csv desde la ubicación del script.
ruta_archivo = (
    Path(__file__).resolve().parent.parent        
    / "data"
    / "admisiones_historico.csv"
)
#imprimo la ruta
print(f"Ruta del archivo CSV: {ruta_archivo}")

#ahora lo meto en un dataframe de pandas
df = pd.read_csv(ruta_archivo)
print(df.head())