from __future__ import annotations

import html
import random
from typing import Any


def generate_order_number() -> str:
    return f"W{random.randint(10000000, 99999999)}"


def full_name(data: dict[str, Any]) -> str:
    return f"{data['name']} {data['surname']}".strip()


def format_preview(data: dict[str, Any]) -> str:
    return (
        "🛍 OFFICIALBRAND Receipt Preview\n\n"
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
        "Нажми «Send Receipt» чтобы отправить на почту\n"
        "или «Start Over» чтобы начать заново.\n\n"
        "⚠️ DEMO / NOT A REAL RECEIPT"
    )


def render_plain(data: dict[str, Any]) -> str:
    name = full_name(data)
    return f"""OFFICIALBRAND — Order Receipt (DEMO)

Thank you for your order.

Order Number: {data['order_number']}
Ordered on: {data['order_date']}

Product: {data['product_name']}
Price: {data['product_price']}
Qty: 1

Shipping Address:
{data['street']}
{data['city']}
{data['zip_code']}
{data['state']}
{data['phone']}

Bill To: {name}

---
DEMO / NOT A REAL RECEIPT
This message is for educational demonstration only.
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
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f5f5f7;font-family:Arial,Helvetica,sans-serif;color:#1d1d1f;">
  <div style="max-width:680px;margin:0 auto;background:#fff;">
    <div style="background:#ff3b30;color:#fff;text-align:center;padding:14px 16px;font-weight:bold;font-size:14px;letter-spacing:.5px;">
      DEMO / NOT A REAL RECEIPT — EDUCATIONAL USE ONLY
    </div>
    <div style="padding:32px 40px 16px;text-align:center;">
      <div style="font-size:28px;font-weight:700;letter-spacing:1px;color:#111;">OFFICIALBRAND</div>
    </div>
    <div style="padding:0 40px 24px;text-align:center;">
      <h1 style="margin:0 0 12px;font-size:32px;font-weight:600;">Thank you for your order.</h1>
      <p style="margin:0;font-size:15px;color:#6e6e73;line-height:1.5;">
        One or more of your items will be delivered by a courier service.
        Someone must be present to receive these items.
      </p>
    </div>
    <div style="padding:0 40px 24px;font-size:14px;color:#1d1d1f;">
      <strong>Order Number:</strong> <span style="color:#0066cc;">{order_no}</span><br>
      <strong>Ordered on:</strong> {order_date}
    </div>
    <table width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid #d2d2d7;">
      <tr>
        <td style="width:28%;padding:24px 16px 24px 40px;vertical-align:top;font-size:14px;font-weight:600;color:#1d1d1f;border-right:1px solid #d2d2d7;">
          Items to be Dispatched
        </td>
        <td style="padding:24px 40px 24px 24px;vertical-align:top;">
          <div style="font-size:13px;font-weight:700;margin-bottom:4px;">EXPRESS SHIPPING</div>
          <div style="font-size:13px;color:#6e6e73;margin-bottom:20px;">
            Delivery: Today from Store, 2 p.m. - 4 p.m. by Scheduled Courier Delivery
          </div>
          <table width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid #d2d2d7;padding-top:16px;">
            <tr>
              <td style="width:72px;vertical-align:top;padding-top:8px;">
                <img src="{image_url}" alt="product" width="64" height="64" style="display:block;object-fit:contain;border:1px solid #e5e5ea;">
              </td>
              <td style="vertical-align:top;padding:8px 12px;font-size:14px;">
                <div style="font-weight:600;">{product}</div>
                <div style="color:#6e6e73;">{price}</div>
                <div style="color:#6e6e73;">Qty 1</div>
              </td>
              <td style="vertical-align:top;padding:8px 0;text-align:right;font-size:14px;font-weight:600;">{price}</td>
            </tr>
          </table>
          <div style="margin-top:24px;padding-top:16px;border-top:1px solid #d2d2d7;font-size:14px;line-height:1.6;">
            <strong>Shipping Address:</strong><br>
            {street}<br>
            {city}<br>
            {zip_code}<br>
            {state}<br>
            {phone}
          </div>
        </td>
      </tr>
    </table>
    <table width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid #d2d2d7;">
      <tr>
        <td style="width:28%;padding:24px 16px 24px 40px;vertical-align:top;font-size:14px;font-weight:600;border-right:1px solid #d2d2d7;">
          Billing and Payment
        </td>
        <td style="padding:24px 40px 24px 24px;font-size:14px;line-height:1.6;">
          <strong>Bill To:</strong> {name}<br><br>
          <strong>Billing Address:</strong><br>
          {street}<br>
          {city}<br>
          {zip_code}<br>
          {phone}<br><br>
          <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;">
            <tr><td>Bag Subtotal</td><td align="right">{price}</td></tr>
            <tr><td>Delivery</td><td align="right" style="color:#34c759;">SHIPPING</td></tr>
            <tr><td style="padding-top:8px;font-weight:700;">Order Total</td><td align="right" style="padding-top:8px;font-weight:700;">{price}</td></tr>
          </table>
          <p style="margin:16px 0 0;font-size:12px;color:#6e6e73;">
            Your invoice will be sent via email 2–3 business days after receipt of your order.
          </p>
        </td>
      </tr>
    </table>
    <table width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid #d2d2d7;">
      <tr>
        <td style="width:28%;padding:24px 16px 24px 40px;vertical-align:top;font-size:14px;font-weight:600;border-right:1px solid #d2d2d7;">
          Questions
        </td>
        <td style="padding:24px 40px 24px 24px;font-size:13px;line-height:1.6;color:#1d1d1f;">
          <strong>When will I get my items?</strong><br>
          Delivery estimates are shown above. This is a demo receipt for educational purposes only.<br><br>
          <strong>How do I view or change my order?</strong><br>
          This is not a real order. No changes can be made.
        </td>
      </tr>
    </table>
    <div style="background:#f5f5f7;padding:24px 40px;text-align:center;font-size:11px;color:#6e6e73;line-height:1.6;">
      OFFICIALBRAND Demo Store | support@officialbrand.demo<br>
      Copyright © 2026 OFFICIALBRAND Demo. All rights reserved.<br>
      Terms of Use | Privacy Policy | Sales and Refunds
    </div>
    <div style="background:#ff3b30;color:#fff;text-align:center;padding:14px 16px;font-weight:bold;font-size:14px;">
      DEMO / NOT A REAL RECEIPT
    </div>
  </div>
</body>
</html>"""
