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

    new_status = (
        update.application_status.value
        if update.application_status is not None
        else company["application_status"]
    )
    new_notes = update.notes if update.notes is not None else company["notes"]
    await db.update_company_status(company_id, new_status, new_notes)

    json_updates = {}
    if update.application_status is not None:
        json_updates["application_status"] = update.application_status
    if update.notes is not None:
        json_updates["notes"] = update.notes
    if json_updates:
        json_store.update_company(company["source"], company_id, json_updates)

    return {"success": True}
