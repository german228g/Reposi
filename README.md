# Telegram → Gmail

Бот принимает текст в Telegram и отправляет его на фиксированную почту
`oficcialbrandeu@gmail.com`. Пользователь адрес не меняет — только поддержка
в `bot/config.py` (`FIXED_RECIPIENT`).

## Где файлы

```
/workspace/
  bot/main.py       # Telegram-бот
  bot/mailer.py     # отправка через Gmail SMTP
  bot/config.py     # настройки + FIXED_RECIPIENT
  .env              # секреты (локально, не в git)
  .env.example
  requirements.txt
  run.sh
  tests/
```

## Важно про Gmail

Обычный пароль Google **не работает** для SMTP.
Нужен [пароль приложения](https://myaccount.google.com/apppasswords)
(включи 2FA → Пароли приложений → вставь 16 символов в `GMAIL_APP_PASSWORD`).

## Запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./run.sh
```

## Использование

1. `/start` боту
2. Любой текст → письмо на фиксированную почту
