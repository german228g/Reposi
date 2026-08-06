import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

GMAIL_ADDRESS = "oficcialbrandeu@gmail.com"
GMAIL_APP_PASSWORD = "jtnpbndftzlwfxna"
DEFAULT_EMAIL_SUBJECT = "Ваш чек"


def send_receipt_email(
    recipient: str,
    image_path: Path,
    order_number: str,
    buyer_name: str,
    product_name: str,
    amount: str,
    subject: str = DEFAULT_EMAIL_SUBJECT,
) -> None:
    message = MIMEMultipart("related")
    message["Subject"] = subject
    message["From"] = f"OFFICIALBRAND <{GMAIL_ADDRESS}>"
    message["To"] = recipient

    alternative = MIMEMultipart("alternative")
    message.attach(alternative)

    text_body = (
        f"Здравствуйте, {buyer_name}!\n\n"
        f"Ваш чек по заказу {order_number}.\n"
        f"Товар: {product_name}\n"
        f"Сумма: {amount}\n"
    )
    html_body = f"""
    <html>
      <body style="margin:0;padding:24px;background:#f5f5f7;font-family:Arial,Helvetica,sans-serif;">
        <div style="max-width:680px;margin:0 auto;background:#ffffff;border-radius:12px;padding:24px;">
          <p style="font-size:16px;color:#1c1c1e;">Здравствуйте, <b>{buyer_name}</b>!</p>
          <p style="font-size:14px;color:#3a3a3c;">Ваш чек по заказу <b>{order_number}</b>.</p>
          <p style="font-size:14px;color:#3a3a3c;">Товар: {product_name}<br>Сумма: {amount}</p>
          <div style="margin-top:20px;text-align:center;">
            <img src="cid:receipt" alt="Чек" style="max-width:100%;height:auto;border:0;" />
          </div>
        </div>
      </body>
    </html>
    """
    alternative.attach(MIMEText(text_body, "plain", "utf-8"))
    alternative.attach(MIMEText(html_body, "html", "utf-8"))

    with open(image_path, "rb") as file:
        image_data = file.read()

    inline = MIMEImage(image_data, _subtype="png")
    inline.add_header("Content-ID", "<receipt>")
    inline.add_header("Content-Disposition", "inline", filename="receipt.png")
    message.attach(inline)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, recipient, message.as_string())
