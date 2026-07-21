from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.ai.profile import load_profile
from app.ai.service import AIService, AIServiceError
from app.api.deps import get_ai_service, get_db
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


@router.post("/generate-email")
async def generate_email(
    request: CompanyIdRequest,
    db: DatabaseManager = Depends(get_db),
    ai_service: AIService = Depends(get_ai_service),
):
    company = await _load_company(request.company_id, db)
    try:
        email_draft = await ai_service.generate_email(company)
    except AIServiceError as exc:
        raise HTTPException(502, str(exc)) from exc
    return {"email_draft": email_draft, "company_name": company.name}


@router.post("/generate-cv")
async def generate_cv(
    request: CompanyIdRequest,
    db: DatabaseManager = Depends(get_db),
    ai_service: AIService = Depends(get_ai_service),
):
    company = await _load_company(request.company_id, db)
    try:
        cv_content = await ai_service.generate_cv_content(company)
    except AIServiceError as exc:
        raise HTTPException(502, str(exc)) from exc
    return {"cv_content": cv_content, "company_name": company.name}


@router.post("/generate-application")
async def generate_application(
    request: CompanyIdRequest,
    db: DatabaseManager = Depends(get_db),
    ai_service: AIService = Depends(get_ai_service),
):
    company = await _load_company(request.company_id, db)
    try:
        result = await ai_service.generate_application(company)
    except AIServiceError as exc:
        raise HTTPException(502, str(exc)) from exc
    return result


@router.get("/profile")
async def get_profile():
    return load_profile()
