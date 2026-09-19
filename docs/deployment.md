# Развертывание

## Состав окружения

`src/server/docker-compose.yml` описывает production-like стек:

| Service   | Назначение                                            |
| --------- | ----------------------------------------------------- |
| `db`      | PostgreSQL 16                                         |
| `migrate` | Однократный `alembic upgrade head`                    |
| `app`     | FastAPI/Uvicorn на внутреннем порту 8000              |
| `caddy`   | Публичный reverse proxy и TLS                         |
| `loki`    | Хранилище логов                                       |
| `alloy`   | Сбор container logs                                   |
| `grafana` | Просмотр логов                                        |
| `backup`  | Дамп PostgreSQL и Restic upload по отдельному profile |

## Конфигурация

Создайте `src/server/.env` на основе `.env.example` и задайте как минимум:

- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`;
- `DATABASE_URL` и `DATABASE_ASYNC_URL` для запуска вне Compose;
- `ADMIN_SECRET` и `API_KEY_PEPPER`;
- `DOMAIN` и `ACME_EMAIL`;
- `GF_SECURITY_ADMIN_USER` и `GF_SECURITY_ADMIN_PASSWORD`;
- `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `POSTGRES_DB_BUCKET` и
  `RESTIC_PASSWORD` для backup.

Также создайте локальный `axiom_users_fingerprints.json` из example-файла. Эти
файлы содержат секреты и не должны попадать в Git.

## Запуск

```powershell
cd src/server
docker compose config
docker compose up --build -d
docker compose ps
```

Перед приемом трафика проверьте:

- `migrate` завершился с кодом 0;
- `db` healthy, а `app` и `caddy` запущены;
- `/health` доступен через публичный HTTPS endpoint;
- создание тестового ключа и WebSocket-подключение работают;
- в Grafana появляются логи приложения без секретов.

## Backup и восстановление

```powershell
docker compose --profile backup_for_cron run --rm backup
```

Скрипт использует Restic и S3-совместимое хранилище. Текущая retention policy:
7 дневных, 4 недельных и 6 месячных snapshot. Планировщик запуска backup не
входит в Compose и настраивается на хосте отдельно.

После изменения схемы или backup-скрипта выполните восстановление в отдельную
базу. Не проверяйте restore поверх production-базы.

## Обновление

Номер серверного выпуска хранится в `src/server/VERSION`; правила его изменения
и формат тегов описаны в [документе версионирования](versioning.md).

1. Сохраните проверенный backup и зафиксируйте текущие неизменяемые версии image.
2. Соберите новые image и проверьте Compose-конфигурацию.
3. Запустите стек; migration service должен завершиться до API.
4. Проверьте healthcheck, доступ и основной WebSocket-поток.
5. При несовместимой миграции используйте заранее описанный rollback-план, а не
   ручное изменение production-схемы.
