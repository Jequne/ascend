# Модульный backend: совместимость и проверки

## Исходное состояние

Baseline от 2026-09-27: `src/server/.venv/Scripts/python.exe -m pytest -q
-p no:cacheprovider` — 51 passed, 1 failed. Падает
`test_shared_http_concurrency_limit_under_burst`: тест ожидает 15 одновременных
запросов, текущий `AxiomRequestPacer` имеет default 50 и допускает весь burst из
20 запросов. Алгоритм и production limit сохраняются; ожидание теста необходимо
связать с явно заданным лимитом. Системный Python не содержит pytest.

## Контракты, которые сохраняются

- `POST /api/v1/api-keys/create-api-key`: admin header, 201, ключ, kid,
  expires_at, max_active_sessions и label; 401/409/422 при ошибках.
- `POST /api/v1/api-keys/validate-api-key`: X-Api-Key, 200 с status/expires_at;
  401 при ошибке ключа. Внутренние kid/session limit не добавляются в ответ.
- `/ws`: accept перед проверкой, приоритет query api_key → X-Api-Key → Bearer.
  Непереданный ключ: `the api key was not transferred`, неверный:
  `api key is not valid`, превышение: `too_many_sessions`; close 1008.
- Envelope: `type` и `payload`; token_feed, sol_price, ping, error. Нет replay.
  Heartbeat и watchdog: 30 секунд. Send error логируется, соединение не удаляется.
- Feed: base до HTTP, независимые developer/funding updates одной пары.
  Developer выбирает первые три записи, пропуская текущую только в начале.
  Funding выбирает до трёх distinct предыдущих токенов по времени и требует
  проверенные fees. Funding для BSC отсутствует.
- Изображения: фиксированный Axiom CDN, лимит 2 MiB, без redirects;
  422/404/502, bytes/media type и Cache-Control public, max-age=3600.

## Известные дефекты и согласованные изменения

- Repository ключей не переносит revoked_at в domain. Это сохраняется:
  revoked status может превратиться в expired при истечении даты.
- Проверка session limit и регистрация выполняются раздельно: гонка остаётся.
- Watchdog при недоступной БД обращается к status отсутствующего результата:
  исходный дефект фиксируется отдельно, исправление не входит в рефакторинг.
- WS переходит на правила api_keys: expiry при now >= expires_at, обновление
  записи при проверке, сохранение фактической status/revoked_at семантики.
  Старый валидатор использовал now > expires_at и раньше проверял revoked.
- Rate limiter не вызывался на пути подключения и не активируется.
- Create DTO допускает session limit 5, domain — только 1–4; запрос с 5
  сохраняет прежнюю ошибку ValueError/500. Это отдельный дефект, без исправления
  в данном рефакторинге. Пропущенный label даёт null в response; явно переданный
  null в request по-прежнему отклоняется с 422/string_type.
- SDK сохраняет прежнее присваивание CF-cookie в extra field с буквальным
  именем key. Поведение не исправляется при типизации.

## Выполнение

Реализация выполнена по [ТЗ 003](tasks/003-backend-modular-refactoring.md),
последовательными слайсами в `refactor/backend-modules`. Слияние в main и
публикация ветки не выполнялись.

| Слайс | Реализованный рабочий путь |
| --- | --- |
| 0 | Baseline, фиксация контрактов/дефектов, закреплённые Ruff/mypy/pytest settings |
| 1 | HTTP ключ → manager/domain → repository contract → SQLAlchemy adapter → response |
| 2 | WS/access/watchdog → единый api_keys; cleanup с инфраструктурной транзакцией |
| 3 | Независимый SDK → feed adapter → собственное событие → base → queue → WS |
| 4 | Developer history → отдельное правило выбора → mapping → update той же пары |
| 5 | Immediate funder → cache/history/fees → selection → funding update; BSC skip |
| 6 | Собственный SolPrice → callback → streaming; feed/heartbeat delivery |
| 7 | Address → provider contract → ограниченный HTTP adapter → bytes/status/headers |
| 8 | Runtime/lifespan, отмена задач, снятие callbacks, partial startup, импорт и схема |

Перенесены существующие тесты историй, collector, SDK и изображений; добавлены
проверки границ, staged delivery в обоих порядках, сбоев, кэша, lifecycle и
HTTP → WS. Прежний падающий concurrency test теперь явно задаёт лимит 15;
production default 50 не менялся. Нет общего event bus или service locator.

По запросу пользователя восстановлены INFO-карточки токенов со смайликами,
адресом, именем/тикером, dev holds, developer migrations и fees прошлых монет.
Карточки выводятся для base и обновлений историй, funding отмечен отдельно.
Регулярные Axiom HTTP diagnostics переведены на DEBUG. Regression tests
проверяют формат, логирование collector и видимость diagnostics по уровням.

## Итоговые проверки

Команды выполняются из `src/server` существующим `.venv/Scripts/python.exe`.
Применённые миграции исключены только из format и import sorting, поскольку
их содержимое не меняется. Lint остальных правил и mypy охватывают миграции.
Сторонние stubs и собственные модули не исключались из type checking.

Итоговый запуск 2026-09-27:

| Команда | Результат |
| --- | --- |
| `python -m ruff format --check app third_party_apis scripts migrations` | 104 files already formatted |
| `python -m ruff check app third_party_apis scripts migrations` | All checks passed |
| `python -m mypy app third_party_apis scripts migrations` | no issues in 105 source files |
| `python -m compileall -q app third_party_apis scripts migrations` | exit 0 |
| `python -m pytest -q` | 91 passed |
| `git diff --check` | exit 0 |

Pytest включает проверку Alembic/schema, независимого импорта SDK, границ/циклов,
routes/lifespan и HTTP → WS. Остаются предупреждения исходного Pydantic class
Config, Starlette/httpx testclient и curl_cffi Proactor loop на Windows; проверки
не отключают их. Клиент и расширение не затронуты, их проверки неприменимы.

Docker CLI присутствует,
но `docker info --format '{{.ServerVersion}}'` не подключается: отсутствует pipe
docker_engine/daemon. Сборка image недоступна. Live Axiom probe не запускался:
он требует действующих credentials; автоматические проверки используют fakes.
