from typing import Any
from selenium import webdriver
import time
from config import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import pandas as pd
import os
import re
from datetime import datetime
from collections import Counter
from json_urls import *
from filter import *
import logging
import traceback
import random
import signal
import sys
from bs4 import BeautifulSoup

driver = None
global_batch_data = None
excel_filename = None
global_checked_urls = None


def save_progress_on_interrupt():
    if global_batch_data and excel_filename and CHECKED_URLS_FILE_MAIN:
        print(
            f"\n[ПРЕРЫВАНИЕ] Сохранение оставшихся {len(global_batch_data)} записей..."
        )
        try:
            saved_urls = save_to_excel(global_batch_data, excel_filename)
            if saved_urls:
                for saved_url in saved_urls:
                    global_checked_urls[saved_url] = True
                save_json(global_checked_urls, CHECKED_URLS_FILE_MAIN)
                print(f"[ПРЕРЫВАНИЕ] Успешно сохранено {len(saved_urls)} записей")

                # Запускаем функции фильтрации с правильными путями
                clear_filter_contracts_data(
                    input_file=EXCEL_FILE, output_file=FINAL_OUTPUT_PATH3
                )
                filter_contracts_data(
                    input_file=FINAL_OUTPUT_PATH3, output_file=FINAL_OUTPUT_PATH
                )
                weak_filter_contracts_data(
                    input_file=FINAL_OUTPUT_PATH3, output_file=FINAL_OUTPUT_PATH2
                )

        except Exception as e:
            print(f"[ПРЕРЫВАНИЕ] Ошибка при сохранении: {e}")


def signal_handler(sig, frame):

    print(f"\n{'!'*60}")
    print("Получен сигнал прерывания (Ctrl+C)")
    print(f"{'!'*60}")
    save_progress_on_interrupt()
    print("\nЗавершение работы...")
    if driver:
        try:
            driver.quit()
        except:
            pass
    sys.exit(0)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from okved_categories import *


def extract_region_from_page(driver: webdriver.Chrome) -> str | None:

    try:
        # Ищем таблицу с данными компании
        tables = driver.find_elements(By.CSS_SELECTOR, "table.table.two-columns-table")

        for table in tables:
            try:
                # Ищем строку с текстом "Регион"
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 2:
                        label = cells[0].text.strip()
                        if label == "Регион":
                            region = cells[1].text.strip()
                            return region
            except:
                continue

        # Альтернативный способ: поиск по XPath
        try:
            region_elements = driver.find_elements(
                By.XPATH, "//td[contains(text(), 'Регион')]/following-sibling::td[1]"
            )
            if region_elements:
                region = region_elements[0].text.strip()
                return region
        except:
            pass

    except Exception:
        pass

    return None


def normalize_contract_number(contract_str: str) -> str | None:

    if not contract_str:
        return None

    cleaned = contract_str.replace("№", "").strip()
    return cleaned


def find_financial_values(driver):
    """
    Ищет выручку и прибыль на странице datanewton.ru
    Возвращает кортеж (выручка, прибыль) в виде int значений
    """

    def find_value_by_label(label_text):

        try:
            # Ищем элемент, содержащий точно заданную метку
            xpath = f"//*[text()='{label_text}']"
            label_elements = driver.find_elements(By.XPATH, xpath)

            if not label_elements:
                # Если не нашли точное совпадение, пробуем частичное
                xpath = f"//*[contains(text(), '{label_text}')]"
                label_elements = driver.find_elements(By.XPATH, xpath)

            for label_element in label_elements:
                try:
                    # Проверяем, что элемент содержит именно нужную метку
                    element_text = label_element.text.strip()
                    if label_text not in element_text:
                        continue

                    # Ищем родительский контейнер (1 уровень вверх)
                    parent = label_element.find_element(By.XPATH, "..")

                    # В этом контейнере ищем все дочерние элементы
                    all_elements = parent.find_elements(By.XPATH, "./*")

                    # Проходим по всем элементам в контейнере
                    for element in all_elements:
                        element_text = element.text.strip()

                        # Проверяем, что это денежное значение
                        if element_text and element_text != label_text:
                            # Проверяем признаки денежного значения
                            has_money_marker = (
                                "₽" in element_text
                                or "руб" in element_text.lower()
                                or "млн" in element_text.lower()
                                or "млрд" in element_text.lower()
                                or "тыс" in element_text.lower()
                                or "трлн" in element_text.lower()
                                or any(char.isdigit() for char in element_text)
                            )

                            if has_money_marker:
                                # Парсим значение
                                value = parse_money_value(element_text)
                                if value is not None:
                                    return value

                    # Если не нашли на первом уровне, пробуем подняться выше
                    for i in range(3):
                        try:
                            parent = parent.find_element(By.XPATH, "..")
                            all_elements = parent.find_elements(By.XPATH, ".//*")

                            for element in all_elements:
                                element_text = element.text.strip()
                                if element_text and element_text != label_text:
                                    has_money_marker = (
                                        "₽" in element_text
                                        or "руб" in element_text.lower()
                                        or "млн" in element_text.lower()
                                        or "млрд" in element_text.lower()
                                    )

                                    if has_money_marker:
                                        value = parse_money_value(element_text)
                                        if value is not None:
                                            return value
                        except:
                            break

                except Exception as e:
                    print(f"    Ошибка при обработке элемента {label_text}: {e}")
                    continue

        except Exception as e:
            print(f"  Ошибка при поиске {label_text}: {e}")

        return None

    # Ищем выручку и прибыль
    print("  Поиск финансовых показателей...")
    revenue = find_value_by_label("Выручка")
    profit = find_value_by_label("Прибыль")

    if revenue is not None:
        print(f"    Выручка найдена: {revenue}")
    else:
        print("    Выручка не найдена")

    if profit is not None:
        print(f"    Прибыль найдена: {profit}")
    else:
        print("    Прибыль не найдена")

    return revenue, profit


# Обновленный код функции find_inn с новой логикой поиска финансов
def find_inn(driver: webdriver.Chrome, data: dict[str, Any]):

    driver.get(URL_FIND_INN)
    time.sleep(2.5)

    try:
        wait = WebDriverWait(driver, 10)

        input_element = driver.find_elements(By.CSS_SELECTOR, "input[type=search]")[-1]
        input_element.click()
        input_element.send_keys(data["Инн"])
        time.sleep(1)
        input_element.send_keys(Keys.ENTER)
        time.sleep(1)
        time.sleep(3)

        try:
            first_result_link = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "a.list-group-item:nth-child(1)")
                )
            )
            first_result_link.click()
            time.sleep(2.1)
        except Exception:
            try:
                result_links = driver.find_elements(
                    By.CSS_SELECTOR, "a.list-group-item"
                )
                if result_links:
                    result_links[0].click()
                    time.sleep(3)
            except:
                pass

        time.sleep(2)

        # ПАРСИНГ ВСЕХ ВИДОВ ДЕЯТЕЛЬНОСТИ (оставляем ваш существующий код)
        try:
            # Шаг 1: Находим заголовок "Виды деятельности"
            activity_header = None
            try:
                activity_headers = driver.find_elements(
                    By.XPATH, "//h2[contains(text(), 'Виды деятельности')]"
                )
                if activity_headers:
                    activity_header = activity_headers[0]
                    print("  Найден заголовок 'Виды деятельности'")
            except:
                print("  Не найден заголовок 'Виды деятельности'")

            # Шаг 2: Ищем таблицу с видами деятельности после заголовка
            activity_table = None
            if activity_header:
                try:
                    activity_table = activity_header.find_element(
                        By.XPATH, "./following-sibling::table[1]"
                    )
                    print("  Найдена таблица видов деятельности")
                except Exception as e:
                    print(f"  Не найдена таблица после заголовка: {e}")

            if not activity_table:
                try:
                    activity_tables = driver.find_elements(
                        By.CSS_SELECTOR, "table.table.two-columns-table"
                    )
                    for table in activity_tables:
                        table_html = table.get_attribute("outerHTML")
                        if (
                            "Виды деятельности" in table_html
                            or "вид деятельности" in table.text.lower()
                        ):
                            activity_table = table
                            print("  Найдена таблица по содержимому")
                            break
                except:
                    pass

            # Шаг 4: Если нашли таблицу, ищем кнопку "Показать все виды деятельности"
            if activity_table:
                try:
                    show_all_links = activity_table.find_elements(
                        By.XPATH,
                        ".//tfoot//a[contains(text(), 'Показать все виды деятельности') or contains(text(), 'показать все виды деятельности')]",
                    )

                    if not show_all_links:
                        show_all_links = activity_table.find_elements(
                            By.XPATH,
                            ".//a[contains(text(), 'Показать все виды деятельности') or contains(text(), 'показать все виды деятельности')]",
                        )

                    if not show_all_links:
                        show_all_links = activity_table.find_elements(
                            By.XPATH, ".//a[contains(text(), 'виды деятельности')]"
                        )

                    if show_all_links:
                        show_all_button = show_all_links[0]
                        try:
                            driver.execute_script(
                                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                show_all_button,
                            )
                            time.sleep(1)
                            show_all_button.click()
                            print("  Нажата кнопка 'Показать все виды деятельности'")
                            time.sleep(2)
                        except Exception as e:
                            print(f"  Ошибка при клике на кнопку: {e}")
                    else:
                        print("  Кнопка 'Показать все виды деятельности' не найдена")
                except Exception as e:
                    print(f"  Ошибка при поиске кнопки: {e}")

                # Шаг 5: Парсим все виды деятельности из таблицы (ОПТИМИЗИРОВАННЫЙ)
                all_activities = []

                if activity_table:
                    try:
                        # Более быстрый способ - получаем сразу весь HTML таблицы
                        table_html = activity_table.get_attribute("innerHTML")

                        soup = BeautifulSoup(table_html, "html.parser")

                        # Находим все строки таблицы (кроме заголовков)
                        rows = soup.find_all("tr")

                        for row in rows:
                            # Пропускаем заголовки
                            if row.find("th"):
                                continue

                            # Находим все ячейки в строке
                            cells = row.find_all("td")
                            if len(cells) >= 2:
                                # Код вида деятельности
                                code_cell = cells[0]
                                code = code_cell.get_text(strip=True)

                                # Описание вида деятельности
                                desc_cell = cells[1]
                                # Ищем ссылку в ячейке или берем текст
                                link = desc_cell.find("a")
                                if link:
                                    description = link.get_text(strip=True)
                                else:
                                    description = desc_cell.get_text(strip=True)

                                # Проверяем, что код содержит цифры
                                if code and any(char.isdigit() for char in code):
                                    activity_str = f"{code} {description}"
                                    all_activities.append(activity_str)

                        print(
                            f"  Парсинг таблицы завершен. Найдено записей: {len(all_activities)}"
                        )

                    except Exception as e:
                        print(f"  Ошибка при парсинге таблицы: {e}")
                        # Fallback на старый метод если BeautifulSoup не работает
                        try:
                            rows = activity_table.find_elements(By.TAG_NAME, "tr")
                            for row in rows:
                                try:
                                    # Пропускаем заголовки
                                    if row.find_elements(By.TAG_NAME, "th"):
                                        continue

                                    # Более быстрый способ получения текста
                                    cells = row.find_elements(By.TAG_NAME, "td")
                                    if len(cells) >= 2:
                                        # Получаем текст за один раз
                                        row_text = row.text
                                        if row_text:
                                            parts = row_text.split("\n")
                                            if len(parts) >= 2:
                                                code = parts[0].strip()
                                                description = parts[1].strip()
                                                if code and any(
                                                    char.isdigit() for char in code
                                                ):
                                                    activity_str = (
                                                        f"{code} {description}"
                                                    )
                                                    all_activities.append(activity_str)
                                except:
                                    continue
                        except Exception as e2:
                            print(f"  Fallback также не сработал: {e2}")

                # Убираем дубликаты
                if all_activities:
                    # Используем словарь для удаления дубликатов (быстрее чем set+list)
                    unique_dict = {}

                    for activity in all_activities:
                        # Извлекаем код из строки (первые цифры до пробела)
                        match = re.match(r"^(\d[\d\.]*)", activity.strip())
                        if match:
                            code = match.group(1)
                            if code not in unique_dict:
                                unique_dict[code] = activity.strip()

                    unique_activities = list(unique_dict.values())

                    if unique_activities:
                        data["отрасль"] = "; ".join(unique_activities)
                        print(
                            f"  Уникальных видов деятельности: {len(unique_activities)}"
                        )
                    else:
                        data["отрасль"] = None
                else:
                    data["отрасль"] = None

        except Exception as e:
            data["отрасль"] = None
            print(f"  Ошибка при парсинге видов деятельности: {e}")

        # ИСПРАВЛЕННЫЙ ПАРСИНГ ФИНАНСОВЫХ ПОКАЗАТЕЛЕЙ
        print("  Поиск финансовых показателей...")
        try:
            # Используем новую функцию поиска по тексту
            data["выручка"], data["прибыль"] = find_financial_values(driver)

        except Exception as e:
            print(f"  Ошибка при парсинге финансов: {e}")
            data["выручка"] = None
            data["прибыль"] = None

        # ПАРСИНГ РЕГИОНА (оставляем ваш существующий код)
        region = extract_region_from_page(driver)
        if region:
            data["регион"] = region

        return data

    except Exception as e:
        print(f"  Общая ошибка в функции find_inn: {e}")
        return data


# Альтернативный вариант - более специфичный поиск по структуре навигационной панели
def find_financial_values_alternative(driver):
    """
    Альтернативный метод поиска финансовых показателей
    Более специфичен для навигационной панели datanewton
    """

    def find_in_nav_panel(label_text):

        try:
            # Ищем элемент с текстом метки
            label_xpath = f"//*[contains(text(), '{label_text}')]"
            label_elements = driver.find_elements(By.XPATH, label_xpath)

            for label_element in label_elements:
                try:
                    # Ищем родительский контейнер навигационного элемента
                    parent = label_element

                    # Поднимаемся до контейнера с классами bkcBzX или подобными
                    for _ in range(5):
                        parent = parent.find_element(By.XPATH, "..")
                        parent_classes = parent.get_attribute("class") or ""

                        # Проверяем, что это контейнер навигационного элемента
                        if "bkcBzX" in parent_classes or "pirRL" in parent_classes:
                            # Ищем все элементы внутри этого контейнера
                            all_divs = parent.find_elements(By.TAG_NAME, "div")

                            for div in all_divs:
                                div_text = div.text.strip()
                                if div_text and div_text != label_text:
                                    # Проверяем на денежные признаки
                                    if any(
                                        marker in div_text
                                        for marker in [
                                            "₽",
                                            "млн",
                                            "млрд",
                                            "тыс",
                                            "трлн",
                                        ]
                                    ):
                                        value = parse_money_value(div_text)
                                        if value is not None:
                                            return value

                            break

                except Exception as e:
                    continue

        except Exception as e:
            print(f"  Ошибка в альтернативном поиске {label_text}: {e}")

        return None

    # Ищем выручку и прибыль
    print("  Альтернативный поиск финансов...")
    revenue = find_in_nav_panel("Выручка")
    profit = find_in_nav_panel("Прибыль")

    return revenue, profit


def parse_money_value(value_str: str) -> int | None:

    if not value_str:
        return None

    try:
        # Сохраняем знак минуса
        is_negative = value_str.strip().startswith("-")

        # Сохраняем оригинал для поиска множителей
        value_lower = value_str.lower()

        cleaned = (
            value_str.replace(" ", "")  # Неразрывный пробел
            .replace(" ", "")
            .replace("₽", "")
            .replace(".", "")
        )
        cleaned = cleaned.replace(",", ".")

        # Определяем множитель
        multiplier = 1
        if "трлн" in value_lower:
            multiplier = 1_000_000_000_000
            cleaned = cleaned.replace("трлн", "").replace("трлн.", "")
        elif "млрд" in value_lower:
            multiplier = 1_000_000_000
            cleaned = cleaned.replace("млрд", "").replace("млрд.", "")
        elif "млн" in value_lower:
            multiplier = 1_000_000
            cleaned = cleaned.replace("млн", "").replace("млн.", "")
        elif "тыс" in value_lower:
            multiplier = 1_000
            cleaned = cleaned.replace("тыс", "").replace("тыс.", "")

        # Убираем минус из строки для парсинга
        cleaned = cleaned.replace("-", "")

        # Оставляем только цифры и точку
        cleaned = "".join(c for c in cleaned if c.isdigit() or c == ".")

        if not cleaned:
            return None

        result = float(cleaned) * multiplier

        # Возвращаем с нужным знаком
        return -int(result) if is_negative else int(result)

    except Exception:
        return None


def parse_cost_value(cost_str: str) -> float | None:

    if not cost_str:
        return None

    try:
        # Убираем валюту
        cleaned = cost_str.replace("₽", "")

        # Убираем пробелы (включая неразрывные)
        cleaned = cleaned.replace(" ", "").replace(" ", "")

        # Проверяем формат с запятыми
        comma_count = cleaned.count(",")
        dot_count = cleaned.count(".")

        # Формат "1,500,000.00" - запятые как разделители тысяч
        if comma_count > 1 and dot_count == 1:
            cleaned = cleaned.replace(",", "")
        # Формат "1,500,000" - только запятые как разделители
        elif comma_count > 1 and dot_count == 0:
            cleaned = cleaned.replace(",", "")
        # Формат "1,234.56" или "1.234,56" - одна запятая или точка как десятичный разделитель
        else:
            # Если есть и запятая и точка, определяем что есть что
            if "," in cleaned and "." in cleaned:
                # Последний символ определяет десятичный разделитель
                if cleaned.rfind(",") > cleaned.rfind("."):
                    # Запятая - десятичный разделитель, точка - разделитель тысяч
                    cleaned = cleaned.replace(".", "").replace(",", ".")
                else:
                    # Точка - десятичный разделитель, запятая - разделитель тысяч
                    cleaned = cleaned.replace(",", "")
            # Только запятая
            elif "," in cleaned:
                cleaned = cleaned.replace(",", ".")
            # Только точка - оставляем как есть

        # Оставляем только цифры и точку
        cleaned = "".join(c for c in cleaned if c.isdigit() or c == ".")

        if not cleaned:
            return None

        return float(cleaned)
    except Exception:
        return None


def normalize_inn(inn_value: Any) -> str | None:

    if pd.isna(inn_value):
        return None

    inn_str = str(inn_value).strip()

    # Убираем нецифровые символы (кроме цифр)
    inn_cleaned = "".join(c for c in inn_str if c.isdigit())

    # Возвращаем None если пусто после очистки
    return inn_cleaned if inn_cleaned else None


def generate_pagination_urls(
    base_url: str, start_page: int = 1, end_page: int = 10
) -> list[str]:

    urls = []

    for page in range(start_page, end_page + 1):
        if "pageNumber=1" in base_url:
            url = base_url.replace("pageNumber=1", f"pageNumber={page}")
        else:
            if re.search(r"pageNumber=\d+", base_url):
                url = re.sub(r"pageNumber=\d+", f"pageNumber={page}", base_url)
            else:
                url = f"{base_url}&pageNumber={page}"
        urls.append(url)

    return urls


def is_data_complete(data: dict) -> bool:

    required_fields = ["номер контракта", "стоимость контракта", "Инн"]

    for field in required_fields:
        value = data.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return False

    # Дополнительная проверка для числовых полей
    if not isinstance(data.get("стоимость контракта"), (int, float)):
        return False

    return True


def add_random_delay(min_seconds=1, max_seconds=3):

    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)
    return delay


def save_to_excel(data_list: list[dict], filename: str = EXCEL_FILE) -> list[str]:
    """
    Сохраняет данные в Excel с корректной обработкой дубликатов.
    Использует комбинацию (номер контракта + ИНН + год) как уникальный ключ.
    """

    if not data_list:
        print("  Нет данных для сохранения")
        return []

    # Фильтруем только полные данные
    complete_data = []
    incomplete_urls = []

    for data in data_list:
        if is_data_complete(data):
            complete_data.append(data)
        else:
            incomplete_urls.append(data.get("ссылка", "неизвестная ссылка"))

    if not complete_data:
        print("  Нет полных данных для сохранения")
        if incomplete_urls:
            print(f"  Неполные данные (не сохранены): {incomplete_urls}")
        return []

    if incomplete_urls:
        print(f"  Пропущено неполных записей: {len(incomplete_urls)}")

    try:
        df_new = pd.DataFrame(complete_data)
        saved_urls = []

        # КОНВЕРТИРУЕМ ТИПЫ ДАННЫХ В НОВЫХ ДАННЫХ
        numeric_columns = ["стоимость контракта", "выручка", "прибыль"]
        for col in numeric_columns:
            if col in df_new.columns:
                df_new[col] = pd.to_numeric(df_new[col], errors="coerce")

        string_columns = [
            "Инн",
            "номер контракта",
            "отрасль",
            "регион",
            "ссылка",
            "год",
        ]
        for col in string_columns:
            if col in df_new.columns:
                df_new[col] = df_new[col].astype(str)

        # Нормализуем ИНН в новых данных
        if "Инн" in df_new.columns:
            df_new["Инн_норм"] = df_new["Инн"].apply(normalize_inn)

        # Если файл существует, загружаем его
        if os.path.exists(filename):
            # Читаем существующий файл без указания dtype
            existing_df = pd.read_excel(filename)

            # Убеждаемся, что колонки имеют правильные типы
            for col in numeric_columns:
                if col in existing_df.columns:
                    existing_df[col] = pd.to_numeric(existing_df[col], errors="coerce")

            for col in string_columns:
                if col in existing_df.columns:
                    existing_df[col] = existing_df[col].astype(str)

            # Нормализуем ИНН в существующих данных
            if "Инн" in existing_df.columns:
                existing_df["Инн_норм"] = existing_df["Инн"].apply(normalize_inn)

            # СОЗДАЕМ СЛОВАРЬ ДЛЯ БЫСТРОГО ПОИСКА ПО КЛЮЧУ (НОМЕР КОНТРАКТА + ИНН + ГОД)
            # Создаем составной ключ в существующих данных
            existing_df["composite_key"] = existing_df.apply(
                lambda row: (
                    f"{str(row.get('номер контракта', '')).strip()}_{str(row.get('Инн_норм', '')).strip()}_{str(row.get('год', '')).strip()}"
                    if pd.notna(row.get("номер контракта"))
                    and pd.notna(row.get("Инн_норм"))
                    and pd.notna(row.get("год"))
                    else None
                ),
                axis=1,
            )

            # Создаем составной ключ в новых данных
            df_new["composite_key"] = df_new.apply(
                lambda row: (
                    f"{str(row.get('номер контракта', '')).strip()}_{str(row.get('Инн_норм', '')).strip()}_{str(row.get('год', '')).strip()}"
                    if pd.notna(row.get("номер контракта"))
                    and pd.notna(row.get("Инн_норм"))
                    and pd.notna(row.get("год"))
                    else None
                ),
                axis=1,
            )

            # Создаем словарь для быстрого поиска по составному ключу
            key_to_index = {}
            for idx, row in existing_df.iterrows():
                key_value = row.get("composite_key")
                if key_value and pd.notna(key_value):
                    key_to_index[key_value] = idx

            print(
                f"  В существующем файле найдено {len(key_to_index)} уникальных записей (по номеру+ИНН+год)"
            )

            # Разделяем новые данные на обновляемые и добавляемые
            updated_indices = set()
            new_rows = []

            for _, new_row in df_new.iterrows():
                new_key = new_row.get("composite_key")
                new_url = new_row.get("ссылка")

                if new_url:
                    saved_urls.append(str(new_url))

                # ПРОВЕРЯЕМ ПО СОСТАВНОМУ КЛЮЧУ (НОМЕР КОНТРАКТА + ИНН + ГОД)
                if new_key and pd.notna(new_key) and new_key in key_to_index:
                    # Обновляем существующую запись
                    idx = key_to_index[new_key]
                    for col in new_row.index:
                        # Пропускаем служебные колонки и ключ
                        if col not in ["Инн_норм", "composite_key"]:
                            if (
                                pd.notna(new_row[col])
                                and str(new_row[col]).strip() != ""
                            ):
                                # Преобразуем значение к правильному типу
                                value = new_row[col]

                                # Для числовых колонок конвертируем в float
                                if col in numeric_columns:
                                    try:
                                        if pd.notna(value) and str(value).strip() != "":
                                            value = float(value)
                                        else:
                                            value = np.nan
                                    except:
                                        value = np.nan
                                # Для строковых колонок конвертируем в str
                                elif col in string_columns:
                                    value = (
                                        str(value)
                                        if pd.notna(value) and str(value).strip() != ""
                                        else ""
                                    )

                                # Обновляем только если новое значение не пустое
                                if (
                                    isinstance(value, float) and not pd.isna(value)
                                ) or (isinstance(value, str) and value != ""):
                                    existing_df.at[idx, col] = value

                    updated_indices.add(idx)
                    print(f"    Обновлена запись с ключом: {new_key}")
                else:
                    # Добавляем как новую запись
                    new_rows.append(new_row)

            # Добавляем новые строки
            if new_rows:
                df_new_to_add = pd.DataFrame(new_rows)
                # Убеждаемся, что новые данные имеют правильные типы
                df_new_to_add = df_new_to_add.convert_dtypes()
                df_combined = pd.concat([existing_df, df_new_to_add], ignore_index=True)
            else:
                df_combined = existing_df

            # Удаляем служебные колонки
            columns_to_drop = ["Инн_норм", "composite_key"]
            for col in columns_to_drop:
                if col in df_combined.columns:
                    df_combined = df_combined.drop(columns=[col])

            df_to_save = df_combined

            print(f"  Обновлено записей: {len(updated_indices)}")
            print(f"  Добавлено новых записей: {len(new_rows)}")

        else:
            # Если файла нет, просто сохраняем новые данные
            # Удаляем служебные колонки
            columns_to_drop = ["Инн_норм"]
            if "composite_key" in df_new.columns:
                columns_to_drop.append("composite_key")

            df_to_save = df_new.drop(
                columns=[col for col in columns_to_drop if col in df_new.columns]
            )

            # Сохраняем все ссылки из полных данных
            saved_urls = [
                str(data.get("ссылка")) for data in complete_data if data.get("ссылка")
            ]

        # Сохраняем результат
        df_to_save.to_excel(filename, index=False, engine="openpyxl")
        print(f"  Данные сохранены в {filename} (всего записей: {len(df_to_save)})")

        return saved_urls

    except Exception as e:
        print(f"  Ошибка при сохранении в Excel: {e}")

        traceback.print_exc()
        return []


def safe_get(driver, url, max_retries=3, timeout=60):
    """Безопасный GET с повторными попытками"""
    for attempt in range(max_retries):
        try:
            print(f"  Попытка {attempt + 1}/{max_retries} загрузить: {url}")
            driver.set_page_load_timeout(timeout)
            driver.get(url)
            return True
        except Exception as e:
            print(
                f"  Попытка {attempt + 1}/{max_retries} не удалась: {type(e).__name__}"
            )
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10  # Увеличивающаяся задержка
                print(f"  Ждем {wait_time} секунд перед повторной попыткой...")
                time.sleep(wait_time)

                # Если это таймаут, пробуем перезагрузить драйвер
                if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                    try:
                        print("  Пробуем восстановить соединение...")
                        driver.refresh()
                    except:
                        # Если refresh не работает, создаем новый драйвер
                        print("  Создаем новый драйвер...")
                        try:
                            driver.quit()
                        except:
                            pass
                        time.sleep(5)
                        try:
                            options = webdriver.ChromeOptions()
                            options.add_argument("--headless=new")
                            options.add_argument("--no-sandbox")
                            options.add_argument("--disable-dev-shm-usage")
                            options.add_argument(
                                "--disable-blink-features=AutomationControlled"
                            )
                            options.add_experimental_option(
                                "excludeSwitches", ["enable-automation"]
                            )
                            options.add_experimental_option(
                                "useAutomationExtension", False
                            )
                            options.add_argument(
                                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
                            )
                            driver = webdriver.Chrome(options=options)
                            driver.set_page_load_timeout(timeout)
                        except Exception as new_driver_error:
                            print(
                                f"  Не удалось создать новый драйвер: {new_driver_error}"
                            )
                            return False
    return False


def safe_find_element(driver, by, value, timeout=10):
    """Безопасный поиск элемента с повторными попытками"""
    for attempt in range(3):
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception as e:
            if attempt < 2:
                print(
                    f"  Попытка {attempt + 1}/3 найти элемент не удалась, ждем 2 секунды..."
                )
                time.sleep(2)
            else:
                print(f"  Элемент не найден после 3 попыток: {by}={value}")
                raise e


def check_driver_connection(driver):
    """Проверяет, что драйвер подключен и работает"""
    try:
        # Простая проверка через получение заголовка страницы
        title = driver.title
        return True
    except Exception:
        return False


def main():
    global driver
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"Weekly task executed at {current_time}"
    logger.info(message)

    # Улучшенные опции Chrome для стабильности
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--proxy-server='direct://'")
    options.add_argument("--proxy-bypass-list=*")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    )

    # Создаем драйвер с обработкой ошибок
    try:
        print("Запуск ChromeDriver...")
        driver = webdriver.Chrome(options=options)

        # Устанавливаем таймауты
        driver.set_page_load_timeout(60)
        driver.set_script_timeout(30)
        driver.implicitly_wait(10)

        print("ChromeDriver успешно запущен")
    except Exception as e:
        print(f"Ошибка запуска ChromeDriver: {e}")
        print("Попытка перезапуска через 10 секунд...")
        time.sleep(10)

        # Вторая попытка с более простыми настройками
        try:
            simple_options = webdriver.ChromeOptions()
            simple_options.add_argument("--headless=new")
            simple_options.add_argument("--no-sandbox")
            simple_options.add_argument("--disable-dev-shm-usage")
            driver = webdriver.Chrome(options=simple_options)
            driver.set_page_load_timeout(60)
            print("ChromeDriver запущен со второй попытки")
        except Exception as e2:
            print(f"Вторая попытка также не удалась: {e2}")
            return

    global_batch_data = []
    global_checked_urls = {}
    global_driver = driver  # Сохраняем для обработчика прерываний

    # ============== ИСПОЛЬЗУЕМ ПУТИ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ==============
    excel_filename = EXCEL_FILE
    CHECKED_URLS_FILE_MAIN = CHECKED_URLS_FILE
    # =====================================================================

    try:
        # Список всех URL для обработки по годам
        urls_by_year = {
            "2023": URL_FILTERED_2023,
            "2024": URL_FILTERED_2024,
            "2025": URL_FILTERED_2025,
        }

        all_links = []  # Собираем все ссылки со всех годов
        all_successful_data = []  # Для статистики
        batch_data = []  # Для накопления данных между сохранениями
        global_batch_data = batch_data

        # Загружаем уже проверенные URL
        checked_urls = load_json(CHECKED_URLS_FILE_MAIN, {})
        global_checked_urls = checked_urls
        print(f"Уже проверено URL: {len(checked_urls)}")

        # Обрабатываем каждый год
        for year, base_url in urls_by_year.items():
            print(f"\n{'='*60}")
            print(f"НАЧИНАЕМ ОБРАБОТКУ {year} ГОДА")
            print(f"{'='*60}")

            print(f"\nОпределяем количество страниц для {year} года...")

            # Используем safe_get для загрузки основной страницы
            if not safe_get(driver, base_url, max_retries=3, timeout=90):
                print(
                    f"Не удалось загрузить основную страницу для {year} года: {base_url}"
                )
                # Пробуем сбросить драйвер
                try:
                    driver.quit()
                    time.sleep(5)
                    driver = webdriver.Chrome(options=options)
                    driver.set_page_load_timeout(60)
                    print(f"Драйвер пересоздан, пробуем снова для {year} года...")
                    if not safe_get(driver, base_url, max_retries=2, timeout=90):
                        print(
                            f"Не удалось восстановить соединение для {year} года, переходим к следующему году"
                        )
                        continue
                except Exception as reset_error:
                    print(
                        f"Ошибка при пересоздании драйвера для {year} года: {reset_error}"
                    )
                    continue

            time.sleep(3)
            add_random_delay(1, 2)

            total_pages = 20
            print(f"Всего страниц найдено для {year} года: {total_pages}")

            print(f"\nСбор ссылок для {year} года...")
            all_page_urls = generate_pagination_urls(base_url, 1, total_pages)
            year_links = []

            for page_num, page_url in enumerate(all_page_urls, 1):
                print(
                    f"\nСбор ссылок со страницы {page_num}/{total_pages} ({year} год)"
                )

                # Проверяем соединение перед каждой страницей
                if not check_driver_connection(driver):
                    print("  Потеряно соединение с драйвером, пересоздаем...")
                    try:
                        driver.quit()
                        time.sleep(5)
                        driver = webdriver.Chrome(options=options)
                        driver.set_page_load_timeout(60)
                        print("  Драйвер пересоздан")
                    except Exception as e:
                        print(f"  Не удалось пересоздать драйвер: {e}")
                        break

                if not safe_get(driver, page_url, max_retries=2, timeout=60):
                    print(f"  Не удалось загрузить страницу {page_num}, пропускаем")
                    add_random_delay(3, 5)
                    continue

                # Случайная задержка после загрузки страницы
                delay = add_random_delay(2, 4)
                print(f"  Задержка: {delay:.1f} сек")

                css_selector = "div.search-registry-entry-block > div > div > div > div > div:nth-child(1) > a:nth-child(1)"

                try:
                    link_elements = WebDriverWait(driver, 15).until(
                        EC.presence_of_all_elements_located(
                            (By.CSS_SELECTOR, css_selector)
                        )
                    )

                    page_links = []
                    for element in link_elements:
                        href = element.get_attribute("href")
                        if href:
                            page_links.append(href)

                    print(f"  Найдено ссылок: {len(page_links)}")
                    year_links.extend(page_links)

                except Exception as e:
                    print(f"  Ошибка при поиске ссылок: {e}")
                    # Задержка при ошибке
                    add_random_delay(3, 5)
                    continue

            print(f"\nВсего ссылок за {year} год: {len(year_links)}")
            all_links.extend(year_links)

            # Обрабатываем ссылки для текущего года
            links_to_process = year_links[:]

            for i, url in enumerate(links_to_process, 1):
                # Проверяем, не обрабатывали ли мы уже эту ссылку
                if url in checked_urls:
                    print(f"\nПропускаем {i}/{len(links_to_process)} - уже обработана")
                    print(f"URL: {url}")
                    continue

                # Проверяем соединение каждые 10 ссылок
                if i % 10 == 0:
                    if not check_driver_connection(driver):
                        print(
                            "  Проверка соединения: драйвер не отвечает, пересоздаем..."
                        )
                        try:
                            driver.quit()
                            time.sleep(5)
                            driver = webdriver.Chrome(options=options)
                            driver.set_page_load_timeout(60)
                            print("  Драйвер пересоздан")
                        except Exception as e:
                            print(f"  Не удалось пересоздать драйвер: {e}")
                            break

                try:
                    print(f"\nОбработка {i}/{len(links_to_process)} ({year} год)")
                    print(f"URL: {url}")

                    if not safe_get(driver, url, max_retries=2, timeout=60):
                        print(f"  Не удалось загрузить страницу контракта, пропускаем")
                        add_random_delay(3, 6)
                        continue

                    # Случайная задержка после загрузки страницы
                    delay = add_random_delay(1, 3)
                    print(f"  Задержка: {delay:.1f} сек")

                    data = {
                        "ссылка": url,
                        "номер контракта": None,
                        "стоимость контракта": None,
                        "Инн": "",
                        "отрасль": None,
                        "выручка": None,
                        "прибыль": None,
                        "регион": None,
                        "год": year,  # Добавляем год для статистики
                    }

                    # Парсинг контракта с безопасным поиском
                    try:
                        purchase_element = safe_find_element(
                            driver,
                            By.CSS_SELECTOR,
                            ".cardMainInfo__purchaseLink > a",
                            timeout=8,
                        )
                        contract_text = purchase_element.text
                        data["номер контракта"] = normalize_contract_number(
                            contract_text
                        )
                        print(f"  Контракт: {data['номер контракта']}")
                    except:
                        print(f"  Контракт: не найден")

                    # Парсинг стоимости
                    try:
                        cost_element = safe_find_element(
                            driver, By.CSS_SELECTOR, ".cost", timeout=8
                        )
                        cost_text = cost_element.text
                        cost_float = parse_cost_value(cost_text)
                        data["стоимость контракта"] = cost_float
                        print(f"  Стоимость: {data['стоимость контракта']}")
                    except:
                        print(f"  Стоимость: не найдена")

                    # Парсинг ИНН
                    try:
                        table_element = safe_find_element(
                            driver,
                            By.CSS_SELECTOR,
                            "td.tableBlock__col > section > span:nth-child(2)",
                            timeout=8,
                        )
                        data["Инн"] = table_element.text
                        print(f"  ИНН: {data['Инн']}")
                    except:
                        print(f"  ИНН: не найден")

                    # Поиск дополнительных данных по ИНН
                    if data["Инн"]:
                        print(f"  Поиск данных на datanewton.ru...")
                        find_inn(driver, data)

                        if data.get("отрасль"):
                            print(f"  Отрасль: {data['отрасль']}")
                        if data.get("выручка"):
                            print(f"  Выручка: {data['выручка']:,}".replace(",", " "))
                        if data.get("прибыль"):
                            print(f"  Прибыль: {data['прибыль']:,}".replace(",", " "))
                        if data.get("регион"):
                            print(f"  Регион: {data['регион']}")

                    # Проверяем, полные ли данные
                    if is_data_complete(data):
                        batch_data.append(data)
                        all_successful_data.append(data)
                        print(f"  Данные полные, добавлены в очередь сохранения")
                    else:
                        print(f"  Данные неполные, НЕ будут сохранены")

                    # Периодическое сохранение (каждые 5 полных записей)
                    if len(batch_data) >= 5:
                        print(
                            f"\n  Сохранение данных (пачка из {len(batch_data)} записей)..."
                        )
                        saved_urls = save_to_excel(batch_data, excel_filename)

                        if saved_urls:
                            # Добавляем успешно сохраненные ссылки в checked_urls
                            for saved_url in saved_urls:
                                checked_urls[saved_url] = True

                            # Сохраняем updated checked_urls
                            save_json(checked_urls, CHECKED_URLS_FILE_MAIN)
                            print(f"  Обновлено checked_urls: {len(saved_urls)} ссылок")

                            # Запускаем функции фильтрации после сохранения пачки
                            clear_filter_contracts_data(
                                input_file=EXCEL_FILE, output_file=FINAL_OUTPUT_PATH3
                            )
                            filter_contracts_data(
                                input_file=FINAL_OUTPUT_PATH3,
                                output_file=FINAL_OUTPUT_PATH,
                            )
                            weak_filter_contracts_data(
                                input_file=FINAL_OUTPUT_PATH3,
                                output_file=FINAL_OUTPUT_PATH2,
                            )

                            # Очищаем batch_data
                            batch_data = []
                            global_batch_data = batch_data
                        else:
                            print(f"  Не удалось сохранить данные, оставляем в очереди")

                except Exception as e:
                    print(f"  Ошибка при обработке: {e}")
                    # Задержка при ошибке
                    add_random_delay(3, 6)
                    continue

            print(f"\n{'='*60}")
            print(f"ЗАВЕРШЕНА ОБРАБОТКА {year} ГОДА")
            print(f"{'='*60}")

        # Финальное сохранение оставшихся данных после обработки всех годов
        if batch_data:
            print(
                f"\n  Финальное сохранение данных (осталось {len(batch_data)} записей)..."
            )
            saved_urls = save_to_excel(batch_data, excel_filename)

            if saved_urls:
                # Добавляем успешно сохраненные ссылки в checked_urls
                for saved_url in saved_urls:
                    checked_urls[saved_url] = True

                # Сохраняем updated checked_urls
                save_json(checked_urls, CHECKED_URLS_FILE_MAIN)
                print(f"  Обновлено checked_urls: {len(saved_urls)} ссылок")

                # Запускаем финальную фильтрацию
                clear_filter_contracts_data(
                    input_file=EXCEL_FILE, output_file=FINAL_OUTPUT_PATH3
                )
                filter_contracts_data(
                    input_file=FINAL_OUTPUT_PATH3, output_file=FINAL_OUTPUT_PATH
                )
                weak_filter_contracts_data(
                    input_file=FINAL_OUTPUT_PATH3, output_file=FINAL_OUTPUT_PATH2
                )

            else:
                print(f"  Не удалось сохранить финальные данные")

        print(f"\n{'='*60}")
        print(f"ОБРАБОТКА ВСЕХ ГОДОВ ЗАВЕРШЕНА")
        print(f"{'='*60}")

        # Статистика по годам
        year_stats = {}
        for data in all_successful_data:
            year = data.get("год", "неизвестно")
            if year not in year_stats:
                year_stats[year] = 0
            year_stats[year] += 1

        print(f"\nСтатистика по годам:")
        for year, count in year_stats.items():
            print(f"  {year} год: {count} записей")

        print(f"\nОбщая статистика:")
        print(f"Всего ссылок собрано: {len(all_links)}")
        print(f"Уже проверено URL: {len(checked_urls)}")
        print(
            f"Проверено сейчас: {len([v for v in checked_urls.values() if v is True])}"
        )
        print(f"Обработано полных записей: {len(all_successful_data)}")
        print(f"Файл с данными: {excel_filename}")
        print(f"Файл проверенных URL: {CHECKED_URLS_FILE_MAIN}")

        # Итоговая статистика по успешно сохраненным данным
        if all_successful_data:
            print(f"\n{'='*50}")
            print(f"ИТОГОВАЯ СТАТИСТИКА (по успешно сохраненным данным):")

            contracts_found = sum(
                1 for d in all_successful_data if d.get("номер контракта")
            )
            costs_found = sum(
                1
                for d in all_successful_data
                if isinstance(d.get("стоимость контракта"), (int, float))
            )
            inns_found = sum(1 for d in all_successful_data if d.get("Инн"))
            revenues_found = sum(1 for d in all_successful_data if d.get("выручка"))
            profits_found = sum(1 for d in all_successful_data if d.get("прибыль"))

            print(f"  Контрактов найдено: {contracts_found}/{len(all_successful_data)}")
            print(f"  Стоимостей найдено: {costs_found}/{len(all_successful_data)}")
            print(f"  ИНН найдено: {inns_found}/{len(all_successful_data)}")
            print(f"  Выручек найдено: {revenues_found}/{len(all_successful_data)}")
            print(f"  Прибылей найдено: {profits_found}/{len(all_successful_data)}")

        print(f"\n{'='*50}")
        print(f"ФИЛЬТРАЦИЯ ДАННЫХ ЗАВЕРШЕНА")
        print(f"{'='*50}")

    except Exception as e:
        print(f"Критическая ошибка в main: {e}")

        traceback.print_exc()

        # Попытка сохранить прогресс при критической ошибке
        save_progress_on_interrupt()

    finally:
        print("\nЗавершение работы драйвера...")
        try:
            time.sleep(3)
            driver.quit()
        except:
            pass
        print("Драйвер закрыт")


# for DOCKER TO START EVERY DAY-WEEK
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger


if __name__ == "__main__":
    # Регистрируем обработчик прерывания
    signal.signal(signal.SIGINT, signal_handler)
    scheduler = BlockingScheduler()

    # Запустится сразу при старте (триггер 'date' выполняет задачу один раз сейчас)
    scheduler.add_job(main, trigger="date", id="initial_run", name="Run now on startup")

    scheduler.add_job(
        main,
        CronTrigger(day_of_week="mon", hour=9, minute=0),  # Понедельник
        id="weekly_monday_9am",
        name="Weekly Monday Report",
        replace_existing=True,
    )
    scheduler.start()
