from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ApplicationStatus(str, Enum):
    NOT_APPLIED = "not_applied"
    APPLIED = "applied"
    INTERVIEW = "interview"
    REJECTED = "rejected"
    ACCEPTED = "accepted"


class Company(BaseModel):
    id: str
    name: str
    sector: Optional[str] = None
    sector_tags: list[str] = []
    description: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    contact_email: Optional[str] = None
    detail_url: Optional[str] = None
    full_description: Optional[str] = None
    application_status: ApplicationStatus = ApplicationStatus.NOT_APPLIED
    notes: str = ""


class ScrapedData(BaseModel):
    source: str
    source_name: str
    scraped_at: datetime
    total_companies: int
    companies: list[Company]


class CompanyFilter(BaseModel):
    source: Optional[str] = None
    sector: Optional[str] = None
    status: Optional[ApplicationStatus] = None
    search: Optional[str] = None
    page: int = 1
    per_page: int = 20
