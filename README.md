# Telegram → Gmail (клиенту)

С `oficcialbrandeu@gmail.com` бот отправляет текст **на почту клиента**.

## Как работает

1. Клиент пишет `/start`
2. Бот один раз спрашивает его email и сохраняет
3. Дальше любой текст уходит письмом **на почту клиента**
4. Клиент сам почту не меняет — только поддержка: `/setemail <user_id> <email>`

## Где файлы

```
/workspace/bot/main.py      # бот
/workspace/bot/mailer.py    # SMTP отправка
/workspace/bot/config.py    # отправитель oficcialbrandeu@gmail.com
/workspace/bot/storage.py   # сохранённые почты клиентов
/workspace/data/users.json  # база (создаётся при запуске)
/workspace/.env             # секреты
```

## Запуск

```bash
source .venv/bin/activate
./run.sh
```
