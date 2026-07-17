# MarioProg Lead & CRM System

Преміальний B2B-проєкт для захоплення лідів, збереження їх у SQLite, обробки статусів та Telegram-сповіщень.

## Особливості

- Premium landing для збору заявок
- FastAPI бекенд з SQLite
- Адмін-панель для керування лідами
- Захоплення лідів із валідацією телефона
- Telegram сповіщення через Webhook та inline-кнопки
- Webhook-обробка статусу “Оброблено”
- Захищений доступ до CRM через admin login

## Технології

- FastAPI
- SQLAlchemy
- Pydantic
- Uvicorn
- Tailwind CSS
- SQLite

## Структура проєкту

```text
marioprog-lead-crm/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── config.py
├── frontend/
│   ├── index.html
│   └── dashboard.html
├── .env
├── requirements.txt
└── vercel.json
```

## Локальний запуск

1. Встановіть залежності:

```bash
pip install -r requirements.txt
```

2. Запустіть бекенд:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

3. Відкрийте фронтенд:

- Landing: `frontend/index.html`
- Dashboard: `frontend/dashboard.html`

## Конфігурація

Створіть файл `.env` з наступними змінними:

```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
ADMIN_USERNAME=admin
ADMIN_PASSWORD=marioprog2026
ADMIN_TOKEN=marioprog-admin-token
```

## Деплой на Vercel

1. Підключіть репозиторій до Vercel.
2. Виберіть папку проєкту як кореневу.
3. Додайте змінні середовища з `.env`.
4. Натисніть Deploy.

## Адмін-доступ

- Логін: `admin`
- Пароль: `marioprog2026`

## Автор

MarioProg
