import subprocess
import time
import os
import shutil
from datetime import datetime

first_program = os.getenv("FIRST_PROGRAM", "./avt2.py")
second_program = os.getenv("SECOND_PROGRAM", "./cancelb.py")
third_program = os.getenv("THIRD_PROGRAM", "./prod.py")
delete_path = os.getenv("DELETE_PATH", "")

while True:
    print("=== Запуск отмены заявок ===")
    for attempt in range(2):
        print(f"Попытка отмены {attempt + 1}/2")
        cancel_process = subprocess.run(["python3", second_program])
        if cancel_process.returncode != 0:
            print(f"Ошибка при отмене (попытка {attempt + 1})")
            if attempt == 0:
                print("Критическая ошибка! Переход к следующему этапу.")
            time.sleep(3)
            continue
        print("Отмена выполнена успешно!")
        break

    print("=== Запуск авторизации ===")
    auth_process = subprocess.run(["python3", first_program])
    if auth_process.returncode != 0:
        print("Ошибка авторизации! Переход к следующему этапу.")

    print("=== Запуск основной программы ===")
    main_process = subprocess.run(["python3", third_program])
    if main_process.returncode != 0:
        print("Ошибка в основной программе!")

    print("Ожидание 40 минут перед новым циклом...")
    time.sleep(2400)
