from __future__ import annotations

import html
import random
from typing import Any

from bot.template_assets import APPLE_LOGO_SVG, WARRANTY_HTML

DEMO_BANNER = (
    '<div style="background:#ff3b30;color:#fff;text-align:center;padding:10px 16px;'
    'font-weight:700;font-size:13px;letter-spacing:.4px;">'
    "DEMO / NOT A REAL RECEIPT</div>"
)


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


def _cell_label(text: str) -> str:
    return (
        f'<td style="width:27%;padding:22px 18px 22px 40px;vertical-align:top;'
        f'font-size:14px;font-weight:600;color:#1d1d1f;line-height:1.35;'
        f'border-right:1px solid #d2d2d7;border-top:1px solid #d2d2d7;">{text}</td>'
    )


def render_plain(data: dict[str, Any]) -> str:
    name = full_name(data)
    return f"""Thank you for your order.

One or more of your items will be delivered by a courier service.
Someone must be present to receive these items.

Order Number: {data['order_number']}
Ordered on: {data['order_date']}

Items to be Dispatched
EXPRESS SHIPPING
Delivery: Today from Store , 2 p.m. - 4 p.m. by Scheduled Courier Delivery

{data['product_name']}
{data['product_price']}
Qty 1
{data['product_price']}

Shipping Address:
{data['street']}
{data['city']}
{data['zip_code']}
{data['state']}
{data['phone']}

Bill To:
{name}

Billing Address:
{data['street']}
{data['city']}
{data['zip_code']}
{data['phone']}

Bag Subtotal {data['product_price']}
Delivery SHIPPING
Order Total {data['product_price']}

---
DEMO / NOT A REAL RECEIPT
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

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#f5f5f7;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;color:#1d1d1f;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f7;">
    <tr><td align="center" style="padding:0;">
      <table width="706" cellpadding="0" cellspacing="0" style="max-width:706px;width:100%;background:#ffffff;">
        <tr><td>{DEMO_BANNER}</td></tr>
        <tr><td style="padding:28px 0 18px;text-align:center;">{APPLE_LOGO_SVG}</td></tr>
        <tr><td style="padding:0 40px 10px;text-align:center;">
          <h1 style="margin:0;font-size:32px;line-height:1.125;font-weight:600;letter-spacing:-.003em;">Thank you for your order.</h1>
        </td></tr>
        <tr><td style="padding:0 40px 24px;text-align:center;font-size:14px;line-height:1.42857;color:#1d1d1f;">
          One or more of your items will be delivered by a courier service.<br>
          Someone must be present to receive these items.
        </td></tr>
        <tr><td style="padding:0 40px 24px;font-size:14px;line-height:1.6;">
          <strong>Order Number:</strong> <a href="#" style="color:#0066cc;text-decoration:none;">{order_no}</a><br>
          <strong>Ordered on:</strong> {order_date}
        </td></tr>

        <tr>
          {_cell_label("Items to be<br>Dispatched")}
          <td style="padding:22px 40px 22px 24px;vertical-align:top;border-top:1px solid #d2d2d7;font-size:14px;line-height:1.5;">
            <div style="font-size:12px;font-weight:700;letter-spacing:.02em;margin-bottom:4px;">EXPRESS SHIPPING</div>
            <div style="font-size:12px;color:#1d1d1f;margin-bottom:18px;">
              Delivery: Today from Store , 2 p.m. - 4 p.m. by Scheduled Courier Delivery
            </div>
            <table width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid #d2d2d7;">
              <tr>
                <td width="72" style="padding:16px 12px 0 0;vertical-align:top;">
                  <img src="{image_url}" alt="image" width="56" height="56" style="display:block;border:0;">
                </td>
                <td style="padding:16px 0 0;vertical-align:top;font-size:14px;line-height:1.4;">
                  <div>{product}</div>
                  <div>{price}</div>
                  <div>Qty 1</div>
                </td>
                <td style="padding:16px 0 0;vertical-align:top;text-align:right;font-size:14px;white-space:nowrap;">{price}</td>
              </tr>
            </table>
            <div style="margin-top:22px;padding-top:18px;border-top:1px solid #d2d2d7;font-size:14px;line-height:1.5;">
              <strong>Shipping Address:</strong><br>
              {street}<br>
              {city}<br>
              {zip_code}<br>
              {state}<br>
              {phone}
            </div>
          </td>
        </tr>

        <tr>
          {_cell_label("Billing and<br>Payment")}
          <td style="padding:22px 40px 22px 24px;vertical-align:top;border-top:1px solid #d2d2d7;font-size:14px;line-height:1.5;">
            <strong>Bill To:</strong><br>{name}<br><br>
            <strong>Billing Address:</strong><br>
            {street}<br>
            {city}<br>
            {zip_code}<br>
            {phone}<br><br>
            <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;">
              <tr>
                <td>Bag Subtotal</td>
                <td align="right">{price}</td>
              </tr>
              <tr>
                <td>Delivery</td>
                <td align="right" style="color:#34c759;font-weight:600;">SHIPPING</td>
              </tr>
              <tr>
                <td style="padding-top:10px;font-weight:700;">Order Total</td>
                <td align="right" style="padding-top:10px;font-weight:700;">{price}</td>
              </tr>
            </table>
            <p style="margin:18px 0 0;font-size:12px;line-height:1.5;color:#1d1d1f;">
              Your invoice will be sent via email 2–3 business days after receipt of your order.
            </p>
          </td>
        </tr>

        <tr>
          {_cell_label("Questions")}
          <td style="padding:22px 40px 22px 24px;vertical-align:top;border-top:1px solid #d2d2d7;font-size:12px;line-height:1.55;color:#1d1d1f;">
            <p style="margin:0 0 14px;"><strong>When will I get my items?</strong><br>
            There is a ‘Delivers’ estimate above each item. This tells you when your items are expected to arrive. Once your items have dispatched, you’ll receive a Dispatch Notification email with a delivery reference number. You can also visit online <a href="#" style="color:#0066cc;text-decoration:none;">Order Status</a> to view the most up-to-date status of your order.</p>
            <p style="margin:0 0 14px;">If you ordered multiple items and have chosen to receive separate shipments, you’ll receive a separate email as each item ships.</p>
            <p style="margin:0 0 14px;"><strong>How do I view or change my order?</strong><br>
            Go to <a href="#" style="color:#0066cc;text-decoration:none;">Order Status</a>, then sign in to add your order to your Apple ID. You can make changes to, return, or cancel eligible items there. To learn more about shipping, changing, or returning orders, please visit the <a href="#" style="color:#0066cc;text-decoration:none;">Help</a> page.</p>
            <p style="margin:0 0 14px;">You can also call Apple Store Customer Service on 0800 048 0408 (freephone), Monday–Friday 08:00–20:00, Saturday–Sunday 09:00–18:00. Please have your Order Number available.</p>
            <p style="margin:0;"><strong>Recycling Options.</strong><br>
            You can drop off old devices at an Apple Store or local collection point for recycling. <a href="#" style="color:#0066cc;text-decoration:none;">Learn More &gt;</a></p>
          </td>
        </tr>

        <tr><td style="background:#f5f5f7;padding:24px 40px;text-align:center;font-size:11px;line-height:1.6;color:#6e6e73;border-top:1px solid #d2d2d7;">
          <a href="#" style="color:#0066cc;text-decoration:none;">Shop Online</a> |
          <a href="#" style="color:#0066cc;text-decoration:none;">Find a Store</a> |
          <a href="#" style="color:#0066cc;text-decoration:none;">0800 048 0408</a> |
          <a href="#" style="color:#0066cc;text-decoration:none;">Get the Apple Store App</a><br><br>
          Apple Distribution International Ltd., Hollyhill Industrial Estate, Hollyhill, Cork, Republic of Ireland.<br>
          Copyright © 2024 Apple Inc. All rights reserved.<br>
          <a href="#" style="color:#0066cc;text-decoration:none;">Terms of Use</a> |
          <a href="#" style="color:#0066cc;text-decoration:none;">Privacy Policy</a> |
          <a href="#" style="color:#0066cc;text-decoration:none;">Sales and Refunds</a>
        </td></tr>

        <tr><td style="background:#ffffff;">{WARRANTY_HTML}</td></tr>
        <tr><td>{DEMO_BANNER}</td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
