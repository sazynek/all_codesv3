# import requests


from typing import Any
from bs4 import BeautifulSoup as soup

# text
import html2text

# selenium
from selenium import webdriver
from selenium.webdriver.common.by import By

# from selenium.webdriver.remote.webelement import WebElement

options = webdriver.ChromeOptions()
# options.add_argument("--headless=new")  # The recommended new headless mode
options.add_argument("--disable-gpu")

service = webdriver.ChromeService()


def get_selenium_html(url: str) -> str:

    driver = webdriver.Chrome(options=options, service=service)
    # driver = webdriver.Chrome()

    # driver.ge
    driver.get(url)

    d = driver.page_source
    driver.quit()
    return d


def parser_by_url(url: str):

    text = get_selenium_html(url)
    # print(f"raw {text}")
    parse_html2text(text)


def parse_html2text(text: str) -> str:
    h = html2text.HTML2Text()
    h.ignore_links = True  # Не выводить ссылки
    h.ignore_images = True  # Не выводить изображения
    h.ignore_tables = True  # Игнорировать таблицы (или использовать bypass_tables)
    h.ignore_emphasis = False  # Раскомментировать, чтобы убрать **жирный** и _курсив_
    h.unicode_snob = True  # Использовать "умные" кавычки и тире

    # print("RAW ", text)
    s = soup(text, "lxml")
    res = s.select_one("html body")
    # print("AFTER PARSE", res)
    if res is not None:
        html = res.prettify()
        # print(html)
        # print(html)
        text = h.handle(html)
    return text


import time


def parse_tariff_ya(url: str = "https://taxi.yandex.ru/spb/tariff/"):

    driver = webdriver.Chrome(options=options, service=service)

    driver.get(url)
    elements = driver.find_elements(
        By.CSS_SELECTOR,
        ".HorizTabs a",
    )
    links_data: list[dict[str, str]] = []  # type: ignore
    for elem in elements:
        href: str | None = elem.get_attribute("href")  # type: ignore
        text: str = elem.text  # type: ignore
        # assert isinstance(text, str)
        if href is not None:  # type: ignore
            links_data.append({"href": href, "text": text})  # type: ignore

    time.sleep(2)
    for i in links_data:  # type: ignore
        if i.get("href", None):  # type: ignore
            driver.get(i["href"])  # type: ignore
            time.sleep(1)
            page_content = driver.page_source
            s = soup(page_content, "lxml")
            res = s.select_one("html body main")
            if res is not None:
                res = res.select_one(".TariffDetails__main-price")
                if res:
                    res = res.prettify()
                    print("=" * 90, "\n")
                    str = parse_html2text(res)

                    res = i["text"] + "\n" + str
                    print(res)
                    print("=" * 90, "\n")


def parse_parks_ya(url: str = "https://taxi.yandex.ru/spb/parks") -> str:

    driver = webdriver.Chrome(options=options, service=service)

    driver.get(url)
    infinite_scroll(driver)

    elements = driver.find_elements(
        By.CSS_SELECTOR,
        "div.Park:nth-child > a:nth-child(1)",
    )
    links_data: list[Any] = []
    for elem in elements:
        href: str | None = elem.get_attribute("href")  # type: ignore
        if href:
            links_data.append(href)  # type: ignore

    time.sleep(2)
    for href in links_data:
        if href:
            driver.get(href)
            time.sleep(1)
            page_content = driver.page_source
            s = soup(page_content, "lxml")
            res = s.select_one("html body main")
            if res is not None:
                res = res.select_one(".ParkDetails__content")
                if res is not None:

                    res_header = res.select_one(".ParkDetails__header")
                    tariff = res.select_one("#react-select-tariffSelect--value-item")

                    price_group = res.select_one(".PriceGroup")

                    res = res.prettify()
                    print("=" * 90, "\n")
                    parse_html2text(res)
                    print("=" * 90, "\n")
    return ""


# @delete


def infinite_scroll(driver: webdriver.Chrome, scroll_delay: int = 1):
    """
    Простая бесконечная прокрутка ReactVirtualized контейнера
    """

    container = driver.find_element(
        By.CSS_SELECTOR,
        "#application > div.Core > div > main > div.Parks__content > aside > div > div.ParkList__list-wrap > div:nth-child(1) > div",
    )

    print("🌀 Начинаю бесконечную прокрутку...")
    print("Нажмите Ctrl+C в терминале, чтобы остановить")

    scroll_count = 0
    last_height = 0
    # div.Park:nth-child(6) > a:nth-child(1)
    try:
        while True:
            scroll_count += 1

            # Прокручиваем в самый низ
            driver.execute_script(  # type: ignore
                "arguments[0].scrollTop = arguments[0].scrollHeight;", container
            )

            print(f"📜 Прокрутка #{scroll_count}")
            time.sleep(scroll_delay)
            current_height = driver.execute_script(  # type: ignore
                "return arguments[0].scrollHeight;", container
            )

            if current_height > last_height:
                print(f"   Высота увеличилась: {last_height} → {current_height}")
                last_height = current_height
            else:
                break

    except KeyboardInterrupt:
        print(f"\n⏹️  Прокрутка остановлена пользователем")
        print(f"Всего прокруток: {scroll_count}")
        print(f"Итоговая высота: {last_height}")


def parse_knowledge_base_ya(
    url: str = "https://pro.yandex.ru/ru-ru/knowledge-base",
):

    driver = webdriver.Chrome(options=options, service=service)

    driver.get(url)
    infinite_scroll(driver)

    elements = driver.find_elements(
        By.CSS_SELECTOR,
        "div.profession_professionItem__25iWE > div > a",
    )
    links_data: list[Any] = []
    for elem in elements:
        href: str | None = elem.get_attribute("href")  # type: ignore
        if href:
            links_data.append(href)  # type: ignore

    # time.sleep(2)
    # for href in links_data:
    #     if href:
    #         driver.get(href)
    #         time.sleep(1)
    #         page_content = driver.page_source
    #         s = soup(page_content, "lxml")
    #         res = s.select_one("html body main")
    #         if res is not None:
    #             res = res.select_one(".ParkDetails__content")
    #             if res is not None:

    #                 res_header = res.select_one(".ParkDetails__header")
    #                 tariff = res.select_one("#react-select-tariffSelect--value-item")

    #                 price_group = res.select_one(".PriceGroup")

    #                 res = res.prettify()
    #                 print("=" * 90, "\n")
    #                 parse_html2text(res)
    #                 print("=" * 90, "\n")


# @delete

parse_knowledge_base_ya()
# parse_tariff_ya()
# parse_parks_ya()

# parser_by_url("https://taxi.yandex.ru/spb/parks")


# parser_by_url("https://pro.yandex.ru/ru-ru/knowledge-base")
# parser_by_url("https://pikabu.ru/community/taxi")

# parser_by_url("https://web.telegram.org/#@igormylnikovchannelchat")

# https://t.me/igormylnikovchannelchat
