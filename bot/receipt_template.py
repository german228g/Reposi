from __future__ import annotations

import html
import random
from typing import Any

from bot.template_assets import APPLE_LOGO_SVG, WARRANTY_HTML

# Apple receipt outer background (beige/gray)
OUTER_BG = "#f5f5f7"
CARD_BG = "#ffffff"
BORDER = "#d2d2d7"
LINK = "#0066cc"

DEMO_BANNER = f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#ff3b30">
  <tr>
    <td align="center" style="padding:10px 16px;font-family:Helvetica,Arial,sans-serif;font-size:13px;font-weight:700;color:#ffffff;letter-spacing:.4px;">
      DEMO / NOT A REAL RECEIPT
    </td>
  </tr>
</table>
"""


def generate_order_number() -> str:
    return f"W{random.randint(10000000, 99999999)}"


def full_name(data: dict[str, Any]) -> str:
    return f"{data['name']} {data['surname']}".strip()


def email_subject(data: dict[str, Any]) -> str:
    return f"Your Apple Order Receipt - {data['order_number']}"


def format_preview(data: dict[str, Any]) -> str:
    return (
        "🍎 Apple Receipt Preview\n\n"
        "Customer Details:\n"
        f"• Name: {full_name(data)}\n"
        f"• Address: {data['street']}\n"
        f"• Location: {data['city']}, {data['state']} {data['zip_code']}\n"
        f"• Phone: {data['phone']}\n\n"
        "Order Information:\n"
        f"• Product: {data['product_name']}\n"
        f"• Order Number: {data['order_number']}\n"
        f"• Price: {data['product_price']}\n"
        f"• Order Date: {data['order_date']}\n\n"
        "Click 'Send Receipt' to receive it in your email or "
        "'Start Over' to make changes.\n\n"
        "⚠️ DEMO / NOT A REAL RECEIPT"
    )


def render_plain(data: dict[str, Any]) -> str:
    name = full_name(data)
    return f"""Thank you for your order.

Order Number: {data['order_number']}
Ordered on: {data['order_date']}

{data['product_name']} — {data['product_price']}

Bill To: {name}

---
DEMO / NOT A REAL RECEIPT
"""


def _section_row(label: str, content: str) -> str:
    return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{CARD_BG}">
  <tr>
    <td width="28%" valign="top" bgcolor="{CARD_BG}" style="padding:22px 16px 22px 32px;border-top:1px solid {BORDER};border-right:1px solid {BORDER};font-family:Helvetica,Arial,sans-serif;font-size:14px;font-weight:600;line-height:1.35;color:#1d1d1f;">
      {label}
    </td>
    <td width="72%" valign="top" bgcolor="{CARD_BG}" style="padding:22px 32px 22px 20px;border-top:1px solid {BORDER};font-family:Helvetica,Arial,sans-serif;font-size:14px;line-height:1.5;color:#1d1d1f;">
      {content}
    </td>
  </tr>
</table>
"""


def render_html(data: dict[str, Any]) -> str:
    name = html.escape(full_name(data))
    order_no = html.escape(data["order_number"])
    order_date = html.escape(data["order_date"])
    product = html.escape(data["product_name"])
    price = html.escape(data["product_price"])
    image_url = html.escape(data["product_image_url"])
    street = html.escape(data["street"])
    city = html.escape(data["city"])
    zip_code = html.escape(data["zip_code"])
    state = html.escape(data["state"])
    phone = html.escape(data["phone"])

    items_content = f"""
      <span style="font-size:12px;font-weight:700;letter-spacing:.02em;">EXPRESS SHIPPING</span><br>
      <span style="font-size:12px;">Delivery: Today from Store , 2 p.m. - 4 p.m. by Scheduled Courier Delivery</span>
      <table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{CARD_BG}" style="margin-top:16px;border-top:1px solid {BORDER};">
        <tr>
          <td width="64" valign="top" style="padding-top:16px;padding-right:12px;">
            <img src="{image_url}" alt="image" width="56" height="56" style="display:block;border:0;max-width:56px;">
          </td>
          <td valign="top" style="padding-top:16px;font-size:14px;line-height:1.4;">
            {product}<br>{price}<br>Qty 1
          </td>
          <td valign="top" align="right" style="padding-top:16px;font-size:14px;white-space:nowrap;">{price}</td>
        </tr>
      </table>
      <table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{CARD_BG}" style="margin-top:20px;border-top:1px solid {BORDER};">
        <tr>
          <td style="padding-top:16px;font-size:14px;line-height:1.5;">
            <strong>Shipping Address:</strong><br>
            {street}<br>{city}<br>{zip_code}<br>{state}<br>{phone}
          </td>
        </tr>
      </table>
    """

    billing_content = f"""
      <strong>Bill To:</strong><br>{name}<br><br>
      <strong>Billing Address:</strong><br>
      {street}<br>{city}<br>{zip_code}<br>{phone}<br><br>
      <table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{CARD_BG}">
        <tr><td>Bag Subtotal</td><td align="right">{price}</td></tr>
        <tr><td>Delivery</td><td align="right" style="color:#34c759;font-weight:600;">SHIPPING</td></tr>
        <tr><td style="padding-top:10px;font-weight:700;">Order Total</td><td align="right" style="padding-top:10px;font-weight:700;">{price}</td></tr>
      </table>
      <p style="margin:16px 0 0;font-size:12px;line-height:1.5;">Your invoice will be sent via email 2–3 business days after receipt of your order.</p>
    """

    questions_content = """
      <p style="margin:0 0 14px;font-size:12px;line-height:1.55;"><strong>When will I get my items?</strong><br>
      There is a ‘Delivers’ estimate above each item. This tells you when your items are expected to arrive. Once your items have dispatched, you’ll receive a Dispatch Notification email with a delivery reference number. You can also visit online <a href="#" style="color:#0066cc;text-decoration:none;">Order Status</a> to view the most up-to-date status of your order.</p>
      <p style="margin:0 0 14px;font-size:12px;line-height:1.55;">If you ordered multiple items and have chosen to receive separate shipments, you’ll receive a separate email as each item ships.</p>
      <p style="margin:0 0 14px;font-size:12px;line-height:1.55;"><strong>How do I view or change my order?</strong><br>
      Go to <a href="#" style="color:#0066cc;text-decoration:none;">Order Status</a>, then sign in to add your order to your Apple ID. You can make changes to, return, or cancel eligible items there. To learn more about shipping, changing, or returning orders, please visit the <a href="#" style="color:#0066cc;text-decoration:none;">Help</a> page.</p>
      <p style="margin:0 0 14px;font-size:12px;line-height:1.55;">You can also call Apple Store Customer Service on 0800 048 0408 (freephone), Monday–Friday 08:00–20:00, Saturday–Sunday 09:00–18:00. Please have your Order Number available.</p>
      <p style="margin:0;font-size:12px;line-height:1.55;"><strong>Recycling Options.</strong><br>
      You can drop off old devices at an Apple Store or local collection point for recycling. <a href="#" style="color:#0066cc;text-decoration:none;">Learn More &gt;</a></p>
    """

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="color-scheme" content="light">
  <meta name="supported-color-schemes" content="light">
</head>
<body style="margin:0;padding:0;width:100%;background-color:{OUTER_BG};">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{OUTER_BG}" role="presentation" style="width:100%;background-color:{OUTER_BG};">
    <tr>
      <td align="center" bgcolor="{OUTER_BG}" style="padding:16px 10px;background-color:{OUTER_BG};">
        <table width="680" cellpadding="0" cellspacing="0" border="0" bgcolor="{CARD_BG}" role="presentation" style="width:100%;max-width:680px;background-color:{CARD_BG};">
          <tr><td bgcolor="{CARD_BG}">{DEMO_BANNER}</td></tr>
          <tr>
            <td align="center" bgcolor="{CARD_BG}" style="padding:28px 24px 16px;background-color:{CARD_BG};">
              {APPLE_LOGO_SVG}
            </td>
          </tr>
          <tr>
            <td align="center" bgcolor="{CARD_BG}" style="padding:0 24px 8px;background-color:{CARD_BG};font-family:Helvetica,Arial,sans-serif;">
              <h1 style="margin:0;font-size:32px;line-height:1.12;font-weight:600;color:#1d1d1f;">Thank you for your order.</h1>
            </td>
          </tr>
          <tr>
            <td align="center" bgcolor="{CARD_BG}" style="padding:0 24px 20px;background-color:{CARD_BG};font-family:Helvetica,Arial,sans-serif;font-size:14px;line-height:1.45;color:#1d1d1f;">
              One or more of your items will be delivered by a courier service.<br>
              Someone must be present to receive these items.
            </td>
          </tr>
          <tr>
            <td align="center" bgcolor="{CARD_BG}" style="padding:0 24px 24px;background-color:{CARD_BG};font-family:Helvetica,Arial,sans-serif;font-size:14px;line-height:1.6;color:#1d1d1f;">
              <strong>Order Number:</strong> <a href="#" style="color:{LINK};text-decoration:none;">{order_no}</a><br>
              <strong>Ordered on:</strong> {order_date}
            </td>
          </tr>
          <tr><td bgcolor="{CARD_BG}">{_section_row("Items to be<br>Dispatched", items_content)}</td></tr>
          <tr><td bgcolor="{CARD_BG}">{_section_row("Billing and<br>Payment", billing_content)}</td></tr>
          <tr><td bgcolor="{CARD_BG}">{_section_row("Questions", questions_content)}</td></tr>
          <tr>
            <td align="center" bgcolor="{OUTER_BG}" style="padding:24px 24px;background-color:{OUTER_BG};border-top:1px solid {BORDER};font-family:Helvetica,Arial,sans-serif;font-size:11px;line-height:1.6;color:#6e6e73;">
              <a href="#" style="color:{LINK};text-decoration:none;">Shop Online</a> |
              <a href="#" style="color:{LINK};text-decoration:none;">Find a Store</a> |
              <a href="#" style="color:{LINK};text-decoration:none;">0800 048 0408</a> |
              <a href="#" style="color:{LINK};text-decoration:none;">Get the Apple Store App</a><br><br>
              Apple Distribution International Ltd., Hollyhill Industrial Estate, Hollyhill, Cork, Republic of Ireland.<br>
              Copyright © 2024 Apple Inc. All rights reserved.<br>
              <a href="#" style="color:{LINK};text-decoration:none;">Terms of Use</a> |
              <a href="#" style="color:{LINK};text-decoration:none;">Privacy Policy</a> |
              <a href="#" style="color:{LINK};text-decoration:none;">Sales and Refunds</a>
            </td>
          </tr>
          <tr><td bgcolor="{CARD_BG}">{WARRANTY_HTML}</td></tr>
          <tr><td bgcolor="{CARD_BG}">{DEMO_BANNER}</td></tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
