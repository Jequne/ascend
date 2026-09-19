# База данных

## Режимы работы

Локальная конфигурация по умолчанию использует SQLite:

```dotenv
DATABASE_URL=sqlite:///./ascend.db
DATABASE_ASYNC_URL=sqlite+aiosqlite:///./ascend.db
```

Docker Compose использует PostgreSQL 16 и передает приложению синхронный и
асинхронный SQLAlchemy URL. В текущем коде обе сессии нужны: синхронная — для
инициализации совместимости, асинхронная — для repository и проверки доступа.

## Схема

Текущая таблица `api_keys` содержит:

| Поле                  | Назначение                                                        |
| --------------------- | ----------------------------------------------------------------- |
| `id`                  | Внутренний UUID                                                   |
| `kid`                 | Публичный идентификатор части ключа, уникальный и индексированный |
| `key_hash`            | SHA-256 hash полного ключа с pepper                               |
| `label`               | Необязательная подпись                                            |
| `status`              | `active`, `revoked` или `expired`                                 |
| `expires_at`          | Момент окончания действия                                         |
| `max_active_sessions` | Максимум одновременных WebSocket-сессий                           |
| `created_at`          | Момент создания                                                   |
| `revoked_at`          | Момент отзыва, если он был                                        |

## Миграции

Alembic-конфигурация находится в `src/server/alembic.ini`, версии — в
`src/server/migrations/versions`.

```powershell
cd src/server
alembic upgrade head
```

Для изменения схемы создайте новую миграцию и проверьте upgrade и downgrade на
временной базе. Уже примененную или опубликованную миграцию не редактируют.
Вызов `Base.metadata.create_all()` при старте не заменяет миграции в
production: контейнер `migrate` должен успешно выполнить `alembic upgrade head`
до запуска API.

## Backup

Compose profile `backup_for_cron` создает дамп PostgreSQL и передает его Restic в
S3-совместимое хранилище:

```powershell
cd src/server
docker compose --profile backup_for_cron run --rm backup
```

Наличие backup считается подтвержденным только после тестового восстановления.
Параметры хранилища и retention описаны в [развертывании](deployment.md).
