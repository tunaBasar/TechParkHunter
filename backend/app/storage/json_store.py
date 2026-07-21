import json
from pathlib import Path
from typing import Optional

from app.storage.models import Company, ScrapedData


class JsonStore:
    def __init__(self, data_dir: str = "data/companies"):
        self.data_dir = Path(data_dir)

    def save_scraped_data(self, data: ScrapedData) -> Path:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        file_path = self.data_dir / f"{data.source}.json"
        file_path.write_text(
            json.dumps(data.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return file_path

    def load_scraped_data(self, source: str) -> Optional[ScrapedData]:
        file_path = self.data_dir / f"{source}.json"
        if not file_path.exists():
            return None
        raw = json.loads(file_path.read_text(encoding="utf-8"))
        return ScrapedData(**raw)

    def list_sources(self) -> list[str]:
        if not self.data_dir.exists():
            return []
        return [p.stem for p in self.data_dir.glob("*.json")]

    def get_all_companies(self) -> list[Company]:
        companies: list[Company] = []
        for source in self.list_sources():
            data = self.load_scraped_data(source)
            if data:
                companies.extend(data.companies)
        return companies

    def update_company(self, source: str, company_id: str, updates: dict) -> bool:
        data = self.load_scraped_data(source)
        if not data:
            return False

        for company in data.companies:
            if company.id == company_id:
                for key, value in updates.items():
                    setattr(company, key, value)
                self.save_scraped_data(data)
                return True

        return False
