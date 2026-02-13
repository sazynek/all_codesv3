import pandas as pd
from collections import Counter
from okved_categories import *
from config import *


def extract_okved_codes_from_string(industry_string):
    if pd.isna(industry_string):
        return []

    codes = []
    activities = str(industry_string).split(";")

    for activity in activities:
        activity = activity.strip()
        if activity:
            parts = activity.split()
            if parts:
                potential_code = parts[0]
                if any(char.isdigit() for char in potential_code):
                    cleaned_code = "".join(
                        c for c in potential_code if c.isdigit() or c == "."
                    )
                    if cleaned_code:
                        codes.append(cleaned_code)

    return codes


def clear_filter_contracts_data(
    input_file: str = EXCEL_FILE,
    output_file: str = FINAL_OUTPUT_PATH3,
):
    try:
        df = pd.read_excel(input_file)

        print(f"\n{'='*60}")
        print(f"ОЧИСТКА ДАННЫХ ОТ ПУСТЫХ ЗАПИСЕЙ")
        print(f"{'='*60}")
        print(f"Всего записей до очистки: {len(df)}")

        key_columns = [
            "Инн",
            "номер контракта",
            "стоимость контракта",
            "отрасль",
            "выручка",
            "прибыль",
            "регион",
            "год",
        ]

        existing_key_columns = [col for col in key_columns if col in df.columns]

        missing_columns = [
            col for col in key_columns if col not in existing_key_columns
        ]
        if missing_columns:
            print(
                f"\nВНИМАНИЕ: Отсутствуют следующие обязательные колонки: {missing_columns}"
            )
            print("  Будет выполнена очистка только по имеющимся колонкам.")

        print(f"\nПУСТЫЕ ЗНАЧЕНИЯ ПО КОЛОНКАМ:")
        for col in existing_key_columns:
            empty_count = df[col].isna().sum()
            if col == "отрасль":
                empty_strings_count = (
                    df[col]
                    .apply(lambda x: isinstance(x, str) and x.strip() == "")
                    .sum()
                )
                total_empty = empty_count + empty_strings_count
                print(
                    f"  {col}: {total_empty} пустых (NaN: {empty_count}, пустые строки: {empty_strings_count})"
                )
            else:
                print(f"  {col}: {empty_count} пустых")

        initial_count = len(df)

        if "отрасль" in existing_key_columns:
            df["отрасль"] = df["отрасль"].apply(
                lambda x: None if (isinstance(x, str) and x.strip() == "") else x
            )

        df = df.dropna(subset=existing_key_columns)
        filtered_count = initial_count - len(df)

        print(f"\nОтфильтровано записей с пустыми полями: {filtered_count}")
        print(f"Осталось записей после очистки: {len(df)}")

        # Определяем порядок колонок: год должен быть последним
        required_columns_order = [
            "номер контракта",
            "стоимость контракта",
            "Инн",
            "отрасль",
            "выручка",
            "прибыль",
            "регион",
            "год",  # ГОД ДОЛЖЕН БЫТЬ ПОСЛЕДНИМ
        ]

        # Оставляем только существующие колонки в нужном порядке
        final_columns = [col for col in required_columns_order if col in df.columns]

        # Проверяем, что год действительно есть
        if "год" in final_columns:
            # Убедимся, что год идет последним
            if final_columns[-1] != "год":
                # Перемещаем год в конец
                final_columns = [col for col in final_columns if col != "год"] + ["год"]
                print(f"  Внимание: год перемещен в конец списка колонок")

        final_missing_columns = [
            col for col in required_columns_order if col not in final_columns
        ]
        if final_missing_columns:
            print(
                f"\nВНИМАНИЕ: После очистки отсутствуют колонки: {final_missing_columns}"
            )
            print("  Будет сохранен файл только с имеющимися колонками.")

        df = df[final_columns]

        # Форматирование числовых колонок
        if "стоимость контракта" in df.columns:
            try:
                df["стоимость контракта"] = pd.to_numeric(
                    df["стоимость контракта"], errors="coerce"
                )
                df["стоимость контракта"] = df["стоимость контракта"].apply(
                    lambda x: (
                        f"{x:,.2f}".replace(",", " ").replace(".", ",")
                        if pd.notna(x)
                        else ""
                    )
                )
            except Exception as e:
                print(f"  Ошибка при форматировании 'стоимость контракта': {e}")

        if "выручка" in df.columns:
            try:
                df["выручка"] = pd.to_numeric(df["выручка"], errors="coerce")
                df["выручка"] = df["выручка"].apply(
                    lambda x: (
                        f"{x:,.0f}".replace(",", " ").replace(".", ",")
                        if pd.notna(x)
                        else ""
                    )
                )
            except Exception as e:
                print(f"  Ошибка при форматировании 'выручка': {e}")

        if "прибыль" in df.columns:
            try:
                df["прибыль"] = pd.to_numeric(df["прибыль"], errors="coerce")
                df["прибыль"] = df["прибыль"].apply(
                    lambda x: (
                        f"{x:,.0f}".replace(",", " ").replace(".", ",")
                        if pd.notna(x)
                        else ""
                    )
                )
            except Exception as e:
                print(f"  Ошибка при форматировании 'прибыль': {e}")

        # Сохраняем результат
        df.to_excel(output_file, index=False)

        print(f"\n{'='*60}")
        print(f"ОЧИСТКА ЗАВЕРШЕНА:")
        print(f"  Осталось записей: {len(df)}")
        print(f"  Файл сохранен: {output_file}")
        print(f"  Порядок колонок: {list(df.columns)}")

        if len(df) > 0:
            print(f"\nСТАТИСТИКА ОЧИЩЕННЫХ ДАННЫХ:")
            for col in final_columns:
                if col in ["стоимость контракта", "выручка", "прибыль"]:
                    try:
                        temp_series = df[col].apply(
                            lambda x: (
                                float(str(x).replace(" ", "").replace(",", "."))
                                if pd.notna(x) and str(x).strip() != ""
                                else None
                            )
                        )
                        not_empty = temp_series.notna().sum()
                        print(f"  {col}: {not_empty} непустых значений")
                    except:
                        not_empty = (
                            df[col]
                            .apply(lambda x: pd.notna(x) and str(x).strip() != "")
                            .sum()
                        )
                        print(f"  {col}: {not_empty} непустых значений")
                else:
                    not_empty = (
                        df[col]
                        .apply(lambda x: pd.notna(x) and str(x).strip() != "")
                        .sum()
                    )
                    print(f"  {col}: {not_empty} непустых значений")

            if "год" in df.columns:
                print(f"\nРАСПРЕДЕЛЕНИЕ ПО ГОДАМ:")
                year_stats = df["год"].value_counts().sort_index()
                for year, count in year_stats.items():
                    print(f"  {year}: {count} записей")

        return True

    except Exception as e:
        print(f"Ошибка при очистке данных: {e}")
        import traceback

        traceback.print_exc()
        return False


def filter_contracts_data(
    input_file: str = FINAL_OUTPUT_PATH3,
    output_file: str = FINAL_OUTPUT_PATH,
):
    excluded_regions_far_east = [
        "якутия",
        "саха",
        "камчат",
        "примор",
        "хабаровск",
        "амурск",
        "магадан",
        "сахалин",
        "еврейск",
        "чукот",
        "дальний восток",
        "дальневосточ",
    ]

    excluded_regions_caucasus = [
        "дагестан",
        "ингушетия",
        "кабардино",
        "балкар",
        "карачаево",
        "черкес",
        "осетия",
        "алания",
        "чечен",
        "ставрополь",
        "кавказ",
        "северный кавказ",
    ]

    desired_industries = [
        "строительство",
        "it и связь",
        "здравоохранение",
        "торговля",
        "услуги",
        "производство",
        "разведка и добыча",
        "энергетика и водоснабжение",
        "металлургия",
        "приборостроение",
        "легкая промышленность",
    ]

    try:
        df = pd.read_excel(input_file)

        print(f"\n{'='*60}")
        print(f"ФИЛЬТРАЦИЯ ДАННЫХ")
        print(f"{'='*60}")
        print(f"Всего записей до фильтрации: {len(df)}")

        if "стоимость контракта" in df.columns:
            print("  Преобразование 'стоимость контракта' в числа...")
            df["стоимость_число"] = df["стоимость контракта"].apply(
                lambda x: (
                    float(str(x).replace(" ", "").replace(",", "."))
                    if pd.notna(x) and str(x).strip() != ""
                    else None
                )
            )
        else:
            df["стоимость_число"] = None

        if "выручка" in df.columns:
            print("  Преобразование 'выручка' в числа...")
            df["выручка_число"] = df["выручка"].apply(
                lambda x: (
                    float(str(x).replace(" ", "").replace(",", "."))
                    if pd.notna(x) and str(x).strip() != ""
                    else None
                )
            )
        else:
            df["выручка_число"] = None

        if "прибыль" in df.columns:
            print("  Преобразование 'прибыль' в числа...")
            df["прибыль_число"] = df["прибыль"].apply(
                lambda x: (
                    float(str(x).replace(" ", "").replace(",", "."))
                    if pd.notna(x) and str(x).strip() != ""
                    else None
                )
            )
        else:
            df["прибыль_число"] = None

        if "отрасль" in df.columns:
            df_temp = df.copy()
            df_temp["коды_оквед"] = df_temp["отрасль"].apply(
                extract_okved_codes_from_string
            )
            df_temp["категории_отраслей"] = df_temp["отрасль"].apply(
                get_industries_by_okved
            )

            print(f"\nРАСПРЕДЕЛЕНИЕ ПО ОТРАСЛЯМ ДО ФИЛЬТРАЦИИ:")

            all_categories = []
            for categories_list in df_temp["категории_отраслей"].dropna():
                if isinstance(categories_list, list):
                    all_categories.extend(categories_list)

            if all_categories:
                category_counter = Counter(all_categories)
                for category, count in category_counter.most_common(20):
                    print(f"  {category}: {count}")

            undefined_count = (
                df_temp["категории_отраслей"]
                .apply(lambda x: len(x) == 0 if isinstance(x, list) else True)
                .sum()
            )

            if undefined_count > 0:
                print(f"  Не определено: {undefined_count}")

            activities_count = df_temp["коды_оквед"].apply(
                lambda x: len(x) if isinstance(x, list) else 0
            )
            print(f"\nСТАТИСТИКА ПО ВИДАМ ДЕЯТЕЛЬНОСТИ:")
            print(f"  Среднее количество ОКВЭД: {activities_count.mean():.1f}")
            print(f"  Компаний с одним ОКВЭД: {(activities_count == 1).sum()}")
            print(f"  Компаний с несколькими ОКВЭД: {(activities_count > 1).sum()}")

        if "стоимость_число" in df.columns:
            initial_count = len(df)
            df = df[df["стоимость_число"] >= 10000000]
            filtered_by_cost = initial_count - len(df)
            print(f"\nОтфильтровано по стоимости < 10 млн: {filtered_by_cost}")

        if "выручка_число" in df.columns:
            initial_count = len(df)
            df = df[df["выручка_число"].notna()]
            df = df[
                (df["выручка_число"] >= 100000000) & (df["выручка_число"] <= 5000000000)
            ]
            filtered_by_revenue = initial_count - len(df)
            print(f"Отфильтровано по выручке: {filtered_by_revenue}")

        if "прибыль_число" in df.columns:
            initial_count = len(df)
            df = df[df["прибыль_число"].notna()]
            df = df[df["прибыль_число"] >= 10000000]
            filtered_by_profit = initial_count - len(df)
            print(f"Отфильтровано по прибыли < 10 млн: {filtered_by_profit}")

        if "регион" in df.columns:
            initial_count = len(df)

            def is_excluded_region(region):
                if pd.isna(region):
                    return False
                region_lower = str(region).lower()

                for keyword in excluded_regions_far_east:
                    if keyword in region_lower:
                        return True

                for keyword in excluded_regions_caucasus:
                    if keyword in region_lower:
                        return True

                return False

            excluded_mask = df["регион"].apply(is_excluded_region)
            excluded_count = excluded_mask.sum()
            df = df[~excluded_mask]
            print(f"Отфильтровано по региону (ДВ и Сев.Кавказ): {excluded_count}")

        if "отрасль" in df.columns:
            initial_count = len(df)

            df_temp = df.copy()
            df_temp["категории_отраслей"] = df_temp["отрасль"].apply(
                get_industries_by_okved
            )

            def has_desired_industry(categories_list):
                if not isinstance(categories_list, list):
                    return False
                return any(
                    category in desired_industries for category in categories_list
                )

            industry_mask = df_temp["категории_отраслей"].apply(has_desired_industry)
            undefined_mask = df_temp["категории_отраслей"].apply(
                lambda x: len(x) == 0 if isinstance(x, list) else True
            )

            combined_mask = industry_mask | undefined_mask
            df = df[combined_mask]
            filtered_by_industry = initial_count - len(df)

            print(f"\nОтфильтровано по отраслям: {filtered_by_industry}")

            if len(df) > 0:
                print(f"\nРАСПРЕДЕЛЕНИЕ ПО ОТРАСЛЯМ ПОСЛЕ ФИЛЬТРАЦИИ:")

                df_temp_filtered = df.copy()
                df_temp_filtered["категории_отраслей"] = df_temp_filtered[
                    "отрасль"
                ].apply(get_industries_by_okved)

                all_categories_filtered = []
                for categories_list in df_temp_filtered["категории_отраслей"].dropna():
                    if isinstance(categories_list, list):
                        all_categories_filtered.extend(categories_list)

                if all_categories_filtered:
                    category_counter = Counter(all_categories_filtered)
                    for category, count in category_counter.most_common(10):
                        print(f"  {category}: {count}")

        # Определяем порядок колонок для финального вывода
        required_columns_order = [
            "номер контракта",
            "стоимость контракта",
            "Инн",
            "отрасль",
            "выручка",
            "прибыль",
            "регион",
            "год",  # ГОД В КОНЦЕ
        ]

        # Восстанавливаем отформатированные значения
        if "стоимость_число" in df.columns and "стоимость контракта" not in df.columns:
            df["стоимость контракта"] = df["стоимость_число"].apply(
                lambda x: (
                    f"{x:,.2f}".replace(",", " ").replace(".", ",")
                    if pd.notna(x)
                    else ""
                )
            )

        if "выручка_число" in df.columns and "выручка" not in df.columns:
            df["выручка"] = df["выручка_число"].apply(
                lambda x: (
                    f"{x:,.0f}".replace(",", " ").replace(".", ",")
                    if pd.notna(x)
                    else ""
                )
            )

        if "прибыль_число" in df.columns and "прибыль" not in df.columns:
            df["прибыль"] = df["прибыль_число"].apply(
                lambda x: (
                    f"{x:,.0f}".replace(",", " ").replace(".", ",")
                    if pd.notna(x)
                    else ""
                )
            )

        # Оставляем только существующие колонки в нужном порядке
        final_columns = [col for col in required_columns_order if col in df.columns]

        # Убедимся, что год идет последним (если он есть)
        if "год" in final_columns and final_columns[-1] != "год":
            final_columns = [col for col in final_columns if col != "год"] + ["год"]
            print(f"  Внимание: год перемещен в конец списка колонок")

        # Удаляем временные числовые колонки
        temp_columns_to_remove = ["стоимость_число", "выручка_число", "прибыль_число"]
        for col in temp_columns_to_remove:
            if col in df.columns and col not in final_columns:
                df = df.drop(columns=[col])

        df = df[final_columns]

        print(f"\nОСТАВЛЕНЫ КОЛОНКИ (год в конце): {final_columns}")

        df.to_excel(output_file, index=False)

        print(f"\n{'='*60}")
        print(f"ФИЛЬТРАЦИЯ ЗАВЕРШЕНА:")
        print(f"  Осталось записей: {len(df)}")
        print(f"  Файл сохранен: {output_file}")

        if len(df) > 0:
            print(f"\nФИНАЛЬНАЯ СТАТИСТИКА:")

            if "год" in df.columns:
                print(f"\nРАСПРЕДЕЛЕНИЕ ПО ГОДАМ:")
                year_stats = df["год"].value_counts().sort_index()
                for year, count in year_stats.items():
                    print(f"  {year}: {count} записей")

            if "стоимость_число" in df.columns or "стоимость контракта" in df.columns:
                try:
                    temp_df = df.copy()
                    if "стоимость контракта" in temp_df.columns:
                        temp_df["стоимость_число"] = temp_df[
                            "стоимость контракта"
                        ].apply(
                            lambda x: (
                                float(str(x).replace(" ", "").replace(",", "."))
                                if pd.notna(x) and str(x).strip() != ""
                                else None
                            )
                        )

                    print(f"\nПО СТОИМОСТИ КОНТРАКТОВ:")
                    if "стоимость_число" in temp_df.columns:
                        print(
                            f"  Минимальная: {temp_df['стоимость_число'].min():,.2f}".replace(
                                ",", " "
                            )
                        )
                        print(
                            f"  Максимальная: {temp_df['стоимость_число'].max():,.2f}".replace(
                                ",", " "
                            )
                        )
                        print(
                            f"  Средняя: {temp_df['стоимость_число'].mean():,.2f}".replace(
                                ",", " "
                            )
                        )
                        print(
                            f"  Суммарная: {temp_df['стоимость_число'].sum():,.2f}".replace(
                                ",", " "
                            )
                        )

                except Exception as e:
                    print(f"  Ошибка при расчете статистики стоимости: {e}")

            if "регион" in df.columns:
                print(f"\nТОП-5 РЕГИОНОВ:")
                region_stats = df["регион"].value_counts().head(5)
                for region, count in region_stats.items():
                    print(f"  {region}: {count}")

        return True

    except Exception as e:
        print(f"Ошибка при фильтрации данных: {e}")
        import traceback

        traceback.print_exc()
        return False


def weak_filter_contracts_data(
    input_file: str = FINAL_OUTPUT_PATH3,
    output_file: str = FINAL_OUTPUT_PATH2,
):
    excluded_regions_far_east = [
        "якутия",
        "саха",
        "камчат",
        "примор",
        "хабаровск",
        "амурск",
        "магадан",
        "сахалин",
        "еврейск",
        "чукот",
        "дальний восток",
        "дальневосточ",
    ]

    excluded_regions_caucasus = [
        "дагестан",
        "ингушетия",
        "кабардино",
        "балкар",
        "карачаево",
        "черкес",
        "осетия",
        "алания",
        "чечен",
        "ставрополь",
        "кавказ",
        "северный кавказ",
    ]

    desired_industries = [
        "строительство",
        "it и связь",
        "здравоохранение",
        "торговля",
        "услуги",
        "производство",
        "разведка и добыча",
        "энергетика и водоснабжение",
        "металлургия",
        "приборостроение",
        "легкая промышленность",
    ]

    try:
        df = pd.read_excel(input_file)

        print(f"\n{'='*60}")
        print(f"ОСЛАБЛЕННАЯ ФИЛЬТРАЦИЯ ДАННЫХ")
        print(f"{'='*60}")
        print(f"Всего записей до фильтрации: {len(df)}")

        print("\nПРЕОБРАЗОВАНИЕ ТИПОВ ДАННЫХ:")

        if "выручка" in df.columns:
            print("  'выручка' -> числовой формат...")
            df["выручка_число"] = df["выручка"].apply(
                lambda x: (
                    float(str(x).replace(" ", "").replace(",", "."))
                    if pd.notna(x) and str(x).strip() != ""
                    else None
                )
            )
        else:
            df["выручка_число"] = None

        if "прибыль" in df.columns:
            print("  'прибыль' -> числовой формат...")
            df["прибыль_число"] = df["прибыль"].apply(
                lambda x: (
                    float(str(x).replace(" ", "").replace(",", "."))
                    if pd.notna(x) and str(x).strip() != ""
                    else None
                )
            )
        else:
            df["прибыль_число"] = None

        required_fields = [
            "Инн",
            "номер контракта",
            "стоимость контракта",
            "выручка",
            "прибыль",
            "регион",
            "год",
        ]

        for field in required_fields:
            if field not in df.columns:
                print(f"  Внимание: отсутствует поле '{field}'")

        key_columns = [
            "Инн",
            "номер контракта",
            "стоимость контракта",
            "выручка",
            "прибыль",
            "регион",
            "год",
        ]

        existing_key_columns = [col for col in key_columns if col in df.columns]

        print(f"\nПУСТЫЕ ЗНАЧЕНИЯ ПО КОЛОНКАМ ДО ФИЛЬТРАЦИИ:")
        for col in existing_key_columns:
            empty_count = df[col].isna().sum()
            print(f"  {col}: {empty_count} пустых")

        initial_count = len(df)
        df = df.dropna(subset=existing_key_columns)
        filtered_empty = initial_count - len(df)
        print(f"Отфильтровано записей с пустыми полями: {filtered_empty}")

        if "отрасль" in df.columns:
            df_temp = df.copy()
            df_temp["коды_оквед"] = df_temp["отрасль"].apply(
                extract_okved_codes_from_string
            )
            df_temp["категории_отраслей"] = df_temp["отрасль"].apply(
                get_industries_by_okved
            )

            print(f"\nРАСПРЕДЕЛЕНИЕ ПО ОТРАСЛЯМ ДО ФИЛЬТРАЦИИ:")

            all_categories = []
            for categories_list in df_temp["категории_отраслей"].dropna():
                if isinstance(categories_list, list):
                    all_categories.extend(categories_list)

            if all_categories:
                category_counter = Counter(all_categories)
                for category, count in category_counter.most_common(20):
                    print(f"  {category}: {count}")

            undefined_count = (
                df_temp["категории_отраслей"]
                .apply(lambda x: len(x) == 0 if isinstance(x, list) else True)
                .sum()
            )

            if undefined_count > 0:
                print(f"  Не определено: {undefined_count}")

        if "выручка_число" in df.columns:
            initial_count = len(df)
            df = df[df["выручка_число"] >= 100000000]
            filtered_by_revenue = initial_count - len(df)
            print(f"\nОтфильтровано по выручке < 100 млн: {filtered_by_revenue}")
        else:
            print(
                f"\nВнимание: поле 'выручка' отсутствует или не преобразовано в число"
            )

        if "прибыль_число" in df.columns:
            initial_count = len(df)
            df = df[df["прибыль_число"] >= 10000000]
            filtered_by_profit = initial_count - len(df)
            print(f"Отфильтровано по прибыли < 10 млн: {filtered_by_profit}")
        else:
            print(f"Внимание: поле 'прибыль' отсутствует или не преобразовано в число")

        if "регион" in df.columns:
            initial_count = len(df)

            def is_excluded_region(region):
                if pd.isna(region):
                    return True
                region_lower = str(region).lower()

                for keyword in excluded_regions_far_east:
                    if keyword in region_lower:
                        return True

                for keyword in excluded_regions_caucasus:
                    if keyword in region_lower:
                        return True

                return False

            excluded_mask = df["регион"].apply(is_excluded_region)
            excluded_count = excluded_mask.sum()
            df = df[~excluded_mask]
            print(f"Отфильтровано по региону (ДВ и Сев.Кавказ): {excluded_count}")

        if "отрасль" in df.columns:
            initial_count = len(df)

            df_temp = df.copy()
            df_temp["категории_отраслей"] = df_temp["отрасль"].apply(
                get_industries_by_okved
            )

            def has_desired_industry(categories_list):
                if not isinstance(categories_list, list):
                    return False
                return any(
                    category in desired_industries for category in categories_list
                )

            industry_mask = df_temp["категории_отраслей"].apply(has_desired_industry)
            undefined_mask = df_temp["категории_отраслей"].apply(
                lambda x: len(x) == 0 if isinstance(x, list) else True
            )

            combined_mask = industry_mask | undefined_mask
            df = df[combined_mask]
            filtered_by_industry = initial_count - len(df)

            print(f"Отфильтровано по отраслям: {filtered_by_industry}")

            if len(df) > 0:
                print(f"\nРАСПРЕДЕЛЕНИЕ ПО ОТРАСЛЯМ ПОСЛЕ ФИЛЬТРАЦИИ:")

                df_temp_filtered = df.copy()
                df_temp_filtered["категории_отраслей"] = df_temp_filtered[
                    "отрасль"
                ].apply(get_industries_by_okved)

                all_categories_filtered = []
                for categories_list in df_temp_filtered["категории_отраслей"].dropna():
                    if isinstance(categories_list, list):
                        all_categories_filtered.extend(categories_list)

                if all_categories_filtered:
                    category_counter = Counter(all_categories_filtered)
                    for category, count in category_counter.most_common(10):
                        print(f"  {category}: {count}")

        # Определяем порядок колонок для финального вывода
        required_columns_order = [
            "номер контракта",
            "стоимость контракта",
            "Инн",
            "отрасль",
            "выручка",
            "прибыль",
            "регион",
            "год",  # ГОД В КОНЦЕ
        ]

        # Восстанавливаем отформатированные значения
        if "выручка_число" in df.columns and "выручка" not in df.columns:
            df["выручка"] = df["выручка_число"].apply(
                lambda x: (
                    f"{x:,.0f}".replace(",", " ").replace(".", ",")
                    if pd.notna(x)
                    else ""
                )
            )

        if "прибыль_число" in df.columns and "прибыль" not in df.columns:
            df["прибыль"] = df["прибыль_число"].apply(
                lambda x: (
                    f"{x:,.0f}".replace(",", " ").replace(".", ",")
                    if pd.notna(x)
                    else ""
                )
            )

        # Оставляем только существующие колонки в нужном порядке
        final_columns = [col for col in required_columns_order if col in df.columns]

        # Убедимся, что год идет последним (если он есть)
        if "год" in final_columns and final_columns[-1] != "год":
            final_columns = [col for col in final_columns if col != "год"] + ["год"]
            print(f"  Внимание: год перемещен в конец списка колонок")

        # Удаляем временные числовые колонки
        temp_columns_to_remove = ["выручка_число", "прибыль_число"]
        for col in temp_columns_to_remove:
            if col in df.columns and col not in final_columns:
                df = df.drop(columns=[col])

        df = df[final_columns]

        print(f"\nОСТАВЛЕНЫ КОЛОНКИ (год в конце): {final_columns}")

        df.to_excel(output_file, index=False)

        print(f"\n{'='*60}")
        print(f"ОСЛАБЛЕННАЯ ФИЛЬТРАЦИЯ ЗАВЕРШЕНА:")
        print(f"  Осталось записей: {len(df)}")
        print(f"  Файл сохранен: {output_file}")

        if len(df) > 0:
            print(f"\nФИНАЛЬНАЯ СТАТИСТИКА:")

            if "год" in df.columns:
                print(f"\nРАСПРЕДЕЛЕНИЕ ПО ГОДАМ:")
                year_stats = df["год"].value_counts().sort_index()
                for year, count in year_stats.items():
                    print(f"  {year}: {count} записей")

            if "выручка_число" in df.columns or "выручка" in df.columns:
                try:
                    temp_df = df.copy()
                    if "выручка" in temp_df.columns:
                        temp_df["выручка_число"] = temp_df["выручка"].apply(
                            lambda x: (
                                float(str(x).replace(" ", "").replace(",", "."))
                                if pd.notna(x) and str(x).strip() != ""
                                else None
                            )
                        )

                    print(f"\nПО ВЫРУЧКЕ:")
                    if "выручка_число" in temp_df.columns:
                        print(
                            f"  Минимальная: {temp_df['выручка_число'].min():,.0f}".replace(
                                ",", " "
                            )
                        )
                        print(
                            f"  Максимальная: {temp_df['выручка_число'].max():,.0f}".replace(
                                ",", " "
                            )
                        )
                        print(
                            f"  Средняя: {temp_df['выручка_число'].mean():,.0f}".replace(
                                ",", " "
                            )
                        )

                except Exception as e:
                    print(f"  Ошибка при расчете статистики выручки: {e}")

            if "регион" in df.columns:
                print(f"\nТОП-10 РЕГИОНОВ:")
                region_stats = df["регион"].value_counts().head(10)
                for region, count in region_stats.items():
                    print(f"  {region}: {count}")

        return True

    except Exception as e:
        print(f"Ошибка при ослабленной фильтрации данных: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    clear_filter_contracts_data()
    filter_contracts_data()
    weak_filter_contracts_data()
