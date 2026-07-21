from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.ai.profile import load_profile
from app.ai.service import BriefService, BriefServiceError
from app.api.deps import get_brief_service, get_db
from app.storage.db import DatabaseManager
from app.storage.models import Company

router = APIRouter()


class CompanyIdRequest(BaseModel):
    company_id: str


async def _load_company(company_id: str, db: DatabaseManager) -> Company:
    company_data = await db.get_company(company_id)
    if not company_data:
        raise HTTPException(404, "Company not found")
    return Company(**company_data)


@router.get("/")
async def ai_root():
    return {"message": "AI endpoint"}


@router.post("/generate-brief")
async def generate_brief(
    request: CompanyIdRequest,
    db: DatabaseManager = Depends(get_db),
    brief_service: BriefService = Depends(get_brief_service),
):
    company = await _load_company(request.company_id, db)
    try:
        result = brief_service.generate_brief(company)
    except BriefServiceError as exc:
        raise HTTPException(500, str(exc)) from exc
    return result


@router.get("/profile")
async def get_profile():
    return load_profile()


@router.get("/brief/{company_id}")
async def get_brief(
    company_id: str,
    brief_service: BriefService = Depends(get_brief_service),
):
    brief_markdown = brief_service.load_brief(company_id)
    if brief_markdown is None:
        raise HTTPException(404, "Brief not found")
    return {"brief_markdown": brief_markdown}
