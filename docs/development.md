# Разработка

## Требования

- Python 3.11 или новее;
- Node.js и npm;
- Rust toolchain и системные зависимости Tauri;
- Docker с Compose plugin для полного серверного окружения;
- учетные данные Axiom только для локальной ручной проверки интеграции.

## Server

Из корня репозитория:

```powershell
cd src/server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install pytest pytest-asyncio
Copy-Item .env.example .env
Copy-Item axiom_users_fingerprints.example.json axiom_users_fingerprints.json
alembic upgrade head
uvicorn app.main:app --reload
```

Минимальные проверки текущего server toolchain:

```powershell
python -m compileall app third_party_apis migrations
python -m pytest -q
```

В Python-части пока не закреплены formatter, linter и static type checker. При
добавлении этих инструментов их версии, конфигурация и команды должны быть
зафиксированы в репозитории и в этом разделе.

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
