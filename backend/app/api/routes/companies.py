from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_db, get_json_store
from app.storage.db import DatabaseManager
from app.storage.json_store import JsonStore
from app.storage.models import ApplicationStatus, CompanyFilter

router = APIRouter()


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
