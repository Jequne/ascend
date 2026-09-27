# Аутентификация

## API-ключи

Пользовательский ключ имеет формат `asc_<kid>_<secret>`. Полное значение
возвращается только при создании; в таблице `api_keys` сохраняется SHA-256 hash
полного ключа с серверным `API_KEY_PEPPER`.

Создание ключа защищено заголовком `X-Admin-Secret`:

```http
POST /api/v1/api-keys/create-api-key
X-Admin-Secret: <ADMIN_SECRET>
Content-Type: application/json

{
  "expires_in_days": 7,
  "max_active_sessions": 3,
  "label": "local-dev"
}
```

Проверка ключа выполняется endpoint `POST /api/v1/api-keys/validate-api-key` с
заголовком `X-API-Key`. Клиент использует эту проверку перед подключением к
потоку.

## WebSocket

Endpoint `/ws` принимает ключ из query-параметра `api_key`, `X-API-Key` или
`Authorization: Bearer …` именно в таком порядке приоритета. Пробелы удаляются
после выбора источника; непустой источник из одних пробелов не переключается
на следующий. Query-параметр может попасть в proxy logs.

При подключении сервер:

1. принимает WebSocket;
2. проверяет ключ через внедрённый access adapter единственного сервиса api_keys;
3. проверяет лимит активных сессий для `kid` и регистрирует соединение;
4. каждые 30 секунд повторяет проверку тем же сервисом.

Rate limiter на этом пути не активен. Max active sessions допускает значения
1–4; expiry наступает при now >= expires_at. Внутренние kid и session limit
не включаются в HTTP validation response. Каждая проверка обновляет запись
согласно текущим правилам api_keys. Отказы передают error envelope и close 1008.

Согласованные отличия от прежней WS-валидации и сохранённые дефекты
revoked_at, session race и DB outage watchdog описаны в
[отчёте совместимости](backend-refactoring.md).

## Desktop-extension pairing

Tauri поднимает bridge только на фиксированном loopback-адресе. Pairing secret
создается из системного источника случайности, хранится в app data и может быть
ротирован. Bridge проверяет origin расширения, pairing secret, версию протокола и
версию расширения до приема команд.

## Требования безопасности

- В production обязательно задаются уникальные `ADMIN_SECRET`,
  `API_KEY_PEPPER`, пароли PostgreSQL/Grafana и `RESTIC_PASSWORD`.
- Значения из `.env.example` не подходят для публичного окружения.
- `.env`, fingerprints, API-ключи и pairing codes не коммитятся и не попадают в
  логи, тестовые fixtures или документацию.
- При изменении формата ключа, способа hashing, заголовков или handshake нужно
  одновременно обновить сервер, клиент, тесты и этот документ.
