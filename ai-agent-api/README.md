# AI-Agent — Консультант по цифровой зрелости

Лёгкий серверный проект на Python, который принимает данные о компании, оценивает её цифровую зрелость и даёт рекомендации по ИT-решениям и мерам поддержки, используя набор локальных инструментов и внешний чат-модельный сервис (GigaChat).

## Структура проекта

- `requirements.txt` — зависимости проекта.
- `src/` — исходный код:
  - `main.py` — инициализация агента и функция `run_agent(question, headers=...)`.
  - `api.py` — FastAPI-приложение; публичный эндпоинт `/digitalMaturity`.
  - `models.py` — набор инструментов (анализ зрелости, рекомендации, базы данных) используемых агентом.
  - `data.json` — runtime-данные компании (заполняется API перед вызовом агента).
  - `IT_solutions_database.json`, `grants_database.json` — статические базы данных решений и мер поддержки.
  - `Test-run.py` — простой пример вызова `run_agent`.

## Что делает сервис

1. Принимает JSON с характеристиками компании.
2. Сохраняет его в `src/data.json`.
3. Запускает агент (GigaChat через langchain/langgraph), который использует локальные инструменты из `models.py` для оценки и рекомендаций.
4. Возвращает текстовый результат в JSON.

## Требования

- Python 3.11+ (проект использует зависимости, указанные в `requirements.txt`).

Установите зависимости, например в virtualenv:

```fish
python -m venv venv
source venv/bin/activate.fish
pip install -r requirements.txt
```

> Примечание: если вы используете другую оболочку (bash/zsh), используйте соответствующий activate-скрипт.

## Переменные окружения

Проект использует токен доступа к Gigachat, который должен быть задан в `.env` или в окружении:

- `GIGACHAT_ACCESS_TOKEN` — токен доступа (не публикуйте в публичных репозиториях).
- Опционально: `DEBUG_AGENT_PAYLOAD=1` — при запуске включает печать сообщений, отправляемых агенту, для отладки.

Пример `.env` (в корне проекта):

```
GIGACHAT_ACCESS_TOKEN=ваш_токен_здесь
```

## Запуск API

Запуск через модульный запуск uvicorn (рекомендуется в development):

```fish
# включить debug-печать payload (опционально)
set -x DEBUG_AGENT_PAYLOAD 1
# запустить сервис
python -m uvicorn src.api:app --host 0.0.0.0 --port 8000
```

Или напрямую (файл `src/api.py` содержит точку входа):

```fish
python src/api.py
```

## Эндпоинт

GET /digitalMaturity
- Ожидает JSON тело запроса со следующей схемой (все поля — строки, значения: `yes`, `mostly_yes`, `mostly_no`, `no`, `unknown`):

```json
{
  "formalization_level": "mostly_no",
  "automation_systems": "no",
  "kpi_metrics": "mostly_yes",
  "data_driven_decisions": "no",
  "it_systems_used": "mostly_no",
  "systems_integration": "no",
  "cloud_services_usage": "yes",
  "info_security_measures": "yes",
  "digital_literacy": "mostly_yes",
  "training_programs": "unknown",
  "it_specialists_in_house": "mostly_yes",
  "employees_automation_perception": "yes",
  "it_strategy": "no",
  "state_electronic_services": "yes",
  "future_implementation_plans": "unknown"
}
```

Пример запроса (fish shell):

```fish
curl -v -X GET http://127.0.0.1:8000/digitalMaturity \
  -H 'Content-Type: application/json' \
  -d '{"formalization_level":"mostly_no","automation_systems":"no","kpi_metrics":"mostly_yes","data_driven_decisions":"no","it_systems_used":"mostly_no","systems_integration":"no","cloud_services_usage":"yes","info_security_measures":"yes","digital_literacy":"mostly_yes","training_programs":"unknown","it_specialists_in_house":"mostly_yes","employees_automation_perception":"yes","it_strategy":"no","state_electronic_services":"yes","future_implementation_plans":"unknown"}'
```

Ответ:

```json
{"result": "Цифровая зрелость вашей компании составляет 62.5% (средний)."}
```

Если какие-то обязательные поля отсутствуют, API вернёт сообщение вида:

```json
{"result": "Отсутствуют необходимые поля для расчёта цифровой зрелости: training_programs. Пожалуйста, заполните их и попробуйте снова."}
```

## Логика расчёта

- Вес каждой категории объявлен в `src/models.py`.
- Значения маппируются: `yes`=1, `mostly_yes`=0.8, `mostly_no`=0.2, `no`=0, `unknown` — игнорируется при расчёте.
- Балл считается относительно доступных (не-unknown) полей.

## Отладка и распространённые ошибки

- 422 от Gigachat: чаще всего возникает, если клиент автоматически пытается передать `company_data` как структурный параметр (JSON Schema). В текущей реализации API сохраняет `src/data.json` и инструменты читают его локально — это предотвращает проблему. Если вы по-прежнему видите 422, включите `DEBUG_AGENT_PAYLOAD=1` и посмотрите, какие сообщения отправляются на сервис.

- Ошибки при запуске: проверьте, что `GIGACHAT_ACCESS_TOKEN` задан и что зависимости установлены.

## Тесты и улучшения (рекомендации)

- Добавить unit-тесты (pytest) для `calculate_digital_maturity_score` (happy path, unknowns, missing fields).
- Сделать API POST вместо GET (более корректно для тела запроса) — многие прокси не отправляют тела в GET.
- Безопасность: не логируйте токен, используйте секретный менеджер в проде.
- Производительность: текущая архитектура сохраняет `data.json` и инструменты читают файл; можно улучшить передачу данных через memory/checkpointer или напрямую передавать в инструменты.

## Контакты

Если нужна помощь с развёртыванием или доработками — опишите желаемое поведение, и я подготовлю патчи/тесты.
