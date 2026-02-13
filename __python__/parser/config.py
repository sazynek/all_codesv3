import os

URL_FILTERED_2025 = "https://zakupki.gov.ru/epz/contract/search/results.html?morphology=on&search-filter=%D0%94%D0%B0%D1%82%D0%B5+%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D1%8F&fz44=on&fz94=on&contractStageList_0=on&contractStageList_1=on&contractStageList_2=on&contractStageList_3=on&contractStageList=0%2C1%2C2%2C3&contractPriceFrom=10000000&currencyCode=RUB&budgetLevelsIdNameHidden=%7B%7D&publishDateFrom=01.01.2025&publishDateTo=31.12.2025&sortBy=UPDATE_DATE&pageNumber=1&sortDirection=false&recordsPerPage=_50&showLotsInfoHidden=false"
URL_FIND_INN = "https://datanewton.ru/"


FINAL_OUTPUT_PATH = os.getenv(
    "FINAL_OUTPUT_PATH", "/app/output/filtered_contracts.xlsx"
)
FINAL_OUTPUT_PATH2 = os.getenv(
    "FINAL_OUTPUT_PATH2", "/app/output/weak_filtered_contracts.xlsx"
)
FINAL_OUTPUT_PATH3 = os.getenv(
    "FINAL_OUTPUT_PATH3", "/app/output/cleared_contracts.xlsx"
)


EXCEL_FILE = os.getenv("EXCEL_FILE", "/app/data/contracts_data.xlsx")

CHECKED_URLS_FILE = os.getenv("CHECKED_URLS_FILE", "/app/data/checked_urls.json")


URL_FILTERED_2023 = "https://zakupki.gov.ru/epz/contract/search/results.html?morphology=on&search-filter=%D0%94%D0%B0%D1%82%D0%B5+%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D1%8F&fz44=on&fz94=on&contractStageList_0=on&contractStageList_1=on&contractStageList_2=on&contractStageList_3=on&contractStageList=0%2C1%2C2%2C3&contractPriceFrom=10000000&currencyCode=RUB&budgetLevelsIdNameHidden=%7B%7D&publishDateFrom=01.01.2023&publishDateTo=31.12.2023&sortBy=UPDATE_DATE&pageNumber=1&sortDirection=false&recordsPerPage=_50&showLotsInfoHidden=false"

URL_FILTERED_2024 = "https://zakupki.gov.ru/epz/contract/search/results.html?morphology=on&search-filter=%D0%94%D0%B0%D1%82%D0%B5+%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D1%8F&fz44=on&fz94=on&contractStageList_0=on&contractStageList_1=on&contractStageList_2=on&contractStageList_3=on&contractStageList=0%2C1%2C2%2C3&contractPriceFrom=10000000&currencyCode=RUB&budgetLevelsIdNameHidden=%7B%7D&publishDateFrom=01.01.2024&publishDateTo=31.12.2024&sortBy=UPDATE_DATE&pageNumber=1&sortDirection=false&recordsPerPage=_50&showLotsInfoHidden=false"
