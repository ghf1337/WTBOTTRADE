import json, math, time, threading, os, pyotp, random, shutil
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    WebDriverException, TimeoutException, NoSuchElementException,
    StaleElementReferenceException
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# --- Функции входа ---
def click_login_and_account(driver):
    try:
        wait = WebDriverWait(driver, 20)
        login_span = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#content > div.CustomScrollbar-wrapper > div > div > div.centeredBlock > div > div.links > a > span"))
        )
        if "Войти" in login_span.text:
            login_span.click()
            print("Кнопка 'Войти' найдена и нажата")
            time.sleep(1)
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.TAG_NAME, "iframe")))
            account_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".account-name")))
            account_button.click()
            driver.switch_to.default_content()
            print("Кнопка первого аккаунта найдена и нажата")
    except Exception:
        print("Не удалось найти кнопку 'Войти' или аккаунт.")


def login_to_pixstorm(driver):
    try:
        driver.get("https://trade.pixstorm.ru/")
        wait = WebDriverWait(driver, 10)
        button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#content > div.CustomScrollbar-wrapper > div > div > div.centeredBlock > div > div.links > a"))
        )
        button.click()
        print("Кнопка успешно нажата!")

        time.sleep(1)
        iframe = driver.find_element(By.CSS_SELECTOR, "iframe")
        driver.switch_to.frame(iframe)
        print("Переключились на iframe")

        EMAIL = os.getenv("PIXSTORM_EMAIL", "your_email@example.com")
        PASSWORD = os.getenv("PIXSTORM_PASSWORD", "your_password")
        driver.execute_script(f"document.querySelector('#email').value = '{EMAIL}';")
        driver.execute_script(f"document.querySelector('#password').value = '{PASSWORD}';")

        login_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#js-form > div:nth-child(3) > button"))
        )
        login_button.click()
        print("Кнопка 'Войти' успешно нажата!")

        time.sleep(2)
        remember_checkbox = driver.find_element(By.XPATH, "/html/body/div[1]/div/div[2]/div/div[2]/div/form/div[1]/div[1]/input")
        remember_checkbox.click()
        print("Галочка для двухфакторной аутентификации установлена!")

        secret = os.getenv("PIXSTORM_TOTP_SECRET", "YOUR_2FA_SECRET_KEY")
        totp = pyotp.TOTP(secret)
        app_code = totp.now()
        print("Сгенерированный код приложения:", app_code)

        driver.find_element(By.XPATH, "/html/body/div[1]/div/div[2]/div/div[2]/div/form/div[1]/div[2]/input").send_keys(app_code)
        print("Код приложения успешно введен!")

        driver.find_element(By.XPATH, "/html/body/div[1]/div/div[2]/div/div[2]/div/form/div[1]/div[3]/button").click()
        print("Подтверждение успешно выполнено!")

        time.sleep(5)
        driver.switch_to.default_content()

        close_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/button"))
        )
        close_button.click()
        print("Закрыто всплывающее сообщение.")
    except Exception as e:
        print("Ошибка при входе:", e)


# --- Перейти на страницу продаж ---
def go_to_sales():
    try:
        driver.get("https://trade.pixstorm.ru/orders")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'switchItem') and text()='Заявки на продажу']"))
        )
        sales_button = driver.find_element(By.XPATH, "//div[contains(@class, 'switchItem') and text()='Заявки на продажу']")
        driver.execute_script("arguments[0].click();", sales_button)
        print("Перешли на страницу 'Заявки на продажу'.")
    except Exception as e:
        print("Ошибка при переходе на страницу продаж:", e)


# --- Отмена заявок на продажу ---
def cancel_sales_requests(attempts=5):
    if attempts <= 0:
        print("Достигнуто максимальное количество попыток для отмены продаж.")
        return False
    try:
        go_to_sales()
        wait = WebDriverWait(driver, 15)
        cancel_buttons = wait.until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'button cancel') and text()='Отменить']"))
        )

        for button in cancel_buttons:
            driver.execute_script("arguments[0].click();", button)
            print("Нажата кнопка 'Отменить' для продажи.")
            time.sleep(0.5)
            confirm_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div/div/div[2]/div/div/div[1]/div/div[1]/div[2]/div[2]/div[2]"))
            )
            confirm_button.click()
            print("Нажата кнопка 'Да, для всех'.")
            time.sleep(0.1)
            go_to_sales()

        cancel_sales_requests(attempts - 1)
    except StaleElementReferenceException:
        print("Обнаружен устаревший элемент, повторяем попытку без уменьшения счетчика")
        cancel_sales_requests(attempts)
    except Exception as e:
        print("Произошла ошибка при отмене продаж:", e)
        if attempts <= 1:
            now = time.strftime("%Y%m%d_%H%M%S")
            crash_dir = os.getenv("CRASH_DIR", "./crashes")
            os.makedirs(crash_dir, exist_ok=True)
            path = os.path.join(crash_dir, f"cancel_sales_{now}.png")
            driver.save_screenshot(path)
            print(f"Скриншот сохранен: {path}")
        click_login_and_account(driver)
        login_to_pixstorm(driver)
        cancel_sales_requests(attempts - 1)


# --- Запуск ---
options = Options()
options.set_preference('permissions.default.image', 2)
options.set_preference('gfx.webrender.all', False)
options.add_argument('--headless')
options.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', False)
options.set_preference('network.http.pipelining', True)
options.set_preference('network.http.pipelining.maxrequests', 8)
options.set_preference('network.http.pipelining.abortonerror', False)
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.set_preference('security.sandbox.content.level', 0)
options.set_preference('toolkit.telemetry.reportingpolicy.firstRun', False)

GECKO_DRIVER = os.getenv("GECKO_DRIVER_PATH", "/usr/local/bin/geckodriver")
driver = webdriver.Firefox(
    service=Service(GECKO_DRIVER),
    options=options
)
driver.set_window_size(1920, 1080)

login_to_pixstorm(driver)
driver.get("https://trade.pixstorm.ru/orders")

try:
    close_button = WebDriverWait(driver, 3).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/button"))
    )
    close_button.click()
    print("Закрыто всплывающее сообщение.")
except Exception:
    print("Всплывающее сообщение не найдено.")

print("Все доступные заявки на продажу отменены.")
cancel_sales_requests()
driver.quit()
