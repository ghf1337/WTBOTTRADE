# -*- coding: utf-8 -*-
"""
Reconstructed from avt2.dis.txt best-effort.
- Логика схожа с prod.py, но список ссылок берётся из YouPath
- Выполняет вход и обработку страниц (минимальная стратегия).
"""

import os, time, threading
from datetime import datetime
import pyotp

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

GECKO = os.getenv("GECKO_DRIVER_PATH", "/usr/local/bin/geckodriver")
CRASH_DIR = os.getenv("CRASH_DIR", "./crashes")
URLS_FILE = os.getenv("URLS_FILE", "./urls.txt")

EMAIL = os.getenv("PIXSTORM_EMAIL", "your_email@example.com")
PASSWORD = os.getenv("PIXSTORM_PASSWORD", "your_password")
TOTP_SECRET = os.getenv("PIXSTORM_TOTP_SECRET", "YOUR_2FA_SECRET_KEY")
BASE_URL = "https://trade.pixstorm.ru/"

def create_driver(headless: bool = True) -> webdriver.Firefox:
    opts = Options()
    if headless: opts.add_argument("--headless")
    opts.set_preference('permissions.default.image', 2)
    opts.set_preference('gfx.webrender.all', False)
    opts.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', False)
    opts.set_preference('network.http.pipelining', True)
    opts.set_preference('network.http.pipelining.maxrequests', 8)
    opts.set_preference('network.http.pipelining.abortonerror', False)
    opts.set_preference('security.sandbox.content.level', 0)
    opts.set_preference('toolkit.telemetry.reportingpolicy.firstRun', False)
    drv = webdriver.Firefox(service=Service(GECKO), options=opts)
    drv.set_window_size(1920, 1080)
    return drv

def login_to_pixstorm(driver: webdriver.Firefox) -> bool:
    try:
        driver.get(BASE_URL)
        wait = WebDriverWait(driver, 15)
        btn = wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            "#content > div.CustomScrollbar-wrapper > div > div > div.centeredBlock > div > div.links > a"
        )))
        btn.click()
        time.sleep(1)
        iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe")))
        driver.switch_to.frame(iframe)
        driver.execute_script("document.querySelector('#email').value = arguments[0];", EMAIL)
        driver.execute_script("document.querySelector('#password').value = arguments[0];", PASSWORD)
        login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#js-form > div:nth-child(3) > button")))
        login_button.click()
        time.sleep(2)
        try:
            driver.find_element(By.XPATH, "/html/body/div[1]/div/div[2]/div/div[2]/div/form/div[1]/div[1]/input").click()
        except NoSuchElementException:
            pass
        totp = pyotp.TOTP(TOTP_SECRET).now()
        driver.find_element(By.XPATH, "/html/body/div[1]/div/div[2]/div/div[2]/div/form/div[1]/div[2]/input").send_keys(totp)
        driver.find_element(By.XPATH, "/html/body/div[1]/div/div[2]/div/div[2]/div/form/div[1]/div[3]/button").click()
        time.sleep(5)
        driver.switch_to.default_content()
        try:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/button"))).click()
        except Exception:
            pass
        return True
    except Exception:
        return False

def save_screenshot(driver: webdriver.Firefox, prefix: str):
    os.makedirs(CRASH_DIR, exist_ok=True)
    path = os.path.join(CRASH_DIR, f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    try:
        driver.save_screenshot(path)
    except Exception:
        pass
    return path

def process_page(driver: webdriver.Firefox, url: str):
    driver.get(url)
    time.sleep(2)
    # Заглушка: просто ждём, что таблицы появятся
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'ordersTable')]")))
    except Exception:
        save_screenshot(driver, "avt2obraboshib_")

def worker(urls: list[str]):
    d = create_driver(headless=True)
    try:
        if not login_to_pixstorm(d):
            save_screenshot(d, "avt2obraboshib_")
        for u in urls:
            try:
                process_page(d, u)
            except StaleElementReferenceException:
                process_page(d, u)
            except Exception:
                save_screenshot(d, "avt2prodazha_")
    finally:
        try: d.quit()
        except Exception: pass

def read_urls(path: str) -> list[str]:
    if not os.path.exists(path): return []
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

if __name__ == "__main__":
    urls = read_urls(URLS_FILE)
    if not urls:
        print("Файл ссылок пуст.")
        raise SystemExit(0)
    worker(urls)
