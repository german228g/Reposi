# Сайт регистрации

Простой сайт регистрации пользователей: фронтенд (HTML/CSS/JS) + бэкенд на Node.js/Express. Пароли хешируются через `bcryptjs`, пользователи сохраняются в `data/users.json`.

## Запуск

```bash
npm install
npm start
```

Откройте http://localhost:3000

## API

- `POST /api/register` — регистрация (`{ name, email, password, confirm }`)
- `GET /api/users` — список зарегистрированных (без хешей паролей)
- `GET /api/health` — проверка, что сервер жив
