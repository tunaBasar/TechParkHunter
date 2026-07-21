from app.ai.profile import CandidateProfile
from app.storage.models import Company

EMAIL_PROMPT = """Sen deneyimli bir kariyer danışmanısın. Aşağıdaki aday profiline sahip bir kişi için,
belirtilen şirkete gönderilecek dikkat çekici, profesyonel bir Türkçe iş başvuru e-postası yaz.

## Aday Profili
- İsim: {candidate_name}
- Unvan: {candidate_title}
- Yetenekler: {candidate_skills}
- Öne Çıkan Deneyimler: {candidate_highlights}

## Hedef Şirket
- İsim: {company_name}
- Sektör: {company_sector}
- Açıklama: {company_description}

## Kurallar
- E-postayı konu satırı (Subject) dahil olacak şekilde yaz.
- Gövde metni en fazla 250 kelime olsun.
- Profesyonel ama samimi bir ton kullan.
- Şirketin faaliyet alanına özel, adayın yetenekleriyle bağlantı kuran teknik referanslar ekle.
- Çıktıyı Markdown formatında ver.
"""

CV_PROMPT = """Sen bir CV danışmanısın. Aşağıdaki aday profilini, belirtilen hedef şirkete göre özelleştirerek
CV içeriği önerileri hazırla.

## Aday Profili
- İsim: {candidate_name}
- Unvan: {candidate_title}
- Yetenekler: {candidate_skills}
- Öne Çıkan Deneyimler: {candidate_highlights}

## Hedef Şirket
- İsim: {company_name}
- Sektör: {company_sector}
- Açıklama: {company_description}

## Çıktı Formatı (Markdown)
1. **Profesyonel Özet** (3-4 cümle)
2. **Öne Çıkarılacak Yetenekler** (5 madde)
3. **Proje/Deneyim Vurguları** (3 madde)
4. **Teknik Anahtar Kelimeler**
"""


def _format_company_description(company: Company) -> str:
    return company.full_description or company.description or "Bilgi mevcut değil"


def format_email_prompt(profile: CandidateProfile, company: Company) -> str:
    return EMAIL_PROMPT.format(
        candidate_name=profile.name,
        candidate_title=profile.title,
        candidate_skills=", ".join(profile.core_skills),
        candidate_highlights=", ".join(profile.highlights),
        company_name=company.name,
        company_sector=company.sector or "Belirtilmemiş",
        company_description=_format_company_description(company),
    )


def format_cv_prompt(profile: CandidateProfile, company: Company) -> str:
    return CV_PROMPT.format(
        candidate_name=profile.name,
        candidate_title=profile.title,
        candidate_skills=", ".join(profile.core_skills),
        candidate_highlights=", ".join(profile.highlights),
        company_name=company.name,
        company_sector=company.sector or "Belirtilmemiş",
        company_description=_format_company_description(company),
    )
