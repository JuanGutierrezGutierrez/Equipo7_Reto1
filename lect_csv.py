import csv

with open("data\admisiones_historico.csv", newline="", encoding="utf-8") as f:
    filas = list(csv.DictReader(f))

print(filas)