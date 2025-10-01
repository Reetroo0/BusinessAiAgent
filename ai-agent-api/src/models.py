from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from langchain.tools.base import tool
from langchain.callbacks.manager import CallbackManagerForToolRun

import json

from pathlib import Path

# helper to load runtime company data on demand (so API can pass fresh data or file can be read)
def load_company_data(path: str | Path = None) -> Dict:
    """Load company data from given path or from default `data.json` next to this module.

    Returns a dict. Raises FileNotFoundError if not present.
    """
    if path is None:
        path = Path(__file__).parent / 'data.json'
    else:
        path = Path(path)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Вес каждой категории
weights = {
    "formalization_level": 1,
    "automation_systems": 2,
    "kpi_metrics": 1,
    "data_driven_decisions": 1,
    "it_systems_used": 2,
    "systems_integration": 1,
    "cloud_services_usage": 1,
    "info_security_measures": 1,
    "digital_literacy": 1,
    "training_programs": 1,
    "it_specialists_in_house": 1,
    "employees_automation_perception": 1,
    "it_strategy": 1,
    "state_electronic_services": 1,
    "future_implementation_plans": 1,
}

significance_map = {
    'yes': 1,
    'mostly_yes': 0.8,
    'mostly_no': 0.2,
    'no': 0,
    'unknown': None
}

max_possible_points = sum(weights.values())

# Функция подсчета балла цифровой зрелости
def calculate_digital_maturity_score(company_data: Dict) -> tuple[float, List[str], List[str]]:
    """Calculate maturity score using provided company_data dict.

    Raises KeyError if required attributes are missing. Values are expected to be strings
    mapping to significance_map keys (case-insensitive). Unknown/None values will raise.
    """
    total_points = 0.0
    used_weights = 0.0
    missing_attrs: List[str] = []
    unknown_values: List[str] = []

    # Проходим по каждому атрибуту и его весу
    for attr, weight in weights.items():
        value = company_data.get(attr)

        # Если атрибут отсутствует — помечаем и продолжаем
        if value is None:
            missing_attrs.append(attr)
            continue

        if not isinstance(value, str):
            raise ValueError(f'Атрибут "{attr}" должен быть строкой, получено: {type(value)}')

        mapped_value = significance_map.get(value.lower())

        # Если значение неизвестно в карте значимости — считаем его неизвестным и пропускаем
        if mapped_value is None:
            unknown_values.append(attr)
            continue

        # Учитываем вес в знаменателе и добавляем взвешенный балл
        used_weights += weight
        total_points += mapped_value * weight

    # Если какие-то обязательные поля отсутствуют, вернём это отдельно
    # (анализатор решит, как реагировать)
    if missing_attrs:
        # процент вычислять не будем, вернём None и список отсутствующих
        return (0.0, missing_attrs, unknown_values)

    if used_weights == 0:
        # Невозможно вычислить оценку — нет валидных значений
        raise ValueError('Нет достаточных валидных данных для расчёта уровня цифровой зрелости. Проверьте входные поля.')

    # Вычисляем процент относительно используемых (известных) весов
    percentage = (total_points / used_weights) * 100
    return (round(percentage, 2), missing_attrs, unknown_values)



# Функция №1:Анализ цифровой зрелости
@tool
def analyze_digital_maturity() -> str:
    """
    Оценивает уровень цифровой зрелости компании на основе ее характеристик.

    """
    print("Вызвана функция: analyze_digital_maturity")
    # load fresh data on each invocation
    company_data = load_company_data()
    try:
        score, missing_attrs, unknown_values = calculate_digital_maturity_score(company_data)
    except ValueError as e:
        return f"Кажется, возникла небольшая проблема с оценкой уровня цифровой зрелости. {e}"
    except Exception as e:
        return f"Кажется, возникла небольшая проблема с оценкой уровня цифровой зрелости. {e}"

    if missing_attrs:
        missing_list = ', '.join(missing_attrs)
        return f"Отсутствуют необходимые поля для расчёта цифровой зрелости: {missing_list}. Пожалуйста, заполните их и попробуйте снова."

    note = ''
    if unknown_values:
        note = f" Учтите: поля {', '.join(unknown_values)} помечены как 'unknown' и были пропущены при расчёте."

    if score <= 40:
        result = "низкий"
    elif score <= 70:
        result = "средний"
    else:
        result = "высокий"

    return f'Цифровая зрелость вашей компании составляет {score}% ({result}).{note}'

#print(analyze_digital_maturity.invoke(""))

# Функция №2: Рекомендации по внедрению ИТ-решений и их применению
@tool
def recommend_it_solutions():
    """
        Делает рекомендации по внедрению ИТ-решений на основе данных о компании (характеристик)

    """
    print("Вызвана функция: recommend_it_solutions")
    company_data = load_company_data()
    # Создаем словарь с условиями и соответствующими решениями
    it_recommendations_map = {
        'formalization_level': ('Нет формализации процессов', ['CRM']),
        'automation_systems': ('Отсутствие автоматизации основных бизнес-процессов', ['СЭД']),
        'kpi_metrics': ('Использование показателей KPI без автоматизированных решений', ['BI-система', 'Big Data Analytics']),
        'data_driven_decisions': ('Решение задач без опоры на цифровые технологии', ['Data-driven система поддержки принятия решений']),
        'it_systems_used': ('Необходимо больше использовать современные ИТ-системы', ['Автоматизированные системы учета и отчетности']),
        'systems_integration': ('Невозможность интеграции существующих систем', ['Средства интеграции приложений']),
        'cloud_services_usage': ('Недостаточное использование облачных сервисов', ['Облачные сервисы']),
        'info_security_measures': ('Проблемы с уровнем информационной безопасности', ['Политика безопасности']),
        'digital_literacy': ('Низкий уровень цифровой грамотности сотрудников', ['Программы повышения квалификации персонала']),
        'training_programs': ('Отсутствуют программы обучения сотрудников', ['Программа подготовки кадров']),
        'it_specialists_in_house': ('Отсутствие внутренних ИТ-специалистов', ['Привлечение сторонних консультантов или создание собственной команды']),
        'employees_automation_perception': ('Негативное отношение сотрудников к автоматизации', ['Мероприятия по повышению осведомленности о преимуществах автоматизации']),
        'it_strategy': ('Отсутствие стратегии внедрения ИТ-технологий', ['Создание ИТ-стратегии компании'])
    }

    # Список возможных рекомендаций
    recommended_solutions = []

    for key, value in company_data.items():
        if key not in it_recommendations_map:
            continue
        condition, solutions = it_recommendations_map[key]
        # consider non-empty and meaningful values
        if isinstance(value, str) and value.strip():
            # only recommend if value indicates a problem (e.g., 'no' or 'mostly_no')
            if value.lower() in ('no', 'mostly_no', 'unknown'):
                recommended_solutions.extend(solutions)

    return ', '.join(recommended_solutions)


# Функция №2 дополнение: Описание конкретных ИТ-решений

_BASE_DIR = Path(__file__).parent
# Чтение JSON-файла и загрузка данных в словарь (статические базы)
with open(_BASE_DIR / 'IT_solutions_database.json', encoding='utf-8') as file:  # Используйте нужную кодировку
    IT_solutions = json.load(file)

@tool
def show_all_IT_solutions() -> Dict:
    """
    Выводит подробный список всех описаний конкретных ИТ-решений из базы данных.

    Returns: Dict: Словарь с информацией об ИТ-решениях
    """
    print("Вызвана функция: show_all_IT_solutions")
    IT_solutions_list = IT_solutions
    return(IT_solutions_list)

# Функция №3: Подбор мер господдержки

# Чтение JSON-файла и загрузка данных в словарь
with open(_BASE_DIR / 'grants_database.json', encoding='utf-8') as file:  # Используйте нужную кодировку
    grants = json.load(file)

from datetime import datetime

@tool
def show_all_available_support() -> Dict:
    """
    Просто выводим список всех доступных мер поддержки из базы данных.

    Returns: Dict: Словарь с информацией о мерах поддержки (название и описание)
    """
    print("Вызвана функция: show_all_available_support")
    available_support_list = grants
    return(available_support_list)
