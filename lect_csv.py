import pandas as pd

# lectura  del fichero csv
df = pd.read_csv("data\admisiones_historico.csv")


# Mostrar las dimensiones
print(df.shape)

# Mostrar todas las filas y columnas
print(df.to_string())