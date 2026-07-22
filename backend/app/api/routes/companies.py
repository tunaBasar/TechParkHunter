import csv
import io
import json
from datetime import date
from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.deps import get_db, get_json_store
from app.scraping.contact_finder import find_contact_email
from app.storage.db import DatabaseManager
from app.storage.json_store import JsonStore
from app.storage.models import ApplicationStatus, CompanyFilter

router = APIRouter()

EXPORT_CSV_COLUMNS = [
    "id",
    "name",
    "source",
    "sector",
    "website",
    "contact_email",
    "application_status",
    "notes",
]


class CompanyUpdate(BaseModel):
    application_status: Optional[ApplicationStatus] = None
    notes: Optional[str] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None


@router.get("/")
async def list_companies(
    source: Optional[str] = None,
    sector: Optional[str] = None,
    status: Optional[ApplicationStatus] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
    db: DatabaseManager = Depends(get_db),
):
    filter = CompanyFilter(
        source=source,
        sector=sector,
        status=status,
        search=search,
        page=page,
        per_page=per_page,
    )
    companies, total = await db.get_companies(filter)
    return {
        "companies": companies,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": ceil(total / per_page) if per_page else 0,
    }


@router.get("/stats")
async def get_stats(db: DatabaseManager = Depends(get_db)):
    return await db.get_stats()


@router.get("/export")
async def export_companies(
    format: str = "csv",
    source: Optional[str] = None,
    sector: Optional[str] = None,
    status: Optional[ApplicationStatus] = None,
    search: Optional[str] = None,
    db: DatabaseManager = Depends(get_db),
):
    if format not in ("csv", "json"):
        raise HTTPException(400, "format must be 'csv' or 'json'")

    filter = CompanyFilter(
        source=source,
        sector=sector,
        status=status,
        search=search,
        page=1,
        per_page=1_000_000,
    )
    companies, _total = await db.get_companies(filter)

    filename_date = date.today().isoformat()

    if format == "json":
        payload = json.dumps(companies, ensure_ascii=False, indent=2)
        return StreamingResponse(
            iter([payload]),
            media_type="application/json",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="techpark_companies_{filename_date}.json"'
                )
            },
        )

    def generate_csv():
        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer, fieldnames=EXPORT_CSV_COLUMNS, extrasaction="ignore"
        )
        # UTF-8 BOM so Excel opens the file with correct Turkish characters.
        yield "\ufeff"
        writer.writeheader()
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)

        for company in companies:
            writer.writerow(company)
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

    return StreamingResponse(
        generate_csv(),
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f'attachment; filename="techpark_companies_{filename_date}.csv"'
            )
        },
    )


@router.get("/{company_id}")
async def get_company(company_id: str, db: DatabaseManager = Depends(get_db)):
    company = await db.get_company(company_id)
    if not company:
        raise HTTPException(404, "Company not found")
    return company


@router.patch("/{company_id}")
async def update_company(
    company_id: str,
    update: CompanyUpdate,
    db: DatabaseManager = Depends(get_db),
    json_store: JsonStore = Depends(get_json_store),
):
    company = await db.get_company(company_id)
    if not company:
        raise HTTPException(404, "Company not found")

    db_fields: dict = {}
    json_updates: dict = {}

    if update.application_status is not None:
        db_fields["application_status"] = update.application_status.value
        json_updates["application_status"] = update.application_status
    if update.notes is not None:
        db_fields["notes"] = update.notes
        json_updates["notes"] = update.notes
    if update.website is not None:
        db_fields["website"] = update.website
        json_updates["website"] = update.website
    if update.contact_email is not None:
        db_fields["contact_email"] = update.contact_email
        json_updates["contact_email"] = update.contact_email

    if db_fields:
        await db.update_fields(company_id, db_fields)
    if json_updates and company.get("source"):
        json_store.update_company(company["source"], company_id, json_updates)

    return {"success": True}


@router.delete("/{company_id}")
async def delete_company(
    company_id: str,
    db: DatabaseManager = Depends(get_db),
    json_store: JsonStore = Depends(get_json_store),
):
    company = await db.get_company(company_id)
    if not company:
        raise HTTPException(404, "Company not found")

    await db.delete_company(company_id)
    if company.get("source"):
        json_store.delete_company(company["source"], company_id)

    return {"success": True}


@router.post("/{company_id}/find-contact-email")
async def find_company_contact_email(
    company_id: str,
    db: DatabaseManager = Depends(get_db),
    json_store: JsonStore = Depends(get_json_store),
):
    """Şirketin DB kaydında zaten contact_email varsa onu döner. Yoksa ve
    website alanı mevcutsa, siteyi ziyaret edip mailto: linki bulmaya çalışır.
    Ne website ne de bulunabilir bir mail varsa found=False döner — hiçbir
    zaman uydurma bir adres üretilmez."""

    company = await db.get_company(company_id)
    if not company:
        raise HTTPException(404, "Company not found")

    if company.get("contact_email"):
        return {
            "found": True,
            "contact_email": company["contact_email"],
            "source": "existing",
        }

    website = company.get("website")
    if not website:
        return {
            "found": False,
            "contact_email": None,
            "source": None,
            "reason": "Şirketin kayıtlı bir web sitesi yok.",
        }

    email = await find_contact_email(website)
    if not email:
        return {
            "found": False,
            "contact_email": None,
            "source": None,
            "reason": "Web sitesinde e-posta adresi bulunamadı.",
        }

    await db.update_contact_email(company_id, email)
    if company.get("source"):
        json_store.update_company(
            company["source"], company_id, {"contact_email": email}
        )

    return {"found": True, "contact_email": email, "source": "website"}
