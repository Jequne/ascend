# Ascend

Ascend принимает поток токенов из внешнего провайдера, обогащает его и передает
авторизованному desktop-клиенту. Клиент фильтрует события, показывает компактную
ленту и при необходимости открывает токен в новой вкладке либо в выбранной
вкладке Axiom через браузерное расширение.

## Состав проекта

| Компонент       | Назначение                                         | Технологии                   |
| --------------- | -------------------------------------------------- | ---------------------------- |
| `src/server`    | Сбор и трансляция данных, API-ключи, WebSocket API | Python, FastAPI, SQLAlchemy  |
| `src/client`    | Desktop UI, локальные настройки и фильтрация       | SvelteKit, TypeScript, Tauri |
| `src/extension` | Управление выбранной вкладкой Axiom                | WXT, Svelte, Chrome MV3      |

Подробное описание компонентов, границ и потока данных находится в
[архитектурной документации](docs/architecture.md).

## Быстрый старт

### Сервер

```powershell
cd src/server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
Copy-Item axiom_users_fingerprints.example.json axiom_users_fingerprints.json
alembic upgrade head
uvicorn app.main:app --reload
```

Перед запуском замените демонстрационные значения в `.env` и файле
fingerprints. Healthcheck будет доступен по адресу
`http://localhost:8000/health`, OpenAPI — `http://localhost:8000/docs`.

### Desktop-клиент

```powershell
cd src/client
Copy-Item .env.example .env
npm ci
npm run tauri dev
```

Запуск и сборка Tauri автоматически собирают расширение и копируют его как
ресурс приложения. Для запуска только web-интерфейса используйте `npm run dev`.

Полная настройка окружения и все команды проверки описаны в
[руководстве разработчика](docs/development.md).

## Документация

- [Оглавление документации](docs/index.md)
- [Текущее состояние](docs/project-status.md)
- [Архитектура](docs/architecture.md)
- [Разработка и проверки](docs/development.md)
- [Аутентификация](docs/authentication.md)
- [База данных](docs/database.md)
- [Развертывание](docs/deployment.md)
- [Архитектурные решения](docs/adr/README.md)

Документация написана на стандартном Markdown, использует относительные ссылки
и Mermaid-диаграммы. Ее можно публиковать через GitHub, MkDocs, Docusaurus и
другие генераторы без изменения исходных текстов.
