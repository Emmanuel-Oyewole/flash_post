from typing import Any, Dict
from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from jinja2 import Environment, FileSystemLoader
from ..config.settings import settings


# Jinja2 environment setup to load templates
env = Environment(loader=FileSystemLoader("notification/template"))

# Connection configuration for fastapi-mail
conf = ConnectionConfig(
    MAIL_USERNAME=settings.brevo_smtp_username,
    MAIL_PASSWORD=settings.brevo_smtp_password,
    MAIL_FROM=settings.brevo_sender,
    MAIL_PORT=settings.brevo_smtp_port,
    MAIL_SERVER=settings.brevo_smtp_host,
    MAIL_FROM_NAME=settings.brevo_sender,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
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
        otp_code: str,
        background_tasks: BackgroundTasks,
    ):
        """
        Sends a reset password email to the user.
        """
        subject = "Reset Your Password"
        template_name = "reset_password.html"
        template_body = {
            "otp_code": otp_code,
            "otp_expires_in": settings.otp_expires_seconds,
        }

        await self.send_email(
            recipients=[email],
            subject=subject,
            template_name=template_name,
            template_body=template_body,
            background_tasks=background_tasks,
        )
        return True

    async def send_reset_password_confirmation(self, email: str, background_tasks: BackgroundTasks) -> None:
        """
        Sends a reset password confirmation email to the user.
        """
        subject = "Your Password Has Been Reset"
        template_name = "reset_password_confirmation.html"
        template_body = {
            "email": email,
        }

        await self.send_email(
            recipients=[email],
            subject=subject,
            template_name=template_name,
            template_body=template_body,
            background_tasks=background_tasks,
        )
        