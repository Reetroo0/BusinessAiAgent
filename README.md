# BusinessAiAgent — AI агент (API + Telegram Bot)

Полный README для проекта, который включает два подсервиса:

- `ai-agent-api/` — Python API (FastAPI) для оценки цифровой зрелости и рекомендаций.
- `BusinessAiBot/` — Telegram-бот (aiogram) для опросов и взаимодействия с пользователями.

## Краткое описание

Проект сочетает backend-агента (локальные инструменты + внешний LLM-сервис) и чат-бота, который собирает данные и взаимодействует с пользователями.

- API принимает данные о компании, сохраняет их в `ai-agent-api/src/data.json`, запускает агент и возвращает результат.
- Бот использует `BusinessAiBot/app.py`, `BusinessAiBot/config.py` и обработчики в `BusinessAiBot/handlers/`.

## Структура репозитория

- `ai-agent-api/` — сервис API
  - `src/api.py` — FastAPI приложение
  - `src/main.py`, `src/models.py` — логика агента
  - `src/data.json` — runtime данные, которые заполняет API
  - `IT_solutions_database.json`, `grants_database.json` — статические базы данных
- `BusinessAiBot/` — Telegram-бот
  - `app.py` — точка входа бота
  - `config.py` — конфигурация (переменные окружения)
  - `handlers/` — обработчики (`start.py`, `survey.py`)
  - `misc/` — утилиты (функции, клавиатуры, работа с БД)

## Требования

- Python 3.11+
- Docker (опционально, для контейнеризации)
- Зависимости указаны в `ai-agent-api/requirements.txt` и `BusinessAiBot/requirements.txt`.

## Переменные окружения

Объединённый список переменных, используемых в проекте. Некоторые из них — альтернативные имена (например, `TELEGRAM_TOKEN` / `BOT_TOKEN`).

- Для API (`ai-agent-api`):
  - `GIGACHAT_ACCESS_TOKEN` — токен доступа к внешнему LLM (GigaChat). Обязательно для работы агента.
  - `DEBUG_AGENT_PAYLOAD` — (опционально) включить подробный дамп сообщений агента (значение `1`).

- Для бота (`BusinessAiBot`):
  - `BOT_TOKEN` или `TELEGRAM_TOKEN` — токен Telegram-бота.
  - `DSN` — строка подключения к PostgreSQL (используется `config.py`). Пример: `host=db user=postgres password=pass dbname=aibotdb port=5432 sslmode=disable`.
  - `ADMIN_IDS` — список id администраторов через запятую (опционально).
  - `DATABASE_URL` / `PGHOST` / `PGUSER` / `PGPASSWORD` / `PGDATABASE` — альтернативы для подключения к БД.
  - `POSTGRES_PASSWORD` — если используется локальная БД в контейнере (опционально).

Пример `.env` в корне (не храните реальные токены в публичных репозиториях):

```
GIGACHAT_ACCESS_TOKEN=ваш_токен_здесь
BOT_TOKEN=123456:ABC-DEF
DSN=host=localhost user=postgres password=pass dbname=aibotdb port=5432 sslmode=disable
ADMIN_IDS=123456789,987654321
```

## Установка и запуск (локально)

Рассмотрим шаги для Linux / fish shell. При необходимости используйте соответствующие команды для bash/zsh.

1) Создайте и активируйте виртуальное окружение (в корнях каждого сервиса или в корне проекта):

```fish
python3 -m venv .venv
source .venv/bin/activate.fish
```

2) Установите зависимости для API и бота:

```fish
# из папки ai-agent-api
pip install -r ai-agent-api/requirements.txt
# из папки BusinessAiBot
pip install -r BusinessAiBot/requirements.txt
```

3) Настройте `.env` с необходимыми переменными (см. раздел выше).

4) Запуск API (development):

```fish
# опционально — включить debug payload для агента
set -x DEBUG_AGENT_PAYLOAD 1
# запуск uvicorn
python -m uvicorn ai-agent-api.src.api:app --host 0.0.0.0 --port 8000
```

Или (содержательно эквивалентно) запустить напрямую:

```fish
python ai-agent-api/src/api.py
```

5) Запуск Telegram-бота:

```fish
# из папки BusinessAiBot (или с указанием PYTHONPATH)
python BusinessAiBot/app.py
```

Если вы запускаете оба сервиса локально, убедитесь, что окружение правильно настроено и что бота/агент не конфликтуют по портам.

## Примеры использования API

Эндпоинт: `GET /digitalMaturity` (в текущем репозитории используется GET с JSON в теле; рекомендуется переключить на POST в будущем).

Пример curl (fish):

```fish
curl -v -X GET http://127.0.0.1:8000/digitalMaturity \
  -H 'Content-Type: application/json' \
  -d '{"formalization_level":"mostly_no","automation_systems":"no","kpi_metrics":"mostly_yes","data_driven_decisions":"no","it_systems_used":"mostly_no","systems_integration":"no","cloud_services_usage":"yes","info_security_measures":"yes","digital_literacy":"mostly_yes","training_programs":"unknown","it_specialists_in_house":"mostly_yes","employees_automation_perception":"yes","it_strategy":"no","state_electronic_services":"yes","future_implementation_plans":"unknown"}'
```

Ответ (пример):

```json
{"result": "Цифровая зрелость вашей компании составляет 62.5% (средний)."}
```

## Docker / Docker Compose

В проекте есть `BusinessAiBot/Dockerfile` и `BusinessAiBot/docker-compose.yml`.

Сборка и запуск (в корне проекта):

```fish
cd BusinessAiBot
docker compose build
docker compose up -d
```

Или собрать образ вручную и запустить:

```fish
docker build -t businessai-bot BusinessAiBot
docker run -d --name businessai-bot --env-file .env businessai-bot
```

Для API можно создать Dockerfile отдельно и задать переменные окружения в `docker run` или `docker compose`.

## Тесты и отладка

- В `ai-agent-api/src/` есть `Test-run.py` — быстрая проверка вызова агента.
- В `BusinessAiBot/` есть `TEST.py` для локальных проверок.
- Рекомендуется добавить формальные unit-тесты (pytest) для:
  - расчёта цифровой зрелости (`calculate_digital_maturity_score` в `ai-agent-api/src/models.py`);
  - утилит `misc/` в боте.

Отладка частых ошибок:
- Если API выдаёт 422 от внешнего LLM — включите `DEBUG_AGENT_PAYLOAD=1` и проверьте формат сообщений.
- Если бот не запускается — проверьте `BOT_TOKEN`/`TELEGRAM_TOKEN` и логи: `docker compose logs -f` или вывод `python BusinessAiBot/app.py`.

## Рекомендации по улучшению

- Перевести API на POST для передачи тела запроса.
- Добавить `.env.example` в корне с описанием переменных окружения.
- Добавить CI (GitHub Actions) с линтингом и тестами.
- Хранить секреты в менеджере секретов (Vault, AWS Secrets Manager) для production.

## Безопасность

- Никогда не коммитите реальные токены и пароли. Добавьте `.env` в `.gitignore`.
- Ограничьте доступ к LLM-токену и логируйте без вывода секретов.

## Контакты и вклад

Если нужно помочь с развёртыванием или доработками — создайте issue с описанием проблемы или желаемого поведения. Для патчей присылайте pull request.

---

Файл README.md создан автоматически на основе структуры репозитория и имеющихся описаний в `ai-agent-api/README.md` и `BusinessAiBot/README.md`.
