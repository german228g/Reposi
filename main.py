import asyncio
import logging
import re
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from email_sender import send_receipt_email
from receipt_generator import generate_order_number, generate_receipt_image

TELEGRAM_BOT_TOKEN = "8305270882:AAHYqbnMOss_UaRlQ12u56fDLNIe6qDWpwI"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

OUTPUT_DIR = Path(__file__).parent / "output"


class ReceiptForm(StatesGroup):
    name = State()
    surname = State()
    product_name = State()
    order_date = State()
    product_image_url = State()
    product_price = State()
    street = State()
    city = State()
    zip_code = State()
    phone_number = State()
    state_field = State()
    preview = State()
    email = State()


PART1_HEADER = (
    "📝 <b>Edit Apple Receipt (Part 1)</b>\n\n"
    "⚠️ Эта форма будет получена приложением Zelyon Receipts. "
    "Не указывайте свои пароли и прочую конфиденциальную информацию."
)

PART2_HEADER = (
    "📝 <b>Edit Apple Receipt (Part 2)</b>\n\n"
    "⚠️ Эта форма будет получена приложением Zelyon Receipts. "
    "Не указывайте свои пароли и прочую конфиденциальную информацию."
)

PART3_HEADER = (
    "📝 <b>Edit Apple Receipt (Part 3)</b>\n\n"
    "⚠️ Эта форма будет получена приложением Zelyon Receipts. "
    "Не указывайте свои пароли и прочую конфиденциальную информацию."
)


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
        ]
    )


def preview_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✉️ Send Receipt", callback_data="send_receipt"),
                InlineKeyboardButton(text="🔄 Start Over", callback_data="start_over"),
            ]
        ]
    )


def format_preview(data: dict) -> str:
    full_name = f"{data['name']} {data['surname']}"
    location = f"{data['city']}, {data['state_field']} {data['zip_code']}"
    return (
        "🍎 <b>Apple Receipt Preview</b>\n\n"
        "👤 <b>Customer Details</b>\n"
        f"Name: {full_name}\n"
        f"Address: {data['street']}\n"
        f"Location: {location}\n"
        f"Phone: {data['phone_number']}\n\n"
        "📦 <b>Order Information</b>\n"
        f"Product: {data['product_name']}\n"
        f"Order Number: {data['order_number']}\n"
        f"Price: {data['product_price']}\n"
        f"Order Date: {data['order_date']}\n\n"
        "Click 'Send Receipt' to receive it in your email or 'Start Over' to make changes."
    )


async def start_part1(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.update_data(order_number=generate_order_number())
    await state.set_state(ReceiptForm.name)
    await message.answer(
        f"{PART1_HEADER}\n\n<b>Name *</b>\nEnter your name",
        reply_markup=cancel_keyboard(),
    )


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await start_part1(message, state)


@dp.callback_query(F.data == "cancel")
async def on_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await start_part1(callback.message, state)


@dp.callback_query(F.data == "start_over")
async def on_start_over(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await start_part1(callback.message, state)


@dp.message(ReceiptForm.name)
async def process_name(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.strip():
        await message.answer("Name * — обязательное поле.\nEnter your name")
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(ReceiptForm.surname)
    await message.answer(
        f"{PART1_HEADER}\n\n<b>Surname *</b>\nEnter your surname",
        reply_markup=cancel_keyboard(),
    )


@dp.message(ReceiptForm.surname)
async def process_surname(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.strip():
        await message.answer("Surname * — обязательное поле.\nEnter your surname")
        return
    await state.update_data(surname=message.text.strip())
    await state.set_state(ReceiptForm.product_name)
    await message.answer(
        f"{PART1_HEADER}\n\n<b>Product Name *</b>\nEnter product name",
        reply_markup=cancel_keyboard(),
    )


@dp.message(ReceiptForm.product_name)
async def process_product_name(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.strip():
        await message.answer("Product Name * — обязательное поле.\nEnter product name")
        return
    await state.update_data(product_name=message.text.strip())
    await state.set_state(ReceiptForm.order_date)
    await message.answer(
        f"{PART2_HEADER}\n\n<b>Order Date (YYYY-MM-DD) *</b>\nEnter order date",
        reply_markup=cancel_keyboard(),
    )


@dp.message(ReceiptForm.order_date)
async def process_order_date(message: Message, state: FSMContext) -> None:
    if not message.text or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", message.text.strip()):
        await message.answer(
            "Order Date (YYYY-MM-DD) * — обязательное поле.\n"
            "Enter order date in format YYYY-MM-DD"
        )
        return
    await state.update_data(order_date=message.text.strip())
    await state.set_state(ReceiptForm.product_image_url)
    await message.answer(
        f"{PART2_HEADER}\n\n<b>Product Image URL *</b>\nEnter the URL of the product image",
        reply_markup=cancel_keyboard(),
    )


@dp.message(ReceiptForm.product_image_url)
async def process_product_image_url(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.strip().startswith(("http://", "https://")):
        await message.answer(
            "Product Image URL * — обязательное поле.\nEnter the URL of the product image"
        )
        return
    await state.update_data(product_image_url=message.text.strip())
    await state.set_state(ReceiptForm.product_price)
    await message.answer(
        f"{PART2_HEADER}\n\n<b>Product Price (Price, Currency) *</b>\nEnter product price",
        reply_markup=cancel_keyboard(),
    )


@dp.message(ReceiptForm.product_price)
async def process_product_price(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.strip():
        await message.answer(
            "Product Price (Price, Currency) * — обязательное поле.\nEnter product price"
        )
        return
    await state.update_data(product_price=message.text.strip())
    await state.set_state(ReceiptForm.street)
    await message.answer(
        f"{PART3_HEADER}\n\n<b>Street</b> — Это обязательное поле.\nEnter street address",
        reply_markup=cancel_keyboard(),
    )


@dp.message(ReceiptForm.street)
async def process_street(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.strip():
        await message.answer("Street — Это обязательное поле.\nEnter street address")
        return
    await state.update_data(street=message.text.strip())
    await state.set_state(ReceiptForm.city)
    await message.answer(
        f"{PART3_HEADER}\n\n<b>City *</b>\nEnter city",
        reply_markup=cancel_keyboard(),
    )


@dp.message(ReceiptForm.city)
async def process_city(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.strip():
        await message.answer("City * — обязательное поле.\nEnter city")
        return
    await state.update_data(city=message.text.strip())
    await state.set_state(ReceiptForm.zip_code)
    await message.answer(
        f"{PART3_HEADER}\n\n<b>ZIP Code *</b>\nEnter ZIP code",
        reply_markup=cancel_keyboard(),
    )


@dp.message(ReceiptForm.zip_code)
async def process_zip_code(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.strip():
        await message.answer("ZIP Code * — обязательное поле.\nEnter ZIP code")
        return
    await state.update_data(zip_code=message.text.strip())
    await state.set_state(ReceiptForm.phone_number)
    await message.answer(
        f"{PART3_HEADER}\n\n<b>Phone Number *</b>\nEnter phone number",
        reply_markup=cancel_keyboard(),
    )


@dp.message(ReceiptForm.phone_number)
async def process_phone_number(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.strip():
        await message.answer("Phone Number * — обязательное поле.\nEnter phone number")
        return
    await state.update_data(phone_number=message.text.strip())
    await state.set_state(ReceiptForm.state_field)
    await message.answer(
        f"{PART3_HEADER}\n\n<b>State *</b>\nEnter state",
        reply_markup=cancel_keyboard(),
    )


@dp.message(ReceiptForm.state_field)
async def process_state_field(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.strip():
        await message.answer("State * — обязательное поле.\nEnter state")
        return
    await state.update_data(state_field=message.text.strip())
    data = await state.get_data()
    await state.set_state(ReceiptForm.preview)
    await message.answer(
        format_preview(data),
        reply_markup=preview_keyboard(),
    )


@dp.callback_query(F.data == "send_receipt")
async def on_send_receipt(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ReceiptForm.email)
    await callback.message.answer(
        "✉️ Введите email, на который отправить чек:",
        reply_markup=cancel_keyboard(),
    )


@dp.message(ReceiptForm.email)
async def process_email(message: Message, state: FSMContext) -> None:
    email = (message.text or "").strip()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        await message.answer("Введите корректный email:")
        return

    data = await state.get_data()
    receipt_data = {
        "name": data["name"],
        "surname": data["surname"],
        "product_name": data["product_name"],
        "order_date": data["order_date"],
        "product_image_url": data["product_image_url"],
        "price": data["product_price"],
        "street": data["street"],
        "city": data["city"],
        "zip_code": data["zip_code"],
        "state": data["state_field"],
        "phone": data["phone_number"],
        "order_number": data["order_number"],
    }

    await message.answer("⏳ Генерирую чек и отправляю на email...")

    OUTPUT_DIR.mkdir(exist_ok=True)
    image_path = OUTPUT_DIR / f"receipt_{message.from_user.id}.png"
    generate_receipt_image(receipt_data, image_path)
    send_receipt_email(
        email,
        f"<p>Your Apple Receipt {data['order_number']} is attached.</p>",
        image_path,
    )

    await message.answer(
        f"✅ Чек отправлен на {email}\nOrder Number: {data['order_number']}"
    )
    await state.clear()


@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await start_part1(message, state)


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
