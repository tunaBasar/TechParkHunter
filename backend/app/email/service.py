"""Gmail SMTP üzerinden e-posta gönderimi.

Google hesabında normal şifre yerine 2FA açıp oluşturulan bir "Uygulama
Şifresi" (App Password) kullanılır. Bu servis LLM/AI çağrısı yapmaz — sadece
önceden hazırlanmış bir konu + gövde metnini SMTP ile gönderir.
"""

import aiosmtplib
from aiosmtplib.errors import (
    SMTPAuthenticationError,
    SMTPConnectError,
    SMTPException,
    SMTPResponseException,
    SMTPTimeoutError,
)
from email.message import EmailMessage

from app.config import Settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

SMTP_HOSTNAME = "smtp.gmail.com"
SMTP_PORT = 587
SEND_TIMEOUT_SECONDS = 30


class EmailServiceError(Exception):
    """Raised when the email service cannot send a message."""


class EmailService:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.GMAIL_ADDRESS and self.settings.GMAIL_APP_PASSWORD)

    async def send_email(self, to: str, subject: str, body: str) -> None:
        if not self.is_configured:
            raise EmailServiceError(
                "Gmail gönderimi yapılandırılmamış. .env dosyasında "
                "GMAIL_ADDRESS ve GMAIL_APP_PASSWORD ayarlarını doldurun."
            )

        message = EmailMessage()
        message["From"] = self.settings.GMAIL_ADDRESS
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        try:
            await aiosmtplib.send(
                message,
                hostname=SMTP_HOSTNAME,
                port=SMTP_PORT,
                start_tls=True,
                username=self.settings.GMAIL_ADDRESS,
                password=self.settings.GMAIL_APP_PASSWORD,
                timeout=SEND_TIMEOUT_SECONDS,
            )
        except SMTPAuthenticationError as exc:
            logger.error(f"Gmail kimlik doğrulama hatası: {exc}")
            raise EmailServiceError(
                "Gmail kimlik doğrulaması başarısız. GMAIL_ADDRESS ve "
                "GMAIL_APP_PASSWORD değerlerini kontrol edin (normal şifre "
                "değil, Uygulama Şifresi olmalı)."
            ) from exc
        except (SMTPConnectError, SMTPTimeoutError) as exc:
            logger.error(f"Gmail SMTP bağlantı hatası: {exc}")
            raise EmailServiceError(
                f"Gmail SMTP sunucusuna bağlanılamadı: {exc}"
            ) from exc
        except SMTPResponseException as exc:
            logger.error(f"Gmail SMTP yanıt hatası: {exc}")
            raise EmailServiceError(f"Gmail e-postayı reddetti: {exc}") from exc
        except SMTPException as exc:
            logger.error(f"Gmail SMTP hatası: {exc}")
            raise EmailServiceError(f"E-posta gönderilemedi: {exc}") from exc
