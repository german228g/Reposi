# Telegram → DEMO Receipt (OFFICIALBRAND)

Бот собирает данные по шагам и отправляет **учебный DEMO-чек** на почту клиента.

⚠️ В письме и превью всегда есть пометка **DEMO / NOT A REAL RECEIPT**.

## Поля (11 шагов)

1. Name
2. Surname
3. Product Name
4. Order Date (YYYY-MM-DD)
5. Product Image URL
6. Product Price
7. Street
8. City
9. ZIP Code
10. Phone Number
11. State

После заполнения — превью в Telegram → кнопки **Send Receipt** / **Start Over**.

## Где файлы

```
/workspace/bot/main.py              # бот, шаги, кнопки
/workspace/bot/form_steps.py        # вопросы и валидация
/workspace/bot/receipt_template.py  # HTML-шаблон DEMO-чека
/workspace/bot/mailer.py            # отправка Gmail
/workspace/bot/storage.py           # email клиента
/workspace/.env                     # секреты
```

## Запуск

```bash
source .venv/bin/activate
./run.sh
```

## Команды

- `/start` — новый чек
- `/cancel` — отменить заполнение
- `/setemail <user_id> <email>` — смена почты клиента (поддержка)
