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

Endpoint `/ws` принимает ключ из `Authorization`, `X-API-Key` или query-параметра
`api_key`. Предпочтителен заголовок; query-параметр может попасть в proxy logs и
историю диагностических инструментов.

При подключении сервер:

1. применяет rate limit по адресу клиента;
2. разбирает формат и сверяет hash ключа;
3. проверяет срок действия и отзыв;
4. проверяет лимит активных сессий для `kid`;
5. повторяет проверку во время сессии и закрывает ее при потере доступа.

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
