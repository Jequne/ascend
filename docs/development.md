# Разработка

## Требования

- [uv](https://docs.astral.sh/uv/getting-started/installation/) 0.12.3 или новее;
- Python 3.14 для backend (uv установит его при отсутствии);
- Node.js и npm;
- Rust toolchain и системные зависимости Tauri;
- Docker с Compose plugin для полного серверного окружения;
- учетные данные Axiom только для локальной ручной проверки интеграции.

## Server

Из корня репозитория:

```powershell
cd src/server
uv sync --locked
Copy-Item .env.example .env
Copy-Item axiom_users_fingerprints.example.json axiom_users_fingerprints.json
uv run --locked alembic upgrade head
uv run --locked uvicorn app.main:app --reload
```

Зависимости приложения перечислены в `pyproject.toml`, инструменты проверок —
в его группе `dev`. `uv.lock` фиксирует полный граф зависимостей и хранится
в Git вместе с `pyproject.toml`. `.python-version` выбирает Python 3.14,
как и Docker. `uv sync --locked` создаёт или синхронизирует `.venv` и включает
группу `dev`; активировать окружение вручную не требуется.
Backend запускается из исходников (`tool.uv.package = false`).

Добавление и обновление зависимостей выполняйте из `src/server`:

```powershell
uv add package-name
uv add --dev tool-name
uv remove package-name
uv add "package-name==1.2.3"
uv sync --locked
```

Изменения `pyproject.toml` и `uv.lock` коммитятся вместе. `--locked` проверяет,
что lock-файл соответствует декларациям, и не обновляет его при запуске.
В `pyproject.toml` перечислены только используемые прямые зависимости.
Транзитивные зависимости фиксируются в `uv.lock`. Версии оставшихся прямых
зависимостей сохранены; для обновления задайте новую версию через `uv add`.
Наборы `uvicorn[standard]`, `SQLAlchemy[asyncio]` и `psycopg[binary]` сохраняют
HTTP/WebSocket backend, reload, асинхронную БД и PostgreSQL driver.
Для окружения без инструментов разработки используйте `uv sync --locked --no-dev`
и запускайте команды с `uv run --locked --no-dev ...`.

Проверки server toolchain:

```powershell
uv lock --check
uv run --locked ruff format --check app third_party_apis scripts migrations
uv run --locked ruff check app third_party_apis scripts migrations
uv run --locked mypy app third_party_apis scripts migrations
uv run --locked python -m compileall app third_party_apis scripts migrations
uv run --locked pytest -q
```

Ruff ограничивает строки Python-кода 79 символами по PEP 8 (`line-length = 79`)
и проверяет превышения правилом E501, включая строки, которые formatter не
переносит автоматически. Ruff также проверяет imports, базовые ошибки и async;
mypy с Pydantic plugin проверяет
собственные функции и тела всех backend/SDK модулей, включая тесты. Pytest
использует strict asyncio и importlib import mode.
Для запуска через console entrypoint `uv run pytest` путь исходников server
явно задан в настройке pytest `pythonpath = ["."]`.
Применённые миграции исключены из форматирования и сортировки imports:
их содержимое неизменяемо.
Для существующей миграции `801c5e2b52e7_added_revoked_at_api_keys.py` также
сохранено исключение E501; новые миграции проходят проверку длины строк.
Остальные lint и type проверки действуют для всех миграций.
Fixtures используют временные БД и подменяют внешние адаптеры, credentials не
нужны. Для параллельных runtime используйте отдельные соединения файловой
временной SQLite: in-memory StaticPool разделяет одно соединение между сессиями.

При доступном Docker из `src/server`: `docker build -t ascend-server-check .`.
Compileall проверяет синтаксис и не заменяет сборку Docker image. Результаты
baseline и итоговых проверок: [отчёт рефакторинга](backend-refactoring.md).

На уровне INFO token feed выводит многострочные карточки с 🔍 адресом/именем,
🛠️ кошельком разработчика, долей миграций и 🪙 предыдущими монетами с fees.
Базовая карточка появляется сразу; developer/funding enrichment выводит
обновлённые данные отдельно, funding wallet отмечен 💰. При пустой истории
доля миграций помечается как неизвестная, без деления на ноль.
`Axiom HTTP diagnostics` (attempts/429/pending/oldest_wait) имеет уровень DEBUG;
для него установите `LOG_LEVEL=debug`. Предупреждения и ошибки upstream сохраняют
свои уровни.

### Ручная проверка сырого Axiom WebSocket

Из `src/server`, после настройки зависимостей и локального
`axiom_users_fingerprints.json`, запустите:

```powershell
uv run --locked python -m scripts.manual_wss_probe --rooms new_pairs sol_price
```

Доступные комнаты: `new_pairs`, `sol_price`, `migrations`. Если `--rooms` не указан,
используется `new_pairs`. Скрипт подключается с первым настроенным агентом,
подписывается на комнаты и печатает каждый полученный payload без изменения,
до JSON-разбора и проверки моделей. Остановите его сочетанием Ctrl+C. Проверка
требует действующих учетных данных Axiom и доступа к сети; обычный `pytest` ее
не запускает.

## Desktop client

```powershell
cd src/client
Copy-Item .env.example .env
npm ci
npm run dev
```

Для запуска Tauri используйте `npm run tauri dev`. Эта команда также собирает
расширение как ресурс desktop-приложения.

Полный набор проверок:

```powershell
npm run format:check
npm run lint
npm run check
npm run test
npm run version:check
npm run build
```

Для измененной Rust-части из `src/client/src-tauri`:

```powershell
cargo fmt --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test
cargo check
```

## Browser extension

```powershell
cd src/extension
npm ci
npm run dev
```

Полный набор проверок:

```powershell
npm run format:check
npm run lint
npm run check
npm run test
npm run version:check
npm run build
npm run test:e2e
```

Правила повышения версий, component-specific Git-теги и порядок выпуска
описаны в [документе версионирования](versioning.md).

E2E-сценарии используют production bundle расширения и изолированный Chromium
profile. Ручные проверки в установленном браузере описаны в
`src/extension/QA.md`; не копируйте из браузера cookies, local storage, API-ключи,
pairing codes или данные кошелька.

## Перед завершением изменения

1. Запустите formatter, linter, type checker, релевантные тесты и build для всех
   затронутых компонентов.
2. Добавьте тест для измененного поведения либо объясните, почему он неприменим.
3. Обновите связанный документ из [оглавления](index.md).
4. Для значимого архитектурного решения добавьте ADR.
5. Не отмечайте непроведенную проверку как успешную; явно перечислите пропуски и
   причину.
