import asyncio
import logging
import re
from datetime import datetime
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from email_sender import send_receipt_email
from receipt_generator import generate_order_number, generate_receipt_image, random_amount

TELEGRAM_BOT_TOKEN = "8305270882:AAHYqbnMOss_UaRlQ12u56fDLNIe6qDWpwI"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
OUTPUT_DIR = Path(__file__).parent / "output"


class ReceiptForm(StatesGroup):
    photo = State()
    product_name = State()
    buyer_name = State()
    email = State()


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data="cancel")]]
    )


async def start_flow(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ReceiptForm.photo)
    await message.answer(
        "Создание чека OFFICIALBRAND\n\n"
        "Шаг 1/4. Пришлите фото продукта (как изображение).",
        reply_markup=cancel_keyboard(),
    )


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await start_flow(message, state)


@dp.message(Command("cancel"))
@dp.callback_query(F.data == "cancel")
async def on_cancel(event: Message | CallbackQuery, state: FSMContext) -> None:
    if isinstance(event, CallbackQuery):
        await event.answer()
        target = event.message
    else:
        target = event
    await start_flow(target, state)


@dp.message(ReceiptForm.photo, F.photo)
async def process_photo(message: Message, state: FSMContext) -> None:
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    raw = await bot.download_file(file.file_path)
    photo_bytes = raw.read()
    await state.update_data(photo_bytes=photo_bytes)
    await state.set_state(ReceiptForm.product_name)
    await message.answer(
        "Шаг 2/4. Введите название продукта:",
        reply_markup=cancel_keyboard(),
    )


@dp.message(ReceiptForm.photo)
async def process_photo_invalid(message: Message) -> None:
    await message.answer("Нужно отправить именно фото. Попробуйте ещё раз.")


@dp.message(ReceiptForm.product_name)
async def process_product_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Название не может быть пустым. Введите название продукта:")
        return
    await state.update_data(product_name=name)
    await state.set_state(ReceiptForm.buyer_name)
    await message.answer(
        "Шаг 3/4. Введите имя покупателя:",
        reply_markup=cancel_keyboard(),
    )


@dp.message(ReceiptForm.buyer_name)
async def process_buyer_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Имя не может быть пустым. Введите имя покупателя:")
        return
    await state.update_data(buyer_name=name)
    await state.set_state(ReceiptForm.email)
    await message.answer(
        "Шаг 4/4. Введите email для отправки чека:",
        reply_markup=cancel_keyboard(),
    )


@dp.message(ReceiptForm.email)
async def process_email(message: Message, state: FSMContext) -> None:
    email = (message.text or "").strip()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        await message.answer("Некорректный email. Введите адрес ещё раз:")
        return

    data = await state.get_data()
    order_number = generate_order_number()
    amount = random_amount()
    created_at = datetime.now().strftime("%d.%m.%Y %H:%M")

    receipt_data = {
        "photo_bytes": data["photo_bytes"],
        "product_name": data["product_name"],
        "buyer_name": data["buyer_name"],
        "order_number": order_number,
        "amount": amount,
        "created_at": created_at,
    }

    await message.answer("Генерирую чек и отправляю...")

    try:
        OUTPUT_DIR.mkdir(exist_ok=True)
        image_path = OUTPUT_DIR / f"receipt_{message.from_user.id}.png"
        generate_receipt_image(receipt_data, image_path)

        photo = BufferedInputFile(image_path.read_bytes(), filename="receipt.png")
        await message.answer_photo(
            photo=photo,
            caption=(
                f"Чек готов\n"
                f"Заказ: {order_number}\n"
                f"Товар: {data['product_name']}\n"
                f"Сумма: {amount}"
            ),
        )

        send_receipt_email(
            recipient=email,
            image_path=image_path,
            order_number=order_number,
            buyer_name=data["buyer_name"],
            product_name=data["product_name"],
            amount=amount,
        )
        await message.answer(f"Чек отправлен на email: {email}")
    except Exception:
        logger.exception("Ошибка генерации/отправки чека")
        await message.answer("Не удалось создать или отправить чек. Попробуйте ещё раз: /start")
    finally:
        await state.clear()


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
