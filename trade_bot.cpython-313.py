import json
import time
import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException
)


class TradeBot:
    """Бот для автоматической отмены заявок на сайте https://trade.pixstorm.ru/"""

    def __init__(self):
        self.driver = self._init_driver()
        self._load_cookies()
        self._close_popup()

    # ----------------------------------------------------------------------
    def _init_driver(self):
        """Инициализация браузера Chrome"""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-notifications")
        options.add_argument("--start-maximized")

        chromedriver_path = os.getenv(
            "CHROMEDRIVER_PATH",
            "/usr/local/bin/chromedriver"
        )
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://trade.pixstorm.ru/orders")
        return driver

    # ----------------------------------------------------------------------
    def _load_cookies(self):
        """Загрузка cookies из файла и обновление страницы"""
        cookies_path = os.getenv("COOKIES_PATH", "./cookies.json")

        try:
            with open(cookies_path, "r", encoding="utf-8") as file:
                cookies = json.load(file)

            for cookie in cookies:
                # Удаляем несовместимые поля
                cookie.pop("sameSite", None)
                cookie.pop("storeId", None)
                self.driver.add_cookie(cookie)

            print("✅ Куки успешно загружены!")
            self.driver.refresh()

        except Exception as e:
            print(f"⚠️ Ошибка при загрузке куков: {e}")

    # ----------------------------------------------------------------------
    def _close_popup(self):
        """Закрывает всплывающее окно, если оно есть"""
        try:
            wait = WebDriverWait(self.driver, 3)
            close_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/button"))
            )
            close_button.click()
            print("✅ Закрыто всплывающее сообщение.")
            time.sleep(1)
        except Exception:
            print("ℹ️ Всплывающее сообщение не найдено.")
            time.sleep(1)

    # ----------------------------------------------------------------------
    def _safe_click(self, element, description=""):
        """Безопасное нажатие на элемент с обработкой исключений"""
        try:
            self.driver.execute_script("arguments[0].click();", element)
            print(f"Нажата кнопка {description}")
            return True
        except StaleElementReferenceException:
            print(f"Элемент устарел при попытке {description}")
            return False
        except Exception as e:
            print(f"Ошибка при клике {description}: {e}")
            return False

    # ----------------------------------------------------------------------
    def _go_to_section(self, section_name):
        """Переходит к нужному разделу по названию"""
        try:
            wait = WebDriverWait(self.driver, 5)
            section_button = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//div[contains(@class, 'switchItem') and text()='{section_name}']")
                )
            )
            if self._safe_click(section_button, f"перехода на '{section_name}'"):
                time.sleep(1)
                return True
            return False

        except TimeoutException:
            print(f"Не удалось найти кнопку перехода на '{section_name}'")
            return False

    # ----------------------------------------------------------------------
    def _cancel_requests(self, section_name):
        """Отменяет все заявки в указанном разделе"""
        if not self._go_to_section(section_name):
            return False

        try:
            wait = WebDriverWait(self.driver, 5)
            cancel_buttons = wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[contains(@class, 'button cancel') and text()='Отменить']")
                )
            )

            if not cancel_buttons:
                print(f"Нет доступных заявок в разделе '{section_name}' для отмены.")
                return False

            for button in cancel_buttons:
                if not self._safe_click(button, "'Отменить'"):
                    continue

                try:
                    confirm_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable(
                            (
                                By.XPATH,
                                "/html/body/div[1]/div/div/div/div[2]/div/div/div[1]/div/div[1]/div[2]/div[2]/div[2]",
                            )
                        )
                    )
                    if self._safe_click(confirm_button, "'Да, для всех'"):
                        time.sleep(0.5)
                        self.driver.refresh()
                        time.sleep(0.5)
                        return True
                except TimeoutException:
                    print("Не удалось найти кнопку подтверждения")
                    continue

            return False

        except TimeoutException:
            print(f"Не удалось найти кнопки отмены в разделе '{section_name}'")
            return False

    # ----------------------------------------------------------------------
    def cancel_purchases(self):
        """Отменяет все заявки на покупку"""
        while self._cancel_requests("Покупки"):
            pass
        print("✅ Все доступные заявки на покупку отменены.")

    # ----------------------------------------------------------------------
    def cancel_sales(self):
        """Отменяет все заявки на продажу"""
        while self._cancel_requests("Заявки на продажу"):
            pass
        print("✅ Все доступные заявки на продажу отменены.")

    # ----------------------------------------------------------------------
    def close(self):
        """Закрывает драйвер"""
        self.driver.quit()


# ======================================================================
if __name__ == "__main__":
    bot = TradeBot()
    try:
        bot.cancel_purchases()
        bot.cancel_sales()
    finally:
        bot.close()
