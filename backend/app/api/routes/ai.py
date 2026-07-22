from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.ai.brief_template import build_email_subject_and_body
from app.ai.profile import load_profile
from app.ai.service import BriefService, BriefServiceError
from app.api.deps import get_brief_service, get_db, get_email_service
from app.email.service import EmailService, EmailServiceError
from app.storage.db import DatabaseManager
from app.storage.models import Company

router = APIRouter()


class CompanyIdRequest(BaseModel):
    company_id: str


class SendEmailRequest(BaseModel):
    company_id: str
    # İkisi de opsiyonel: boş bırakılırsa build_email_subject_and_body() ile
    # üretilen sabit şablon kullanılır (geriye dönük uyumlu). Cowork gibi bir
    # LLM aracı kişiye özel bir konu/gövde ürettiyse, burada gönderip sabit
    # şablonun yerine geçirebilir.
    subject: Optional[str] = None
    body: Optional[str] = None


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


@router.post("/send-email")
async def send_email(
    request: SendEmailRequest,
    db: DatabaseManager = Depends(get_db),
    email_service: EmailService = Depends(get_email_service),
):
    company = await _load_company(request.company_id, db)

    if not company.contact_email:
        raise HTTPException(
            400,
            "Bu şirketin kayıtlı bir iletişim e-postası yok. "
            "Önce 'İletişim E-postası Bul' özelliğini deneyin.",
        )

    if not email_service.is_configured:
        raise HTTPException(
            400,
            "Gmail gönderimi yapılandırılmamış. .env dosyasında GMAIL_ADDRESS "
            "ve GMAIL_APP_PASSWORD ayarlarını doldurun.",
        )

    # subject/body verilmişse (örn. Cowork'ün ürettiği kişiye özel metin)
    # onu kullan; verilmemişse sabit şablona düş.
    if request.subject is not None or request.body is not None:
        if not request.subject or not request.body:
            raise HTTPException(
                400,
                "Özel bir e-posta göndermek için hem 'subject' hem 'body' "
                "birlikte verilmelidir.",
            )
        subject, body = request.subject, request.body
        used_custom_content = True
    else:
        profile = load_profile()
        subject, body = build_email_subject_and_body(profile, company)
        used_custom_content = False

    try:
        await email_service.send_email(company.contact_email, subject, body)
    except EmailServiceError as exc:
        raise HTTPException(502, str(exc)) from exc

    return {
        "success": True,
        "sent_to": company.contact_email,
        "used_custom_content": used_custom_content,
    }
