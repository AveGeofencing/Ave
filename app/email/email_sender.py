from fastapi import HTTPException
from fastapi_mail import MessageSchema, MessageType, FastMail, ConnectionConfig
from jinja2 import Environment, FileSystemLoader

from .types import BaseEmail
from app.settings import email_config
from app.utils import logger

"""This maps the EmailType to the appopriate ConnectionConfig for the email sender."""


async def send_email_with_fastmail(
    subject: str, recipients: list[str], body: str, config: ConnectionConfig
) -> None:
    """
    General app-wide email sender.

    :param subject: Str - Subject of email message
    :param recipients: EmailStr - Email address of recipient
    :param body: Rendered HTML to be sent to the recipient
    :param config: ConnectionConfig - configuration for account to use for sending email.
    :return:
    """
    message = MessageSchema(
        subject=subject,
        recipients=recipients,  # type: ignore
        body=body,
        subtype=MessageType.html,
    )

    fm = FastMail(config)
    await fm.send_message(message)
    logger.info(f"Successfully sent email to {recipients}")


class EmailSender:
    def __init__(self, env: Environment | None = None):
        self.env = (
            env
            if env
            else Environment(
                loader=FileSystemLoader("app/email/templates"),
                enable_async=True,
            )
        )

    async def _get_template(self, template_path: str, **context) -> str:
        """
        Renders the template for the email sender

        :param template_path: Path to the template file
        :param context: Context args to be passed to Jinja2

        :return: Rendered HTML
        """
        user_template = self.env.get_template(template_path)
        rendered_template = await user_template.render_async(
            **context
        )
        return rendered_template

    async def send_email(
        self,
        email_context: BaseEmail,
        recipients: list[str],
    ) -> None:
        """
        This gets the email content of a particular type and sends the mail to the ``recipient`` based on the configuration
        for that particular type.

        All the metadata for sending emails is stored implicitly in the type, e.g. - config, email_subject.

        :param email_context: UserEmailBodyType - Contains the metadata and content for email to be sent.
        :param recipients: EmailStr - Email of the recipient.
        :return: None
        """
        try:
            rendered_body = await self._get_template(
                template_path=email_context.template_path,  # Template path for Jinja2 rendering
                **email_context.context_vars,
            )
            await send_email_with_fastmail(
                subject=email_context.subject,
                recipients=recipients,
                body=rendered_body,
                config=email_config,
            )

        except Exception as e:
            logger.error(f"Error occurred while sending email to user: {e}")
            raise HTTPException(status_code=500, detail="An unknown error occurred")


email_sender = EmailSender()

async def send_email_task(email_context: BaseEmail, recipients: list[str]):
    await email_sender.send_email(
        email_context=email_context,
        recipients=recipients,
    )
