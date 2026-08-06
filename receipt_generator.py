import io
import random
import string
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path(__file__).parent / "output"

WIDTH = 680
MARGIN = 44
WHITE = (255, 255, 255)
BLACK = (28, 28, 30)
GRAY = (110, 110, 115)
LIGHT = (220, 220, 224)
ACCENT = (30, 30, 32)


def generate_order_number() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"ORDER-{suffix}"


def random_amount() -> str:
    value = random.randint(10, 500)
    return f"${value}"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    paths = (
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
        if bold
        else [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
    )
    for path in paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def _hline(draw: ImageDraw.ImageDraw, y: int) -> int:
    draw.line([(MARGIN, y), (WIDTH - MARGIN, y)], fill=LIGHT, width=1)
    return y + 1


def _prepare_photo(photo_bytes: bytes, size: int = 260) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(photo_bytes)).convert("RGBA")
    except Exception:
        img = Image.new("RGBA", (size, size), (245, 245, 247, 255))
    img.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), WHITE + (255,))
    canvas.paste(img, ((size - img.width) // 2, (size - img.height) // 2), img)
    return canvas


def generate_receipt_image(data: dict, output_path: Path) -> Path:
    product_name = data["product_name"]
    buyer_name = data["buyer_name"]
    order_number = data["order_number"]
    amount = data["amount"]
    created_at = data.get("created_at") or datetime.now().strftime("%d.%m.%Y %H:%M")
    photo = _prepare_photo(data["photo_bytes"], size=260)

    canvas_h = 1180
    image = Image.new("RGB", (WIDTH, canvas_h), WHITE)
    draw = ImageDraw.Draw(image)
    y = 42

    brand_font = _font(22, bold=True)
    brand = "OFFICIALBRAND"
    bw, bh = _size(draw, brand, brand_font)
    draw.text(((WIDTH - bw) / 2, y), brand, fill=ACCENT, font=brand_font)
    y += bh + 28

    title_font = _font(26, bold=True)
    title = "Спасибо за заказ"
    tw, th = _size(draw, title, title_font)
    draw.text(((WIDTH - tw) / 2, y), title, fill=BLACK, font=title_font)
    y += th + 10

    sub_font = _font(13)
    subtitle = "Ваш заказ подтверждён. Чек сформирован автоматически."
    sw, sh = _size(draw, subtitle, sub_font)
    draw.text(((WIDTH - sw) / 2, y), subtitle, fill=GRAY, font=sub_font)
    y += sh + 22
    y = _hline(draw, y) + 22

    meta_font = _font(13)
    meta_bold = _font(13, bold=True)
    draw.text((MARGIN, y), "Номер заказа:", fill=GRAY, font=meta_font)
    draw.text((MARGIN + 130, y), order_number, fill=BLACK, font=meta_bold)
    y += 22
    draw.text((MARGIN, y), "Дата и время:", fill=GRAY, font=meta_font)
    draw.text((MARGIN + 130, y), created_at, fill=BLACK, font=meta_bold)
    y += 28
    y = _hline(draw, y) + 28

    frame = 14
    box = photo.width + frame * 2
    bx = (WIDTH - box) // 2
    draw.rounded_rectangle(
        [bx, y, bx + box, y + box],
        radius=14,
        outline=LIGHT,
        width=2,
        fill=WHITE,
    )
    image.paste(photo.convert("RGB"), (bx + frame, y + frame))
    y += box + 24

    name_font = _font(20, bold=True)
    nw, nh = _size(draw, product_name, name_font)
    draw.text(((WIDTH - nw) / 2, y), product_name, fill=BLACK, font=name_font)
    y += nh + 14

    info_font = _font(14)
    buyer_line = f"Покупатель: {buyer_name}"
    lw, lh = _size(draw, buyer_line, info_font)
    draw.text(((WIDTH - lw) / 2, y), buyer_line, fill=BLACK, font=info_font)
    y += lh + 10

    amount_font = _font(30, bold=True)
    aw, ah = _size(draw, amount, amount_font)
    draw.text(((WIDTH - aw) / 2, y), amount, fill=BLACK, font=amount_font)
    y += ah + 26
    y = _hline(draw, y) + 24

    thanks_font = _font(16, bold=True)
    thanks = "Благодарим за покупку в OFFICIALBRAND"
    tw, th = _size(draw, thanks, thanks_font)
    draw.text(((WIDTH - tw) / 2, y), thanks, fill=BLACK, font=thanks_font)
    y += th + 16

    foot_font = _font(12)
    for line in (
        f"Заказ {order_number}",
        f"Итого: {amount}",
        f"Дата: {created_at}",
        "OFFICIALBRAND Store Online",
    ):
        fw, fh = _size(draw, line, foot_font)
        color = GRAY if "Store" in line else BLACK
        draw.text(((WIDTH - fw) / 2, y), line, fill=color, font=foot_font)
        y += fh + 8

    y += 20
    draw.rectangle([0, y, WIDTH, y + 70], fill=(248, 248, 250))
    small = _font(11)
    footer = "OFFICIALBRAND  ·  support@officialbrand.local  ·  Все права защищены"
    fw, fh = _size(draw, footer, small)
    draw.text(((WIDTH - fw) / 2, y + 26), footer, fill=GRAY, font=small)

    final = image.crop((0, 0, WIDTH, y + 70))
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = Path(output_path)
    final.save(output_path, "PNG", optimize=True)
    return output_path
