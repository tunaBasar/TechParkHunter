import asyncio
from datetime import datetime, timezone
from pathlib import Path

import litellm

from app.ai.profile import load_profile
from app.ai.prompts import format_cv_prompt, format_email_prompt
from app.config import Settings
from app.storage.models import Company
from app.utils.logger import get_logger

logger = get_logger(__name__)

REQUEST_TIMEOUT_SECONDS = 60


class AIServiceError(Exception):
    """Raised when the AI service fails to generate content."""


class AIService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = self._resolve_model(settings)
        self.profile = load_profile()

    def _resolve_model(self, settings: Settings) -> str:
        if settings.LLM_PROVIDER == "ollama":
            return f"ollama/{settings.LLM_MODEL}"
        elif settings.LLM_PROVIDER == "openai":
            return settings.LLM_MODEL
        elif settings.LLM_PROVIDER == "anthropic":
            return settings.LLM_MODEL
        return settings.LLM_MODEL

    async def _complete(self, prompt: str, temperature: float, max_tokens: int) -> str:
        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            return response.choices[0].message.content
        except litellm.exceptions.APIConnectionError as exc:
            logger.error(f"LLM bağlantı hatası: {exc}")
            if self.settings.LLM_PROVIDER == "ollama":
                raise AIServiceError(
                    "Ollama servisi bulunamadı. 'ollama serve' ile başlatın "
                    "veya .env'de cloud provider ayarlayın."
                ) from exc
            raise AIServiceError(f"LLM servisine bağlanılamadı: {exc}") from exc
        except litellm.exceptions.Timeout as exc:
            logger.error(f"LLM zaman aşımı: {exc}")
            raise AIServiceError(
                f"LLM isteği {REQUEST_TIMEOUT_SECONDS} saniye içinde yanıt vermedi."
            ) from exc
        except litellm.exceptions.AuthenticationError as exc:
            logger.error(f"LLM kimlik doğrulama hatası: {exc}")
            raise AIServiceError(
                "LLM sağlayıcısı için API anahtarı geçersiz veya eksik."
            ) from exc
        except litellm.exceptions.APIError as exc:
            logger.error(f"LLM hatası: {exc}")
            raise AIServiceError(f"LLM isteği başarısız oldu: {exc}") from exc
        except Exception as exc:
            logger.error(f"Beklenmeyen LLM hatası: {exc}")
            raise AIServiceError(f"LLM isteği başarısız oldu: {exc}") from exc

    async def generate_email(self, company: Company) -> str:
        prompt = format_email_prompt(self.profile, company)
        return await self._complete(prompt, temperature=0.7, max_tokens=1500)

    async def generate_cv_content(self, company: Company) -> str:
        prompt = format_cv_prompt(self.profile, company)
        return await self._complete(prompt, temperature=0.5, max_tokens=2000)

    async def generate_application(self, company: Company) -> dict:
        email_draft, cv_content = await asyncio.gather(
            self.generate_email(company), self.generate_cv_content(company)
        )

        save_dir = Path(self.settings.DATA_DIR) / "applications" / company.id
        save_dir.mkdir(parents=True, exist_ok=True)

        (save_dir / "email_draft.md").write_text(email_draft, encoding="utf-8")
        (save_dir / "cv_content.md").write_text(cv_content, encoding="utf-8")

        return {
            "email_draft": email_draft,
            "cv_content": cv_content,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "saved_to": str(save_dir),
        }
