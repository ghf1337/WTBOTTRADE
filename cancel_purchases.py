import json, math, pyotp, time, threading, os, random, shutil
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


# --- Настройка браузера ---
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

driver = webdriver.Firefox(
    service=Service('YouPath'),
    options=options
)
driver.set_window_size(1920, 1080)


# --- Авторизация ---
def click_login_and_account(driver):
    try:
        wait = WebDriverWait(driver, 10)
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
            return True
        else:
            print("Найдена кнопка, но текст не 'Войти'")
            return False
    except (TimeoutException, NoSuchElementException):
        print("Не удалось найти кнопку первого аккаунта")
        return False
    except TimeoutException:
        print("Не удалось найти кнопку 'Войти'")
        return False


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

        # Вводим логин и пароль
        driver.execute_script("document.querySelector('#email').value = 'email';")
        driver.execute_script("document.querySelector('#password').value = 'password';")

        # Входим
        login_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#js-form > div:nth-child(3) > button"))
        )
        login_button.click()
        print("Кнопка 'Войти' успешно нажата!")

        time.sleep(2)
        remember_checkbox = driver.find_element(By.XPATH, "/html/body/div[1]/div/div[2]/div/div[2]/div/form/div[1]/div[1]/input")
        remember_checkbox.click()
        print("Галочка для двухфакторной аутентификации установлена!")

        # Генерация TOTP
        secret = "BZ3D73HNRTGG66FM"
        totp = pyotp.TOTP(secret)
        app_code = totp.now()
        print("Сгенерированный код приложения:", app_code)

        code_input = driver.find_element(By.XPATH, "/html/body/div[1]/div/div[2]/div/div[2]/div/form/div[1]/div[2]/input")
        code_input.send_keys(app_code)
        print("Код приложения успешно введен!")

        confirm_button = driver.find_element(By.XPATH, "/html/body/div[1]/div/div[2]/div/div[2]/div/form/div[1]/div[3]/button")
        confirm_button.click()
        print("Подтверждение успешно выполнено!")

        time.sleep(5)
        driver.switch_to.default_content()

        # Закрытие всплывающего окна
        close_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/button"))
        )
        close_button.click()
        print("Закрыто всплывающее сообщение.")
        return True
    except Exception as e:
        print("Ошибка при авторизации:", e)
        return False


# --- Основная логика отмены заявок ---
def cancel_purchase_requests(attempts=5):
    if attempts <= 0:
        print("Достигнуто максимальное количество попыток.")
        return False

    try:
        driver.get("https://trade.pixstorm.ru/orders")
        wait = WebDriverWait(driver, 15)
        cancel_buttons = wait.until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'button cancel') and text()='Отменить']"))
        )

        for button in cancel_buttons:
            driver.execute_script("arguments[0].click();", button)
            print("Нажата кнопка 'Отменить'.")
            time.sleep(0.1)

            confirm_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div/div/div[2]/div/div/div[1]/div/div[1]/div[2]/div[2]/div[2]"))
            )
            confirm_button.click()
            print("Нажата кнопка 'Да, для всех'.")
            time.sleep(1)
            driver.refresh()

        # Повторяем для возможных оставшихся
        cancel_purchase_requests(attempts - 1)
    except StaleElementReferenceException:
        print("Обнаружен устаревший элемент, повторяем попытку без уменьшения счетчика")
        cancel_purchase_requests(attempts)
    except Exception as e:
        print("Произошла ошибка:", e)
        if attempts <= 1:
            now = time.strftime("%Y%m%d_%H%M%S")
            path = f"YouPath{now}.png"
            driver.save_screenshot(path)
            print(f"Скриншот сохранен: {path}")
        click_login_and_account(driver)
        login_to_pixstorm(driver)
        cancel_purchase_requests(attempts - 1)


# --- Запуск ---
login_to_pixstorm(driver)
driver.get("https://trade.pixstorm.ru/orders")

try:
    close_button = WebDriverWait(driver, 1).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/button"))
    )
    close_button.click()
    print("Закрыто всплывающее сообщение.")
except Exception:
    print("Всплывающее сообщение не найдено.")

time.sleep(3)
cancel_purchase_requests()
driver.quit()
