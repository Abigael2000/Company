import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.zoho.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
COMPANY_EMAIL = os.environ.get("COMPANY_EMAIL", SMTP_USER)


def _send(to_address: str, subject: str, body: str, reply_to: str = None) -> bool:
    if not SMTP_USER or not SMTP_PASSWORD or not to_address:
        return False

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = to_address
    msg["Subject"] = subject

    if reply_to:
        msg["Reply-To"] = reply_to

    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(
                SMTP_USER,
                to_address,
                msg.as_string()
            )

        return True

    except Exception as e:
        print(f"Email sending failed: {e}")
        return False


def notify_company(subject: str, body: str, reply_to: str = None) -> bool:
    """Send an email to the company's inbox."""
    return _send(
        COMPANY_EMAIL,
        subject,
        body,
        reply_to=reply_to
    )


def notify_customer(to_address: str, subject: str, body: str) -> bool:
    """Send a confirmation email to the customer."""
    return _send(
        to_address,
        subject,
        body
    )


def send_bulk(
    addresses: list[str],
    subject: str,
    body: str
) -> tuple[int, int]:

    if not SMTP_USER or not SMTP_PASSWORD or not addresses:
        return 0, len(addresses)

    sent = 0
    failed = 0

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)

            for addr in addresses:
                msg = MIMEMultipart()
                msg["From"] = SMTP_USER
                msg["To"] = addr
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain"))

                try:
                    server.sendmail(
                        SMTP_USER,
                        addr,
                        msg.as_string()
                    )
                    sent += 1

                except Exception as e:
                    print(f"Failed to send to {addr}: {e}")
                    failed += 1

    except Exception as e:
        print(f"SMTP connection failed: {e}")
        return 0, len(addresses)

    return sent, failed
