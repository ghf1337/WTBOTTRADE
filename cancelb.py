import subprocess
import threading
import os
import json
import math
import time
import random
from datetime import datetime
import shutil
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


SCRIPTS_DIR = "YouPath"
PURCHASES_SCRIPT = os.path.join(SCRIPTS_DIR, "cancel_purchases.exe")
SALES_SCRIPT = os.path.join(SCRIPTS_DIR, "cancel_sales.exe")


def run_script(script_path: str):
    """Запускает .exe с помощью python3."""
    subprocess.run(["python3", script_path], check=True)


if __name__ == "__main__":
    t1 = threading.Thread(target=run_script, args=(PURCHASES_SCRIPT,))
    t2 = threading.Thread(target=run_script, args=(SALES_SCRIPT,))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    print("Оба скрипта завершены")
