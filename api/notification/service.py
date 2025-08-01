from typing import Any, Dict
from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from jinja2 import Environment, FileSystemLoader
from ..config.settings import settings


# Jinja2 environment setup to load templates
env = Environment(loader=FileSystemLoader("api/notification/template"))

# Connection configuration for fastapi-mail
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_TLS=settings.MAIL_TLS,
    MAIL_SSL=settings.MAIL_SSL,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
)
fast_mail = FastMail(conf)


class NotificationService:
    async def send_email(
        self,
        recipients: list[str],
        subject: str,
        template_name: str,
        template_body: Dict[str, Any],
        background_tasks: BackgroundTasks,
    ):
        """
        Generic method to send an email using a Jinja2 template.
        """
        # Render the HTML template with the provided body data
        template = env.get_template(template_name)
        html_body = template.render(**template_body)

        # Create the email message schema
        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            body=html_body,
            subtype="html",
        )

        # Add the email sending task to the background tasks
        background_tasks.add_task(fast_mail.send_message, message)

    async def send_reset_password_email(
        self,
        email: str,
        token: str,
        background_tasks: BackgroundTasks,
    ):
        """
        Sends a reset password email to the user.
        """
        pass
