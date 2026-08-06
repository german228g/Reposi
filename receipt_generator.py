import io
import random
import string
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path(__file__).parent / "output"

WIDTH = 680
MARGIN = 40
CONTENT_W = WIDTH - MARGIN * 2

WHITE = (255, 255, 255)
BLACK = (29, 29, 31)
GRAY = (102, 102, 102)
LIGHT_GRAY = (210, 210, 215)
LINK_BLUE = (0, 102, 204)
GREEN = (0, 128, 9)
FOOTER_BG = (245, 245, 247)
LOGO_GRAY = (134, 134, 139)


def generate_order_number() -> str:
    digits = "".join(random.choices(string.digits, k=8))
    return f"W{digits}"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]
        if bold
        else [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]
    )
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _serif(size: int) -> ImageFont.FreeTypeFont:
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return _font(size)


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _draw_apple_logo(draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float = 1.0) -> None:
    # Approximate Apple logo via filled ellipse + bite + leaf
    s = scale
    body = [
        (cx - 10 * s, cy - 2 * s),
        (cx - 12 * s, cy - 10 * s),
        (cx - 6 * s, cy - 16 * s),
        (cx + 2 * s, cy - 16 * s),
        (cx + 10 * s, cy - 10 * s),
        (cx + 12 * s, cy - 2 * s),
        (cx + 10 * s, cy + 10 * s),
        (cx + 2 * s, cy + 16 * s),
        (cx - 4 * s, cy + 16 * s),
        (cx - 10 * s, cy + 10 * s),
    ]
    draw.ellipse(
        [cx - 11 * s, cy - 14 * s, cx + 11 * s, cy + 14 * s],
        fill=LOGO_GRAY,
    )
    # bite
    draw.ellipse(
        [cx + 4 * s, cy - 6 * s, cx + 16 * s, cy + 6 * s],
        fill=WHITE,
    )
    # leaf
    draw.ellipse(
        [cx - 2 * s, cy - 22 * s, cx + 8 * s, cy - 12 * s],
        fill=LOGO_GRAY,
    )
    draw.ellipse(
        [cx + 2 * s, cy - 22 * s, cx + 12 * s, cy - 12 * s],
        fill=WHITE,
    )


def _load_product_image(url: str, size: int = 220) -> Image.Image:
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=15) as response:
            raw = response.read()
        img = Image.open(io.BytesIO(raw)).convert("RGBA")
    except Exception:
        img = Image.new("RGBA", (size, size), (240, 240, 245, 255))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, size - 1, size - 1], outline=LIGHT_GRAY, width=2)
        f = _font(16)
        tw, th = _text_size(d, "image", f)
        d.text(((size - tw) / 2, (size - th) / 2), "image", fill=GRAY, font=f)
        return img

    img.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), WHITE + (255,))
    ox = (size - img.width) // 2
    oy = (size - img.height) // 2
    canvas.paste(img, (ox, oy), img if img.mode == "RGBA" else None)
    return canvas


def _format_display_date(order_date: str) -> str:
    try:
        dt = datetime.strptime(order_date, "%Y-%m-%d")
        return dt.strftime("%d.%m.%Y")
    except ValueError:
        return order_date


def _hline(draw: ImageDraw.ImageDraw, y: int, x0: int = MARGIN, x1: int = WIDTH - MARGIN) -> int:
    draw.line([(x0, y), (x1, y)], fill=LIGHT_GRAY, width=1)
    return y + 1


def generate_receipt_image(data: dict, output_path: Path) -> Path:
    full_name = f"{data['name']} {data['surname']}"
    price = data["price"]
    if not str(price).startswith("$") and not any(c.isalpha() for c in str(price)):
        price = f"${price}"
    order_number = data["order_number"]
    order_date = data["order_date"]
    display_date = _format_display_date(order_date)
    order_datetime = data.get("order_datetime") or datetime.now().strftime("%d.%m.%Y %H:%M")
    product_name = data["product_name"]
    street = data["street"]
    city = data["city"]
    zip_code = data["zip_code"]
    state = data["state"]
    phone = data["phone"]

    product_img = _load_product_image(data["product_image_url"], size=240)

    # Build on a tall canvas then crop
    height_guess = 2200
    img = Image.new("RGB", (WIDTH, height_guess), WHITE)
    draw = ImageDraw.Draw(img)

    y = 36

    # Apple logo centered
    _draw_apple_logo(draw, WIDTH // 2, y + 16, scale=1.35)
    y += 48

    # Title
    title_font = _serif(34)
    title = "Thank you for your order."
    tw, th = _text_size(draw, title, title_font)
    draw.text(((WIDTH - tw) / 2, y), title, fill=BLACK, font=title_font)
    y += th + 16

    # Intro
    intro_font = _font(13)
    intro_lines = [
        "One or more of your items will be delivered by a courier service.",
        "Someone must be present to receive these items.",
    ]
    for line in intro_lines:
        lw, lh = _text_size(draw, line, intro_font)
        draw.text(((WIDTH - lw) / 2, y), line, fill=BLACK, font=intro_font)
        y += lh + 4
    y += 18

    # Order meta
    meta_font = _font(13)
    meta_bold = _font(13, bold=True)
    draw.text((MARGIN, y), "Order Number: ", fill=BLACK, font=meta_bold)
    label_w, _ = _text_size(draw, "Order Number: ", meta_bold)
    draw.text((MARGIN + label_w, y), order_number, fill=LINK_BLUE, font=meta_font)
    y += 20
    draw.text((MARGIN, y), "Ordered on: ", fill=BLACK, font=meta_bold)
    label_w, _ = _text_size(draw, "Ordered on: ", meta_bold)
    draw.text((MARGIN + label_w, y), order_date, fill=BLACK, font=meta_font)
    y += 24
    y = _hline(draw, y) + 18

    # Items to be Dispatched
    section_font = _font(14, bold=True)
    draw.text((MARGIN, y), "Items to be Dispatched", fill=BLACK, font=section_font)
    y += 26
    ship_font = _font(12, bold=True)
    draw.text((MARGIN, y), "EXPRESS SHIPPING", fill=BLACK, font=ship_font)
    y += 18
    body = _font(13)
    draw.text(
        (MARGIN, y),
        "Delivery: Today from Store , 2 p.m. - 4 p.m.",
        fill=BLACK,
        font=body,
    )
    y += 18
    draw.text((MARGIN, y), "by Scheduled Courier Delivery", fill=BLACK, font=body)
    y += 28

    # Large centered product photo with thin frame
    frame_pad = 14
    box = product_img.width + frame_pad * 2
    bx = (WIDTH - box) // 2
    draw.rounded_rectangle(
        [bx, y, bx + box, y + box],
        radius=12,
        outline=LIGHT_GRAY,
        width=2,
        fill=WHITE,
    )
    img.paste(product_img.convert("RGB"), (bx + frame_pad, y + frame_pad))
    y += box + 20

    # Product info block centered
    name_font = _font(20, bold=True)
    nw, nh = _text_size(draw, product_name, name_font)
    draw.text(((WIDTH - nw) / 2, y), product_name, fill=BLACK, font=name_font)
    y += nh + 12

    info_font = _font(14)
    purchased = f"Purchased by: {full_name}"
    pw, ph = _text_size(draw, purchased, info_font)
    draw.text(((WIDTH - pw) / 2, y), purchased, fill=BLACK, font=info_font)
    y += ph + 8

    date_line = f"Date: {display_date}"
    dw, dh = _text_size(draw, date_line, info_font)
    draw.text(((WIDTH - dw) / 2, y), date_line, fill=GRAY, font=info_font)
    y += dh + 12

    price_font = _font(28, bold=True)
    prw, prh = _text_size(draw, str(price), price_font)
    draw.text(((WIDTH - prw) / 2, y), str(price), fill=BLACK, font=price_font)
    y += prh + 8

    qty_font = _font(13)
    qw, qh = _text_size(draw, "Qty 1", qty_font)
    draw.text(((WIDTH - qw) / 2, y), "Qty 1", fill=BLACK, font=qty_font)
    y += qh + 22
    y = _hline(draw, y) + 18

    # Shipping Address
    addr_title = _font(13, bold=True)
    draw.text((MARGIN, y), "Shipping Address:", fill=BLACK, font=addr_title)
    y += 20
    for line in (street, city, zip_code, state, phone):
        draw.text((MARGIN, y), str(line), fill=BLACK, font=body)
        y += 18
    y += 8
    y = _hline(draw, y) + 18

    # Billing and Payment
    draw.text((MARGIN, y), "Billing and Payment", fill=BLACK, font=section_font)
    y += 24
    draw.text((MARGIN, y), f"Bill To: {full_name}", fill=BLACK, font=body)
    y += 20
    draw.text((MARGIN, y), "Billing Address:", fill=BLACK, font=addr_title)
    y += 20
    for line in (street, city, zip_code, state, phone):
        draw.text((MARGIN, y), str(line), fill=BLACK, font=body)
        y += 18
    y += 10
    y = _hline(draw, y) + 14

    # Totals
    def money_row(label: str, value: str, bold: bool = False, green: bool = False) -> None:
        nonlocal y
        lf = _font(13, bold=bold)
        vf = _font(13, bold=bold)
        color = GREEN if green else BLACK
        draw.text((MARGIN, y), label, fill=color, font=lf)
        vw, _ = _text_size(draw, value, vf)
        draw.text((WIDTH - MARGIN - vw, y), value, fill=color, font=vf)
        y += 22

    money_row("Bag Subtotal", str(price))
    money_row("Delivery", "SHIPPING", green=True)
    money_row("Order Total", str(price), bold=True)
    y += 6
    note = "Your invoice will be sent via email 2–3 business days after receipt of your order."
    note_font = _font(11)
    draw.text((MARGIN, y), note, fill=GRAY, font=note_font)
    y += 28
    y = _hline(draw, y) + 18

    # Questions (short, as in video)
    draw.text((MARGIN, y), "Questions", fill=BLACK, font=section_font)
    y += 24
    q_bold = _font(13, bold=True)
    draw.text((MARGIN, y), "When will I get my items?", fill=BLACK, font=q_bold)
    y += 20
    q_lines = [
        "There is a 'Delivers' estimate above each item. This tells you when",
        "your items are expected to arrive. Once your items have dispatched,",
        "you will receive a Dispatch Notification email with a delivery",
        "reference number. You can also visit online Order Status.",
    ]
    for line in q_lines:
        draw.text((MARGIN, y), line, fill=BLACK, font=_font(12))
        y += 16
    y += 20

    # Bottom thank-you block
    y = _hline(draw, y) + 22
    thanks_font = _serif(22)
    thanks = "Thank you for shopping with Apple"
    tw, th = _text_size(draw, thanks, thanks_font)
    draw.text(((WIDTH - tw) / 2, y), thanks, fill=BLACK, font=thanks_font)
    y += th + 16

    total_font = _font(16, bold=True)
    total_line = f"Order Total: {price}"
    tw, th = _text_size(draw, total_line, total_font)
    draw.text(((WIDTH - tw) / 2, y), total_line, fill=BLACK, font=total_font)
    y += th + 12

    foot_font = _font(13)
    for line in (
        f"Order Number: {order_number}",
        f"Date & Time: {order_datetime}",
        "Apple Store Online",
        "1 Infinite Loop, Cupertino, CA 95014",
    ):
        lw, lh = _text_size(draw, line, foot_font)
        color = GRAY if "Apple Store" in line or "Infinite" in line else BLACK
        draw.text(((WIDTH - lw) / 2, y), line, fill=color, font=foot_font)
        y += lh + 8

    y += 24

    # Legal footer strip (as in video)
    footer_top = y
    footer_h = 160
    draw.rectangle([0, footer_top, WIDTH, footer_top + footer_h], fill=FOOTER_BG)
    fy = footer_top + 18
    small = _font(10)
    links = "Shop Online  |  Find a Store  |  0800 048 0408  |  Get the Apple Store App"
    lw, lh = _text_size(draw, links, small)
    draw.text(((WIDTH - lw) / 2, fy), links, fill=LINK_BLUE, font=small)
    fy += lh + 12
    for line in (
        "Apple Distribution International Ltd., Hollyhill Industrial Estate,",
        "Hollyhill, Cork, Republic of Ireland.",
        "Copyright © 2024 Apple Inc. All rights reserved.",
        "Terms of Use  |  Privacy Policy  |  Sales and Refunds",
    ):
        draw.text((MARGIN, fy), line, fill=GRAY, font=small)
        fy += 14

    final_h = footer_top + footer_h
    img = img.crop((0, 0, WIDTH, final_h))

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = Path(output_path)
    img.save(output_path, "PNG", optimize=True)
    return output_path


# Backwards-compatible aliases used by older main.py
def build_receipt_html(data: dict) -> str:
    return (
        f"<html><body><p>Apple Receipt {data.get('order_number', '')}</p></body></html>"
    )


def render_receipt_image(html: str, output_path: Path) -> Path:
    raise RuntimeError("Use generate_receipt_image(data, output_path) instead")
