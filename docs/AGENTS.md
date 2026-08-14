# Сервисы

| Сервис | Путь | Стек | Порт (dev) | Зона ответственности |
|---|---|---|---|---|
| API | `api/` | FastAPI + SQLModel + SQLite | 8000 | БД, бизнес-логика, claim/lock, auth оператора, WebSocket |
| Bot | `bot/` | aiogram | polling + внутр. сервер :8001 | Единственная точка связи с Telegram (входящие и исходящие сообщения) |
| Web (miniapp) | `web/` | React + TypeScript + Vite | 5173 (dev) | UI оператора внутри Telegram Mini App |

Интеграционная ветка — `dev`. Тикеты — `feature/N-slug` → `dev`, коммиты со ссылкой на issue (`Refs #N` / `Closes #N`).
Переменные окружения — шаблоны в `<service>/.env.example`, реальные `.env` в git не попадают (см. `.gitignore`).
