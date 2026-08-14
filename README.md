# Support Bot + Miniapp

Telegram-поддержка: пользователь пишет боту, оператор отвечает **только** через miniapp.
Три независимых сервиса: `api/`, `bot/`, `web/`. План работы и прогресс — в Issues/Project репозитория.

## Архитектура

```
Telegram user → bot (polling) → api (БД, бизнес-логика) ← web (miniapp, оператор)
                bot ←──────────── api  (при ответе оператора: POST /internal/send)
```

- **api/** — FastAPI + SQLModel + SQLite. Вся бизнес-логика, claim/lock, auth оператора, WebSocket. Ничего не знает про Telegram Bot API напрямую.
- **bot/** — aiogram. Единственная точка связи с Telegram: принимает сообщения пользователей (long polling) и отправляет ответы операторов. Параллельно поднимает свой внутренний HTTP-сервер (`/internal/send`), который дёргает `api`, когда оператор отвечает.
- **web/** — React + TypeScript + Vite. Telegram Mini App для операторов: список чатов, переписка, claim/release/close.

**claim/lock:** атомарный `UPDATE chats SET claimed_by=... WHERE id=... AND claimed_by IS NULL` — гонка двух операторов исключена на уровне БД, а не только в интерфейсе. Отвечать и закрывать чат может только тот, кто его claim'нул (проверяется на сервере на каждый запрос).

**Auth оператора:** Telegram WebApp `initData`, подпись проверяется HMAC-SHA256 бот-токеном на бэке, плюс allowlist по `telegram_id` (`ALLOWED_OPERATOR_IDS` в `api/.env`). Публичного доступа нет.

## Быстрый старт (локально)

### 1. API
```bash
cd api
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# впишите свой BOT_TOKEN (нужен для проверки подписи initData) и ALLOWED_OPERATOR_IDS
uvicorn app.main:app --reload --port 8000
```
Проверка: http://localhost:8000/health → `{"status": "ok"}`

### 2. Bot
```bash
cd bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # тот же BOT_TOKEN, что и в api/.env
python -m app.main
```
> Получить `BOT_TOKEN`: напишите **@BotFather** в Telegram → `/newbot` → следуйте инструкциям.

### 3. Web (miniapp)
```bash
cd web
npm install
npm run dev
```
Откройте через кнопку miniapp у вашего бота в Telegram (задаётся в @BotFather: `/mybots` → бот → Bot Settings → Menu Button, укажите публичный URL сборки `web/`, например через `npm run build` + любой статический хостинг, либо туннель типа ngrok на `npm run dev` для локальной отладки).

### Тест без реального Telegram-клиента

Для проверки бэкенда/UI без живого бота:
- `api/.env`: `DEV_MODE=true`
- запросы к api с заголовком `Authorization: dev <telegram_id>` вместо `tma <initData>`
- `web/.env`: раскомментируйте `VITE_DEV_OPERATOR_ID=111111111` и откройте `web` в обычном браузере через `npm run dev`

**⚠️ `DEV_MODE=true` — только для локальной разработки.** В проде переменная должна отсутствовать или быть `false`.

## Переменные окружения

| Сервис | Переменная | Назначение |
|---|---|---|
| api | `BOT_TOKEN` | проверка подписи `initData` |
| api | `ALLOWED_OPERATOR_IDS` | allowlist telegram_id операторов, через запятую |
| api | `BOT_INTERNAL_URL`, `BOT_INTERNAL_SECRET` | адрес и секрет внутреннего сервера бота (для доставки ответов) |
| bot | `BOT_TOKEN`, `API_BASE_URL` | токен бота, адрес api |
| bot | `BOT_INTERNAL_PORT`, `BOT_INTERNAL_SECRET` | свой внутренний сервер `/internal/send` |
| web | `VITE_API_BASE_URL` | адрес api |

Полный список с примерами — в `<service>/.env.example`. Реальные `.env` в git не коммитятся.

## Статусы чата

`open` (новый, свободен) → `in_progress` (кто-то claim'нул) → `closed`. Освобождённый (`release`) чат возвращается в `open`.
