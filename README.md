# Zelyon Receipts — Telegram Bot

Telegram-бот для генерации Apple Receipt по данным пользователя.

## Требования

- Python 3.10+
- `wkhtmltoimage` (для imgkit)

### Установка wkhtmltoimage (Ubuntu/Debian)

```bash
sudo apt-get update && sudo apt-get install -y wkhtmltopdf
```

## Установка

```bash
pip install -r requirements.txt
```

## Запуск

```bash
python3 main.py
```

## Использование

1. Отправьте `/start` боту в Telegram.
2. Заполните 3 части формы (Name, Surname, Product Name → Order Date, Product Image URL, Product Price → Street, City, ZIP, Phone, State).
3. Проверьте превью и нажмите **Send Receipt**.
4. Введите email — чек будет отправлен через Gmail SMTP.

Кнопка **Start Over** / **Отмена** — начать заново.
