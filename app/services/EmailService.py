import logging
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from ..utils import get_email_settings

logger = logging.getLogger("uvicorn")
email_settings = get_email_settings()

conf = ConnectionConfig(
    MAIL_USERNAME=email_settings.MAIL_USERNAME,
    MAIL_PASSWORD=email_settings.MAIL_PASSWORD,
    MAIL_FROM=email_settings.MAIL_FROM,
    MAIL_PORT=email_settings.MAIL_PORT,
    MAIL_SERVER=email_settings.MAIL_SERVER,
    MAIL_STARTTLS=email_settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=email_settings.MAIL_SSL_TLS,
)


# Send Email Function
async def send_email(
    subject: str, 
    recipients: list, 
    body: dict, 
    template_name: str|None = None
):
    try:
        message = MessageSchema(
            subject=subject,
            recipients=recipients,  # List of recipients
            body=body,
            subtype="html",
        )
        fm = FastMail(conf)
        await fm.send_message(message, template_name=template_name)
    except Exception as e:
        logger.error(f"Something went wrong in send email")
        logger.error(str(e))
