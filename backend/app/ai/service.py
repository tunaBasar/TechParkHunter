from datetime import datetime, timezone
from pathlib import Path

from app.ai.brief_template import build_application_brief, save_brief
from app.ai.profile import load_profile
from app.storage.models import Company
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BriefServiceError(Exception):
    """Raised when the brief service fails to generate or save a brief."""


class BriefService:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.profile = load_profile()

    def generate_brief(self, company: Company) -> dict:
        markdown = build_application_brief(self.profile, company)
        try:
            path = save_brief(company.id, markdown, data_dir=self.data_dir)
        except OSError as exc:
            logger.error(f"Brief dosyası kaydedilemedi: {exc}")
            raise BriefServiceError(f"Brief dosyası kaydedilemedi: {exc}") from exc

        return {
            "brief_markdown": markdown,
            "saved_to": str(path),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def load_brief(self, company_id: str) -> str | None:
        path = Path(self.data_dir) / "applications" / company_id / "brief.md"
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")
