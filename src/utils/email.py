import smtplib
from email.message import EmailMessage

from src.config.settings import settings


def send_otp_email(to_email: str, otp: str) -> None:
    """
    Dispatch a highly secure One-Time Password to the requested user.

    If TEST_SMTP is active, it intercepts the transmission and logs the OTP locally to bypass network latency during development.

    Args:
        to_email (str): Target email address.
        otp (str): The one-time password to dispatch.

    Returns:
        None: Executed natively.

    """
    subject = "DeciMark - Your 2FA Verification Code"
    body = f"Your DeciMark authentication code is: {otp}\\n\\nThis code expires in 5 minutes. Do not share it with anyone."

    if settings.TEST.SMTP:
        print(f"\\n{'='*50}")
        print(f"MOCK SMTP INTERCEPT: EMAIL TO {to_email}")
        print(f"OTP CODE: {otp}")
        print(f"{'='*50}\\n")
        return

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP.USERNAME
    msg["To"] = to_email

    try:
        # Use synchronous smtplib for absolute stability, or aiosmtplib if async is strictly required.
        # For a standard 2FA dispatch, this is perfectly adequate.
        with smtplib.SMTP(settings.SMTP.HOST, settings.SMTP.PORT) as server:
            server.starttls()
            server.login(settings.SMTP.USERNAME, settings.SMTP.PASSWORD)
            server.send_message(msg)
    except Exception as e:  # noqa: BLE001
        print(f"CRITICAL SMTP FAILURE: {e}")
