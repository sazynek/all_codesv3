import pytest
import pandas as pd
import tempfile
import os
import time
from unittest.mock import Mock, MagicMock, patch
from selenium.webdriver.common.by import By
import sys

# Добавляем путь к модулю
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем функции (замените на имя вашего модуля)
try:
    from main import (
        parse_money_value,
        parse_cost_value,
        normalize_inn,
        normalize_contract_number,
        is_data_complete,
        generate_pagination_urls,
        add_random_delay,
        save_to_excel,
        filter_contracts_data,
        find_financial_values,
        find_financial_values_alternative,
        extract_region_from_page,
        find_inn,
    )

    MODULE_IMPORTED = True
except ImportError:
    MODULE_IMPORTED = False
    print("Внимание: не удалось импортировать модуль, создаем заглушки")


# Мок-объекты для Selenium
class MockWebElement:
    def __init__(self, text="", attribute=None):
        self.text = text
        self._attribute = attribute or {}

    def find_element(self, *args, **kwargs):
        return MockWebElement()

    def find_elements(self, *args, **kwargs):
        return []

    def get_attribute(self, name):
        return self._attribute.get(name, "")

    def click(self):
        pass

    def send_keys(self, keys):
        pass

    def __repr__(self):
        return f"MockWebElement(text='{self.text}')"


class MockWebDriver:
    def __init__(self):
        self.page_source = ""

    def find_element(self, *args, **kwargs):
        return MockWebElement()

    def find_elements(self, *args, **kwargs):
        return []

    def get(self, url):
        pass

    def execute_script(self, script, element):
        pass

    def quit(self):
        pass


# Тесты начинаются здесь
if not MODULE_IMPORTED:
    pytest.skip("Модуль не импортирован", allow_module_level=True)


# ==================== ТЕСТЫ ДЛЯ parse_money_value ====================
@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("2,8 млрд. ₽", 2800000000),
        ("-50,5 млн. ₽", -50500000),
        ("100 тыс. ₽", 100000),
        ("1,5 трлн. ₽", 1500000000000),
        ("100 000 ₽", 100000),
        ("123", 123),
        ("", None),
        ("abc", None),
        (None, None),
        ("0 ₽", 0),
        ("-0 ₽", 0),
    ],
)
def test_parse_money_value_basic(input_str, expected):
    """Тестируем базовый парсинг денежных значений"""
    result = parse_money_value(input_str)
    assert result == expected


# ==================== ТЕСТЫ ДЛЯ parse_cost_value ====================
@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("15 000 000 ₽", 15000000.0),
        ("1,500,000 ₽", 1500000.0),
        ("1000000", 1000000.0),
        ("1.000.000", 1000000.0),
        ("", None),
        ("abc", None),
    ],
)
def test_parse_cost_value_basic(input_str, expected):
    """Тестируем парсинг стоимости"""
    result = parse_cost_value(input_str)
    assert result == expected


# ==================== ТЕСТЫ ДЛЯ normalize_inn ====================
@pytest.mark.parametrize(
    "input_val,expected",
    [
        ("1234567890", "1234567890"),
        (" 1234567890 ", "1234567890"),
        ("ИНН: 1234567890", "1234567890"),
        (1234567890, "1234567890"),
        ("12-34-567890", "1234567890"),
        ("", None),
        (None, None),
    ],
)
def test_normalize_inn(input_val, expected):
    """Тестируем нормализацию ИНН"""
    result = normalize_inn(input_val)
    assert result == expected


# ==================== ТЕСТЫ ДЛЯ normalize_contract_number ====================
@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("№123/2024", "123/2024"),
        ("123/2024", "123/2024"),
        ("  № 456/2023  ", "456/2023"),
        ("", None),
        (None, None),
    ],
)
def test_normalize_contract_number(input_str, expected):
    """Тестируем нормализацию номера контракта"""
    result = normalize_contract_number(input_str)
    assert result == expected


# ==================== ТЕСТЫ ДЛЯ is_data_complete ====================
@pytest.mark.parametrize(
    "data,expected",
    [
        # Полные данные
        (
            {
                "номер контракта": "123/2024",
                "стоимость контракта": 15000000,
                "Инн": "1234567890",
            },
            True,
        ),
        # Неполные данные
        (
            {
                "номер контракта": "",
                "стоимость контракта": 15000000,
                "Инн": "1234567890",
            },
            False,
        ),
        (
            {
                "номер контракта": "123/2024",
                "стоимость контракта": None,
                "Инн": "1234567890",
            },
            False,
        ),
        (
            {"номер контракта": "123/2024", "стоимость контракта": 15000000, "Инн": ""},
            False,
        ),
        # Некорректный тип стоимости
        (
            {
                "номер контракта": "123/2024",
                "стоимость контракта": "15 млн",
                "Инн": "1234567890",
            },
            False,
        ),
    ],
)
def test_is_data_complete(data, expected):
    """Тестируем проверку полноты данных"""
    result = is_data_complete(data)
    assert result == expected


# ==================== ТЕСТЫ ДЛЯ generate_pagination_urls ====================
@pytest.mark.parametrize(
    "base_url,start,end,expected_count",
    [
        ("https://example.com?pageNumber=1", 1, 5, 5),
        ("https://example.com?pageNumber=1", 2, 4, 3),
        ("https://example.com?page=1", 1, 3, 3),
        ("https://example.com", 1, 2, 2),
    ],
)
def test_generate_pagination_urls(base_url, start, end, expected_count):
    """Тестируем генерацию URL для пагинации"""
    urls = generate_pagination_urls(base_url, start, end)
    assert len(urls) == expected_count
    assert f"pageNumber={start}" in urls[0]
    assert f"pageNumber={end}" in urls[-1]


# ==================== ТЕСТЫ ДЛЯ add_random_delay ====================
def test_add_random_delay():
    """Тестируем добавление случайной задержки"""
    start_time = time.time()
    delay = add_random_delay(0.001, 0.002)  # Минимальные значения для теста
    end_time = time.time()

    actual_delay = end_time - start_time
    assert 0.001 <= delay <= 0.002
    assert actual_delay >= 0.001


# ==================== ТЕСТЫ ДЛЯ save_to_excel ====================
def test_save_to_excel_new_file():
    """Тестируем сохранение в новый Excel файл"""
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Тест с полными данными
        complete_data = [
            {
                "номер контракта": "123/2024",
                "стоимость контракта": 15000000,
                "Инн": "1234567890",
                "ссылка": "https://example.com/123",
            }
        ]

        saved_urls = save_to_excel(complete_data, tmp_path)

        assert len(saved_urls) == 1
        assert saved_urls[0] == "https://example.com/123"
        assert os.path.exists(tmp_path)

        # Проверяем содержимое файла
        df = pd.read_excel(tmp_path)
        assert len(df) == 1
        assert df.iloc[0]["Инн"] == "1234567890"

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_save_to_excel_incomplete_data():
    """Тестируем сохранение неполных данных"""
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Тест с неполными данными
        incomplete_data = [
            {
                "номер контракта": "",  # Пустое поле
                "стоимость контракта": 15000000,
                "Инн": "1234567890",
                "ссылка": "https://example.com/456",
            }
        ]

        saved_urls = save_to_excel(incomplete_data, tmp_path)
        assert len(saved_urls) == 0

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_save_to_excel_update_existing():
    """Тестируем обновление существующего файла"""
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Создаем исходный файл
        initial_data = [
            {
                "номер контракта": "123/2024",
                "стоимость контракта": 15000000,
                "Инн": "1234567890",
                "отрасль": "Торговля",
                "ссылка": "https://example.com/123",
            }
        ]

        save_to_excel(initial_data, tmp_path)

        # Обновляем данные
        update_data = [
            {
                "номер контракта": "123/2024",
                "стоимость контракта": 18000000,  # Обновленная стоимость
                "Инн": "1234567890",  # Тот же ИНН
                "отрасль": "Торговля оптовая",  # Обновленная отрасль
                "ссылка": "https://example.com/123",
            }
        ]

        saved_urls = save_to_excel(update_data, tmp_path)
        assert len(saved_urls) == 1

        # Проверяем, что данные обновились
        df = pd.read_excel(tmp_path)
        assert len(df) == 1
        assert df.iloc[0]["стоимость контракта"] == 18000000

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ==================== ТЕСТЫ ДЛЯ filter_contracts_data ====================
def test_filter_contracts_data_success():
    """Тестируем успешную фильтрацию данных"""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.xlsx")
        output_path = os.path.join(tmpdir, "output.xlsx")

        # Создаем тестовые данные
        test_data = [
            {
                "номер контракта": "123/2024",
                "стоимость контракта": 15000000,
                "Инн": "1234567890",
                "отрасль": "46.46 Торговля оптовая фармацевтической продукцией",
                "выручка": 2800000000,
                "прибыль": -50500000,
                "регион": "Москва",
            },
            {
                "номер контракта": "124/2024",
                "стоимость контракта": 5000000,  # Меньше 10 млн - будет отфильтровано
                "Инн": "0987654321",
                "отрасль": "45.31 Торговля",
                "выручка": 50000000,  # Меньше 100 млн - будет отфильтровано
                "прибыль": 5000000,  # Меньше 10 млн - будет отфильтровано
                "регион": "Якутия",  # Будет отфильтровано
            },
        ]

        pd.DataFrame(test_data).to_excel(input_path, index=False)

        # Патчим внешние зависимости
        with patch("main.extract_okved_codes") as mock_extract, patch(
            "main.get_industries_by_okved"
        ) as mock_get_ind:

            mock_extract.return_value = []
            mock_get_ind.return_value = []

            result = filter_contracts_data(
                input_file=input_path, output_file=output_path
            )

            assert result is True
            assert os.path.exists(output_path)

            # Проверяем результат
            df_output = pd.read_excel(output_path)
            assert len(df_output) == 1
            assert df_output.iloc[0]["номер контракта"] == "123/2024"


def test_filter_contracts_data_file_not_found():
    """Тестируем фильтрацию при отсутствии файла"""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "output.xlsx")

        result = filter_contracts_data(
            input_file="non_existent_file.xlsx", output_file=output_path
        )

        assert result is False


# ==================== ТЕСТЫ ДЛЯ find_financial_values ====================
def test_find_financial_values_no_data():
    """Тестируем поиск финансовых показателей, когда данных нет"""
    driver = MockWebDriver()

    revenue, profit = find_financial_values(driver)

    assert revenue is None
    assert profit is None


def test_find_financial_values_with_mocks():
    """Тестируем поиск финансовых показателей с моками"""
    driver = MockWebDriver()

    # Патчим find_elements чтобы имитировать поиск
    with patch.object(driver, "find_elements") as mock_find:
        # Создаем мок элемента
        mock_element = MockWebElement(text="Выручка")
        mock_find.return_value = [mock_element]

        revenue, profit = find_financial_values(driver)

        # Проверяем, что функция была вызвана
        assert mock_find.called
        assert revenue is None  # Не найдены денежные значения в моке


# ==================== ТЕСТЫ ДЛЯ find_financial_values_alternative ====================
def test_find_financial_values_alternative_no_data():
    """Тестируем альтернативный поиск финансовых показателей, когда данных нет"""
    driver = MockWebDriver()

    revenue, profit = find_financial_values_alternative(driver)

    assert revenue is None
    assert profit is None


# ==================== ТЕСТЫ ДЛЯ extract_region_from_page ====================
def test_extract_region_from_page_no_data():
    """Тестируем извлечение региона, когда данных нет"""
    driver = MockWebDriver()

    result = extract_region_from_page(driver)

    assert result is None


# ==================== ТЕСТЫ ДЛЯ find_inn ====================
def test_find_inn_basic():
    """Тестируем базовый вызов find_inn"""
    driver = MockWebDriver()
    data = {"Инн": "1234567890"}

    # Патчим все зависимости
    with patch("main.URL_FIND_INN", "http://test.com"), patch(
        "main.WebDriverWait"
    ) as mock_wait, patch("main.time.sleep"), patch("main.EC") as mock_ec, patch(
        "main.extract_region_from_page"
    ) as mock_extract_region:

        # Настраиваем моки
        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance

        mock_element = MockWebElement()

        driver.find_elements = Mock(return_value=[mock_element])

        mock_extract_region.return_value = "Москва"

        # Вызываем функцию
        result = find_inn(driver, data)

        # Проверяем, что регион был добавлен
        assert result["регион"] == "Москва"


# ==================== ИНТЕГРАЦИОННЫЕ ТЕСТЫ ====================
class TestIntegration:
    """Интеграционные тесты"""

    def test_full_flow_with_mocks(self):
        """Тестируем полный поток с моками"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Создаем тестовые данные
            test_data = [
                {
                    "номер контракта": "123/2024",
                    "стоимость контракта": 15000000,
                    "Инн": "1234567890",
                    "отрасль": "46.46 Торговля оптовая фармацевтической продукцией",
                    "выручка": 2800000000,
                    "прибыль": -50500000,
                    "регион": "Москва",
                }
            ]

            input_path = os.path.join(tmpdir, "contracts_data.xlsx")
            output_path = os.path.join(tmpdir, "filtered_contracts.xlsx")

            pd.DataFrame(test_data).to_excel(input_path, index=False)

            # Патчим внешние зависимости
            with patch("main.extract_okved_codes") as mock_extract, patch(
                "main.get_industries_by_okved"
            ) as mock_get_ind:

                mock_extract.return_value = ["46.46"]
                mock_get_ind.return_value = ["торговля"]

                # Тестируем фильтрацию
                result = filter_contracts_data(
                    input_file=input_path, output_file=output_path
                )

                assert result is True
                assert os.path.exists(output_path)

                # Проверяем, что данные сохранились
                df = pd.read_excel(output_path)
                assert len(df) == 1
                assert df.iloc[0]["номер контракта"] == "123/2024"

    def test_save_and_filter_integration(self):
        """Интеграционный тест сохранения и фильтрации"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Тест 1: Сохраняем данные
            data_path = os.path.join(tmpdir, "data.xlsx")
            filtered_path = os.path.join(tmpdir, "filtered.xlsx")

            test_data = [
                {
                    "номер контракта": "123/2024",
                    "стоимость контракта": 20000000,  # > 10 млн
                    "Инн": "1234567890",
                    "отрасль": "строительство",
                    "выручка": 200000000,  # > 100 млн
                    "прибыль": 15000000,  # > 10 млн
                    "регион": "Москва",
                }
            ]

            # Сохраняем
            saved_urls = save_to_excel(test_data, data_path)
            assert len(saved_urls) == 1

            # Тест 2: Фильтруем (с моками)
            with patch("main.extract_okved_codes") as mock_extract, patch(
                "main.get_industries_by_okved"
            ) as mock_get_ind:

                mock_extract.return_value = ["41.20"]
                mock_get_ind.return_value = ["строительство"]

                result = filter_contracts_data(
                    input_file=data_path, output_file=filtered_path
                )

                assert result is True
                assert os.path.exists(filtered_path)


# ==================== ТЕСТЫ ДЛЯ ГРАНИЧНЫХ СЛУЧАЕВ ====================
class TestEdgeCases:
    """Тесты для граничных случаев"""

    @pytest.mark.parametrize(
        "input_str,expected",
        [
            ("0 ₽", 0),
            ("-0 ₽", 0),
            ("0,0 млн. ₽", 0),
            ("9,999 млн. ₽", 9999000),
            ("1 234 567,89 ₽", 1234567),
        ],
    )
    def test_parse_money_value_edge_cases(self, input_str, expected):
        """Тестируем граничные случаи парсинга денежных значений"""
        result = parse_money_value(input_str)
        assert result == expected

    @pytest.mark.parametrize(
        "data,expected",
        [
            # Минимально допустимые данные
            ({"номер контракта": "1", "стоимость контракта": 1, "Инн": "1"}, True),
            # Пограничные значения стоимости
            (
                {"номер контракта": "123", "стоимость контракта": 0.0001, "Инн": "123"},
                True,
            ),
        ],
    )
    def test_is_data_complete_edge_cases(self, data, expected):
        """Тестируем граничные случаи проверки полноты данных"""
        result = is_data_complete(data)
        assert result == expected

    def test_save_to_excel_edge_cases(self):
        """Тестируем граничные случаи сохранения в Excel"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Тест с пустыми данными
            empty_data = []
            saved_urls = save_to_excel(empty_data, tmp_path)
            assert len(saved_urls) == 0
            assert not os.path.exists(tmp_path)  # Файл не должен создаваться

            # Тест с None в данных
            data_with_none = [
                {
                    "номер контракта": None,
                    "стоимость контракта": 15000000,
                    "Инн": "1234567890",
                    "ссылка": "https://example.com/123",
                }
            ]

            saved_urls = save_to_excel(data_with_none, tmp_path)
            assert len(saved_urls) == 0

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


# ==================== ТЕСТЫ ДЛЯ ОШИБОК ====================
class TestErrorHandling:
    """Тесты обработки ошибок"""

    def test_parse_money_value_invalid_input(self):
        """Тестируем обработку невалидных входных данных"""
        invalid_inputs = [
            "не число",
            "123abc",
            "###",
            "123.456.789",  # Слишком много точек
        ]

        for input_str in invalid_inputs:
            result = parse_money_value(input_str)
            assert result is None, f"Ожидался None для '{input_str}', получено {result}"

    def test_save_to_excel_invalid_filename(self):
        """Тестируем сохранение с невалидным именем файла"""
        data = [
            {
                "номер контракта": "123/2024",
                "стоимость контракта": 15000000,
                "Инн": "1234567890",
                "ссылка": "https://example.com/123",
            }
        ]

        # Пытаемся сохранить в несуществующую директорию
        invalid_path = "/несуществующая/директория/file.xlsx"

        # Это должно вызвать ошибку, но функция должна ее обработать
        saved_urls = save_to_excel(data, invalid_path)
        assert len(saved_urls) == 0


# ==================== ФИКСТУРЫ ====================
@pytest.fixture
def sample_data_dict():
    """Фикстура с примером словаря данных"""
    return {
        "Инн": "1234567890",
        "номер контракта": "123/2024",
        "стоимость контракта": 15000000,
        "отрасль": None,
        "выручка": None,
        "прибыль": None,
        "регион": None,
        "ссылка": "https://example.com/123",
    }


@pytest.fixture
def temp_excel_file(tmp_path):
    """Фикстура с временным Excel файлом"""
    file_path = tmp_path / "test_contracts.xlsx"
    df = pd.DataFrame(
        [
            {
                "номер контракта": "123/2024",
                "стоимость контракта": 15000000,
                "Инн": "1234567890",
                "отрасль": "46.46 Торговля оптовая",
                "выручка": 2800000000,
                "прибыль": -50500000,
            }
        ]
    )
    df.to_excel(file_path, index=False)
    return str(file_path)


@pytest.fixture
def mock_driver():
    """Фикстура с моком драйвера"""
    return MockWebDriver()


# ==================== ПАРАМЕТРИЗОВАННЫЕ ТЕСТЫ ====================
@pytest.mark.parametrize(
    "function_name,test_cases",
    [
        (
            "parse_money_value",
            [
                ("10 млн. ₽", 10000000),
                ("0,5 млрд. ₽", 500000000),
                ("-100 тыс. ₽", -100000),
            ],
        ),
        (
            "parse_cost_value",
            [
                ("10 000 ₽", 10000.0),
                ("1.234,56 ₽", 1234.56),
            ],
        ),
    ],
)
def test_parametrized_functions(function_name, test_cases, request):
    """Параметризованный тест для разных функций"""
    func = (
        request.getfixturevalue(function_name)
        if hasattr(request, "getfixturevalue")
        else globals()[function_name]
    )

    for input_val, expected in test_cases:
        result = func(input_val)
        assert (
            result == expected
        ), f"Ошибка для {function_name}('{input_val}'): ожидалось {expected}, получено {result}"


# ==================== МОДУЛЬНЫЕ ТЕСТЫ ====================
@pytest.mark.module
class TestModuleLevel:
    """Тесты на уровне модуля"""

    def test_all_functions_imported(self):
        """Проверяем, что все функции импортированы"""
        functions = [
            parse_money_value,
            parse_cost_value,
            normalize_inn,
            normalize_contract_number,
            is_data_complete,
            generate_pagination_urls,
            add_random_delay,
            save_to_excel,
            filter_contracts_data,
        ]

        for func in functions:
            assert callable(func), f"Функция {func.__name__} не является вызываемой"

    def test_function_signatures(self):
        """Проверяем сигнатуры функций"""
        # parse_money_value
        result = parse_money_value("10 млн. ₽")
        assert result is None or isinstance(result, int)

        # parse_cost_value
        result = parse_cost_value("10000 ₽")
        assert result is None or isinstance(result, float)

        # normalize_inn
        result = normalize_inn("1234567890")
        assert result is None or isinstance(result, str)
