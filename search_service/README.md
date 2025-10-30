# Search Service

Этот проект реализует обработку поисковых задач по схеме с двумя очередями RabbitMQ, воркером AI Search и публикацией результатов в Telegram.

## Структура

- FastAPI API `/api/v1/search-tasks`
- Очереди `raw_search_tasks` и `completed_search_tasks`
- Воркер `worker.py` обрабатывает задания, сохраняет статусы и публикует результат
- Паблишер `publisher.py` отправляет итоговые сообщения в Telegram (или печатает в консоль)

## Запуск

1. Установите зависимости:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r search_service/requirements.txt
   ```
2. Запустите RabbitMQ (по умолчанию `amqp://guest:guest@localhost:5672/`).
3. Опционально задайте переменные окружения:
   - `RABBITMQ_URL`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `SEARCH_DB_PATH`

4. Инициализируйте БД и запустите API:
   ```bash
   uvicorn search_service.src.api:app --reload
   ```
5. В отдельном терминале запустите воркер:
   ```bash
   python -m search_service.src.worker
   ```
6. В ещё одном терминале запустите паблишер Telegram:
   ```bash
   python -m search_service.src.publisher
   ```

## API

OpenAPI схема лежит в `search_service/api--v1.yaml`. Основные эндпоинты:

- `POST /api/v1/search-tasks` — создать задачу.
- `GET /api/v1/search-tasks/{taskId}` — получить статус.
- `GET /api/v1/search-tasks` — список с пагинацией.
- `POST /api/v1/search-tasks/{taskId}/retry` — повторить неудавшуюся задачу.

## Тестовый сценарий

1. Отправьте POST запрос:
   ```bash
   curl -X POST http://localhost:8000/api/v1/search-tasks \
     -H "Content-Type: application/json" \
     -d '{"telegramId": "123456", "text": "новости технологий"}'
   ```
2. Проверьте статус задач:
   ```bash
   curl http://localhost:8000/api/v1/search-tasks
   ```
3. Когда воркер завершит обработку, паблишер отправит короткое и полное резюме в Telegram (или выведет сообщение в консоль).
