# -*- coding: utf-8 -*-
# Reconstructed from disassembly (prod.dis.txt)
# NOTE: This is a best-effort decompilation; structure and strings follow the bytecode as closely as possible.

import json
import math
import time
import pyotp
import threading
import os
import random
from datetime import datetime
import shutil

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

CACHE_DIR = os.getenv("CACHE_DIR", "./cache")

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)


def click_login_and_account(driver) -> bool:
    try:
        login_span = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#content > div.CustomScrollbar-wrapper > div > div > div.centeredBlock > div > div.links > a > span'))
        )
        if 'Войти' in login_span.text:
            login_span.click()
            print("Кнопка 'Войти' найдена и нажата")
            time.sleep(1)

            WebDriverWait(driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.TAG_NAME, 'iframe'))
            )

            account_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.account-name'))
            )
            account_button.click()
            driver.switch_to.default_content()
            print('Кнопка первого аккаунта найдена и нажата')
            return True
        else:
            print("Найдена кнопка, но текст не 'Войти'")
            return False
    except (TimeoutException, NoSuchElementException):
        print('Не удалось найти кнопку первого аккаунта')
        return False
    except TimeoutException:
        print("Не удалось найти кнопку 'Войти'")
        return False


def login_to_pixstorm(driver) -> bool:
    try:
        driver.get('https://trade.pixstorm.ru/')
        try:
            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '#content > div.CustomScrollbar-wrapper > div > div > div.centeredBlock > div > div.links > a'))
            )
            button.click()
            print('Кнопка успешно нажата!')
        except Exception as e:
            print('Ошибка при нажатии кнопки: ', e)
            return False

        time.sleep(1)
        try:
            iframe = driver.find_element(By.CSS_SELECTOR, 'iframe')
            driver.switch_to.frame(iframe)
            print('Переключились на iframe')
        except Exception as e:
            print('Ошибка при переключении на iframe: ', e)
            return False

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#email'))
        )
        EMAIL = os.getenv("PIXSTORM_EMAIL", "your_email@example.com")
        PASSWORD = os.getenv("PIXSTORM_PASSWORD", "your_password")
        driver.execute_script(f"document.querySelector('#email').value = '{EMAIL}';")
        driver.execute_script(f"document.querySelector('#password').value = '{PASSWORD}';")

        driver.switch_to.default_content()
        driver.switch_to.frame(iframe)

        try:
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '#js-form > div:nth-child(3) > button'))
            )
            login_button.click()
            print("Кнопка 'Войти' успешно нажата!")
        except Exception as e:
            print("Ошибка при нажатии кнопки 'Войти': ", e)
            return False

        time.sleep(2)

        try:
            remember_twostep = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div/div[2]/div/form/div[1]/div[1]/input')
            remember_twostep.click()
            print('Галочка для двухфакторной аутентификации установлена!')
        except Exception as e:
            print('Ошибка при установке галочки: ', e)
            # falls through to TOTP anyway

        secret = os.getenv("PIXSTORM_TOTP_SECRET", "YOUR_2FA_SECRET_KEY")
        totp = pyotp.TOTP(secret)
        app_code = totp.now()
        print('Сгенерированный код приложения: ', app_code)

        try:
            app_code_input = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div/div[2]/div/form/div[1]/div[2]/input')
            app_code_input.send_keys(app_code)
            print('Код приложения успешно введен!')
        except Exception as e:
            print('Ошибка при вводе кода приложения: ', e)
            return False

        try:
            confirm_button = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div/div[2]/div/form/div[1]/div[3]/button')
            confirm_button.click()
            print('Подтверждение успешно выполнено!')
        except Exception as e:
            print('Ошибка при нажатии кнопки подтверждения: ', e)
            return False

        time.sleep(5)

        try:
            driver.switch_to.default_content()
            close_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[2]/button'))
            )
            close_button.click()
            print('Закрыто всплывающее сообщение.')
        except Exception:
            print('Всплывающее сообщение не найдено.')

        time.sleep(1)
        return True

    except Exception as e:
        print('Произошла непредвиденная ошибка: ', e)
        return False


def create_driver():
    options = Options()
    options.add_argument('--headless')
    options.set_preference('permissions.default.image', 2)
    options.set_preference('browser.cache.disk.parent_directory', CACHE_DIR)
    options.set_preference('browser.cache.disk.capacity', 104857600)
    options.set_preference('browser.cache.memory.capacity', 10485760)
    options.set_preference('gfx.webrender.all', False)
    options.set_preference('layers.acceleration.disabled', False)
    options.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', False)
    options.set_preference('network.http.pipelining', True)
    options.set_preference('network.http.pipelining.maxrequests', 8)
    options.set_preference('network.http.pipelining.abortonerror', False)
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.set_preference('security.sandbox.content.level', 0)
    options.set_preference('toolkit.telemetry.reportingpolicy.firstRun', False)

    GECKO_DRIVER = os.getenv("GECKO_DRIVER_PATH", "/usr/local/bin/geckodriver")
    driver = webdriver.Firefox(service=Service(GECKO_DRIVER), options=options)
    return driver


urls_file = os.getenv("URLS_FILE", "./produrls.txt")

# Load URLs
try:
    with open(urls_file, 'r', encoding='utf-8') as file:
        urls = [line.strip() for line in file if line.strip()]
except Exception as e:
    print('Ошибка загрузки списка ссылок: ', e)
    exit()

if not urls:
    print('Файл ссылок пуст.')
    exit()


def save_screenshot(driver, name):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{name}_{timestamp}.png'
    crash_dir = os.getenv("CRASH_DIR", "./crashes")
    os.makedirs(crash_dir, exist_ok=True)
    path = os.path.join(crash_dir, filename)
    driver.save_screenshot(path)
    print('Скриншот сохранён: ', path)


def worker(urls_chunk, thread_id):
    # thread_vars carries driver, per-thread cache dir, etc.
    thread_vars = {
        'driver': None,
        'cache_dir': f'{CACHE_DIR}/thread_{thread_id}',
        'cookies_loaded': False,
        'current_url': None,
        'prices': {'buy': 0, 'sell': 0, 'profit': 0},
    }
    print(f'[Поток {thread_id}] Инициализация...')

    try:
        if os.path.exists(thread_vars['cache_dir']):
            shutil.rmtree(thread_vars['cache_dir'])
        os.makedirs(thread_vars['cache_dir'])

        options = Options()
        options.headless = True
        options.add_argument('--headless')
        options.set_preference('permissions.default.image', 2)
        options.set_preference('browser.cache.disk.parent_directory', CACHE_DIR)
        options.set_preference('browser.cache.disk.capacity', 104857600)
        options.set_preference('browser.cache.memory.capacity', 10485760)
        options.set_preference('gfx.webrender.all', False)
        options.set_preference('layers.acceleration.disabled', False)
        options.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', False)
        options.set_preference('network.http.pipelining', True)
        options.set_preference('network.http.pipelining.maxrequests', 8)
        options.set_preference('network.http.pipelining.abortonerror', False)
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.set_preference('security.sandbox.content.level', 0)
        options.set_preference('toolkit.telemetry.reportingpolicy.firstRun', False)

        GECKO_DRIVER = os.getenv("GECKO_DRIVER_PATH", "/usr/local/bin/geckodriver")
        thread_vars['driver'] = webdriver.Firefox(
            service=Service(GECKO_DRIVER),
            options=options,
        )
        thread_vars['driver'].set_window_size(1920, 1080)

        # Try login first so later flows can reuse session
        login_to_pixstorm(thread_vars['driver'])

        if urls_chunk:
            base_url = urls_chunk[0].split('/market/')[0]
            print(f'[Поток {thread_id}] Открываю базовый URL: {base_url}')
            thread_vars['driver'].get(base_url)
            time.sleep(2)

        for index, url in enumerate(urls_chunk, start=1):
            thread_vars['current_url'] = url
            print(f'\n[Поток {thread_id}] Обработка URL {index}/{len(urls_chunk)}: {url}')
            try:
                process_page(thread_vars['driver'], url, retry=False)
                time.sleep(random.uniform(0.5, 1.5))
            except Exception as e:
                print(f"[Поток {thread_id}] Ошибка обработки URL {url}: {str(e)}")
                save_screenshot(thread_vars['driver'], f'error_thread_{thread_id}_url_{index}')
    except Exception as e:
        print(f"[Поток {thread_id}] Критическая ошибка: {str(e)}")
    finally:
        try:
            if thread_vars['driver']:
                thread_vars['driver'].quit()
                print(f'[Поток {thread_id}] Драйвер успешно закрыт')
        except Exception as e:
            print(f'[Поток {thread_id}] Ошибка при закрытии драйвера: {str(e)}')
        try:
            if os.path.exists(thread_vars['cache_dir']):
                shutil.rmtree(thread_vars['cache_dir'])
                print(f'[Поток {thread_id}] Кэш очищен')
        except Exception as e:
            print(f'[Поток {thread_id}] Ошибка очистки кэша: {str(e)}')


def buy_item(driver, buy_price, retry=True):
    try:
        buy_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.ordersTable.buy div.button.buy'))
        )
        buy_button.click()
        time.sleep(0.1)

        price_input = WebDriverWait(driver, 23).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#modalsHolder > div > div > div.CustomScrollbar-wrapper > div > div.content > div.body > div.view-confirm-dialog-summary > div.view-trade-editor > div.editor-block > div:nth-child(1) > span.input-column.baloonOverride.baloon.baloonTop.baloonCentered > input'))
        )
        price_input.click()

        actions = ActionChains(driver)
        actions.click_and_hold(price_input).perform()

        price_input.send_keys(Keys.HOME)
        price_input.send_keys('0')
        price_input.send_keys(Keys.END)

        current_value = price_input.get_attribute('value')
        for _ in range(len(current_value)):
            price_input.send_keys(Keys.BACKSPACE)

        price_input.send_keys(str(buy_price + 0.01))

        actions.release().perform()

        button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#modalsHolder > div > div > div.CustomScrollbar-wrapper > div > div.content > div.body > div.view-confirm-dialog-summary > div.view-trade-editor > div.editor-block > div:nth-child(2) > span.input-column.baloonOverride.baloon.baloonTop.baloonCentered > div > div.editor-amount-input-more'))
        )
        for _ in range(2):
            button.click()
            time.sleep(0.1)

        place_order_button = WebDriverWait(driver, 23).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div[1]/div/div[1]/div[2]/div[2]/div[3]/div[2]/div/div/div'))
        )
        place_order_button.click()
        time.sleep(0.5)

        confirm_button = WebDriverWait(driver, 23).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div[1]/div/div[1]/div[2]/div[2]/div[3]/div[3]/div'))
        )
        confirm_button.click()
        time.sleep(0.5)
        print('Покупка успешно завершена!')
    except Exception as e:
        print('Ошибка при покупке: ', e)
        current_time = time.strftime('%Y%m%d_%H%M%S')
        crash_dir = os.getenv("CRASH_DIR", "./crashes")
        os.makedirs(crash_dir, exist_ok=True)
        screenshot_path = os.path.join(crash_dir, f'buy_error_{current_time}.png')
        driver.save_screenshot(screenshot_path)
        print('Пробуем переавторизоваться и повторить...')
        click_login_and_account(driver)
        time.sleep(3)
        if retry:
            buy_item(driver, buy_price, retry=False)


def sell_item(driver, sell_price, retry=True):
    try:
        time.sleep(0.3)
        js_selector = '#content > div.CustomScrollbar-wrapper > div > div > div.screenBody > div > div.commodityOrders > div.ordersTable.sell > div.head > div.button.sell'

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, js_selector))
        )

        sell_button_exists = driver.execute_script(
            f"return document.querySelector('{js_selector}') !== null;"
        )
        if not sell_button_exists:
            print("Кнопка 'Продать' не найдена.")
            return

        sell_button_class = driver.execute_script(
            f"return document.querySelector('{js_selector}').getAttribute('class');"
        )
        if 'disabled' in sell_button_class:
            print("Кнопка 'Продать' недоступна: нет предметов для продажи.")
            return

        driver.execute_script(f"document.querySelector('{js_selector}').click();")

        price_input = WebDriverWait(driver, 23).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#modalsHolder > div > div > div.CustomScrollbar-wrapper > div > div.content > div.body > div.view-confirm-dialog-summary > div.view-trade-editor > div.editor-block > div:nth-child(1) > span.input-column.baloonOverride.baloon.baloonTop.baloonCentered > input'))
        )
        price_input.click()

        actions = ActionChains(driver)
        actions.click_and_hold(price_input).perform()

        price_input.send_keys(Keys.HOME)
        price_input.send_keys('0')
        price_input.send_keys(Keys.END)

        current_value = price_input.get_attribute('value')
        for _ in range(len(current_value)):
            price_input.send_keys(Keys.BACKSPACE)

        price_input.send_keys(str(sell_price - 0.01))
        actions.release().perform()

        increase_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div[1]/div/div[1]/div[2]/div[2]/div[3]/div[2]/div[2]/span[3]/div/div[2]'))
        )
        confirm_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div[1]/div/div[1]/div[2]/div[2]/div[3]/div[4]/div'))
        )

        for _ in range(20):
            if confirm_button.is_enabled():
                increase_button.click()
                time.sleep(0.05)

        checkbox = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div/div/div/div/div[2]/div/div/div[1]/div/div[1]/div[2]/div[2]/div[3]/div[3]/div/div/div'))
        )
        checkbox.click()
        time.sleep(0.5)
        confirm_button.click()
        print('Продажа завершена!')
    except Exception as e:
        print('Ошибка при продаже: ', e)
        current_time = time.strftime('%Y%m%d_%H%M%S')
        crash_dir = os.getenv("CRASH_DIR", "./crashes")
        os.makedirs(crash_dir, exist_ok=True)
        screenshot_path = os.path.join(crash_dir, f'sell_error_{current_time}.png')
        driver.save_screenshot(screenshot_path)
        print('Пробуем переавторизоваться и повторить...')
        click_login_and_account(driver)
        time.sleep(3)
        if retry:
            sell_item(driver, sell_price, retry=False)


def get_prices(driver, retry=True):
    try:
        time.sleep(0.1)

        buy_price_element = WebDriverWait(driver, 12).until(
            lambda d: d.execute_script(
                'return document.querySelector("#content > div.CustomScrollbar-wrapper > div > div > div.screenBody > div > div.commodityOrders > div.ordersTable.buy > div.table > div > div:nth-child(2) > div.cell.price");'
            )
        )
        buy_price = float(buy_price_element.text.strip().replace(' ', ''))

        sell_price_element = WebDriverWait(driver, 20).until(
            lambda d: d.execute_script(
                'return document.querySelector("#content > div.CustomScrollbar-wrapper > div > div > div.screenBody > div > div.commodityOrders > div.ordersTable.sell > div.table > div > div:nth-child(2) > div.cell.price");'
            )
        )
        sell_price = float(sell_price_element.text.strip().replace(' ', ''))

        profit = sell_price - (buy_price + 0.15 * buy_price)
        profit = math.floor(profit * 100) / 100.0

        print('Успешно получены цены: покупка=', buy_price, ', продажа=', sell_price, ', прибыль=', profit)
        return buy_price, sell_price, profit

    except Exception as e:
        print('Ошибка при получении цен: ', str(e))
        if retry:
            print('Пробуем переавторизоваться и повторить...')
            click_login_and_account(driver)
            time.sleep(3)
            if not click_login_and_account(driver):
                print('Стандартная авторизация не удалась, пробуем альтернативный метод...')
                login_result = login_to_pixstorm(driver)
                time.sleep(3)
                if not login_result:
                    print('Оба метода авторизации не сработали. Возвращаем None.')
                    return (None, None, None)
            return get_prices(driver, retry=False)
        else:
            print('Повторная попытка не удалась. Возвращаем None.')
            return (None, None, None)


def process_page(driver, url, retry=False):
    print('Открываем ', url)
    driver.get(url)
    time.sleep(0.7)

    buy_price, sell_price, profit = get_prices(driver)

    if profit >= 0.03:
        print('Финансовый результат положительный, продаем предмет!')
        sell_item(driver, sell_price)
        print('Предмет выставлен на продажу.')

    if profit >= 0.08:
        print('Финансовый результат положительный, покупаем предмет!')
        driver.refresh()
        buy_item(driver, buy_price)


def main():
    num_threads = 1
    chunk_size = len(urls) // num_threads
    url_chunks = [urls[i:i + chunk_size] for i in range(0, len(urls), chunk_size)]

    threads = []
    for i, chunk in enumerate(url_chunks):
        thread = threading.Thread(target=worker, args=(chunk, i + 1))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print('Все потоки завершили работу')


if __name__ == '__main__':
    main()
