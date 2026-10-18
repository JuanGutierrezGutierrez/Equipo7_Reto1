import pandas as pd
import csv

# lectura  del fichero csv
df = pd.read_csv("data\admisiones_historico.csv")
import pandas as pd

# Leer el fichero CSV
df = pd.read_csv("admisiones_historico.csv")

# Mostrar las dimensiones
print(df.shape)

# Mostrar todas las filas y columnas
print(df.to_string())