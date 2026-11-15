import os

# Este menu se ejecuta desde la carpeta src:  python3 menu.py

while True:
    os.system("clear")
    print("===== MENU =====")
    print("1. Levantar los contenedores de Docker")
    print("2. Comprobar la conexion con Mongo y Redis")
    print("3. Limpiar partes_clinicos.json (genera partes_clinicos_limpio.json)")
    print("4. Limpiar admisiones_historico.csv (genera admisiones_historico_limpio.csv)")
    print("5. Insertar los datos limpios en MongoDB (carga historica)")
    print("6. Calcular la estancia media por categoria (genera estancia_media_por_categoria.csv)")
    print("7. Leer la API en tiempo real (Ctrl+C para parar)")
    print("8. Leer la API sin conexion (archivo JSON de muestra)")
    print("0. Salir")
    print()

    opcion = input("Elige una opcion: ")

    if opcion == "1":
        os.system("cd ../docker && docker compose up -d")
        input("Pulsa Enter para continuar...")
    elif opcion == "2":
        os.system("docker exec -w /app/src python_container python chequea_conexion.py")
        input("Pulsa Enter para continuar...")
    elif opcion == "3":
        os.system("docker exec -w /app/src python_container python limpiar_partes_clinicos.py")
        input("Pulsa Enter para continuar...")
    elif opcion == "4":
        os.system("docker exec -w /app/src python_container python limpiar_admisiones.py")
        input("Pulsa Enter para continuar...")
    elif opcion == "5":
        os.system("docker exec -w /app/src python_container python insercion_historica_mongo.py")
        print("Insertando los datos limpios en MongoDB...")
        print("Datos insertados en MongoDB correctamente.")
        input("Pulsa Enter para continuar...")       
    elif opcion == "6":
        os.system("docker exec -w /app/src python_container python estancia_media.py")
        input("Pulsa Enter para continuar...")
    elif opcion == "7":
        os.system("docker exec -it -w /app/src python_container python lectura_api.py")
        input("Pulsa Enter para continuar...")
    elif opcion == "8":
        os.system("docker exec -it -w /app/src python_container python lectura_api_offline.py")
        input("Pulsa Enter para continuar...")
    elif opcion == "0":
        break
    else:
        input("Opcion no valida. Pulsa Enter para continuar...")