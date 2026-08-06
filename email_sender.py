import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

GMAIL_ADDRESS = "oficcialbrandeu@gmail.com"
GMAIL_APP_PASSWORD = "jtnpbndftzlwfxna"
DEFAULT_EMAIL_SUBJECT = "Ваш чек Apple"


def send_receipt_email(
    recipient: str,
    html_body: str,
    image_path: Path,
    subject: str = DEFAULT_EMAIL_SUBJECT,
) -> None:
    message = MIMEMultipart("related")
    message["Subject"] = subject
    message["From"] = f"Apple Store <{GMAIL_ADDRESS}>"
    message["To"] = recipient

    with open(image_path, "rb") as image_file:
        image_data = image_file.read()

    html_part = MIMEText(html_body, "html", "utf-8")
    message.attach(html_part)

    image_part = MIMEImage(image_data, _subtype="png")
    image_part.add_header("Content-ID", "<receipt>")
    image_part.add_header("Content-Disposition", "inline", filename="receipt.png")
    message.attach(image_part)

    attachment_part = MIMEImage(image_data, _subtype="png")
    attachment_part.add_header("Content-Disposition", "attachment", filename="receipt.png")
    message.attach(attachment_part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, recipient, message.as_string())
