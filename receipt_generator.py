import random
import string
from pathlib import Path

import imgkit
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent / "templates"
OUTPUT_DIR = Path(__file__).parent / "output"


def generate_order_number() -> str:
    digits = "".join(random.choices(string.digits, k=8))
    return f"W{digits}"


def build_receipt_html(data: dict) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("receipt.html")
    return template.render(
        order_number=data["order_number"],
        order_date=data["order_date"],
        product_name=data["product_name"],
        product_image_url=data["product_image_url"],
        price=data["price"],
        street=data["street"],
        city=data["city"],
        zip_code=data["zip_code"],
        state=data["state"],
        phone=data["phone"],
        full_name=f"{data['name']} {data['surname']}",
    )


def render_receipt_image(html: str, output_path: Path) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    options = {
        "width": 680,
        "quality": 100,
        "enable-local-file-access": "",
        "quiet": "",
    }
    imgkit.from_string(html, str(output_path), options=options)
    return output_path
