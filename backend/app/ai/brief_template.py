from pathlib import Path

from app.ai.profile import CandidateProfile
from app.storage.models import Company


def _bullet_list(items: list[str]) -> str:
    if not items:
        return "- (belirtilmemiş)"
    return "\n".join(f"- {item}" for item in items)


def build_application_brief(profile: CandidateProfile, company: Company) -> str:
    """LLM'e değil, insana (siz) ve Claude Cowork'e verilecek bağlamı
    eksiksiz ve düzenli biçimde hazırlayan markdown belgesi üretir."""

    sector = company.sector or "Belirtilmemiş"

    lines: list[str] = [
        f"# Başvuru Brief'i — {company.name}",
        "",
        "## Şirket Bilgisi",
        f"- **Sektör:** {sector}",
        f"- **Web sitesi:** {company.website or 'Belirtilmemiş'}",
        f"- **İletişim:** {company.contact_email or 'Belirtilmemiş'}",
        f"- **Kaynak:** {company.source_name or company.source or 'Belirtilmemiş'}"
        + (f" ({company.detail_url})" if company.detail_url else ""),
        "",
        "### Şirket Açıklaması",
        company.description or "Açıklama bulunmuyor.",
    ]

    if company.full_description:
        lines.append("")
        lines.append(company.full_description)

    lines.extend(
        [
            "",
            "## Aday Profili",
            f"- **İsim:** {profile.name}",
            f"- **Unvan:** {profile.title}",
            f"- **Deneyim:** {profile.experience_years}",
            "",
            "### Temel Yetenekler",
            _bullet_list(profile.core_skills),
            "",
            "### Öne Çıkanlar",
            _bullet_list(profile.highlights),
            "",
            f"- **Eğitim:** {profile.education}",
            f"- **Diller:** {', '.join(profile.languages) if profile.languages else 'Belirtilmemiş'}",
            "",
            "## Talimat (Cowork için)",
            "Yukarıdaki şirket bilgisi ve aday profilini kullanarak:",
            f"1. Bu şirkete özel, {sector.lower()} alanına yönelik teknik referanslar içeren bir "
            "Türkçe iş başvuru e-postası yaz (max 250 kelime, konu satırı dahil).",
            "2. Adayın CV'sini bu şirkete göre uyarlamak için: Profesyonel Özet (3-4 cümle), "
            "Öne Çıkarılacak Yetenekler (5 madde), Proje/Deneyim Vurguları (3 madde), "
            "Teknik Anahtar Kelimeler listesi hazırla.",
        ]
    )

    return "\n".join(lines) + "\n"


def save_brief(company_id: str, brief_markdown: str, data_dir: str = "data") -> Path:
    save_dir = Path(data_dir) / "applications" / company_id
    save_dir.mkdir(parents=True, exist_ok=True)
    file_path = save_dir / "brief.md"
    file_path.write_text(brief_markdown, encoding="utf-8")
    return file_path


def build_email_subject_and_body(
    profile: CandidateProfile, company: Company
) -> tuple[str, str]:
    """Gerçekten gönderilecek bir e-postanın konu satırını ve gövdesini üretir.

    build_application_brief()'ten farklı olarak bu, Cowork için bir "talimat"
    değil, doğrudan alıcıya gidecek düz metin bir e-postadır. LLM çağrısı
    yapmaz — profil ve şirket verisini basit bir şablonla birleştirir."""

    subject = f"{profile.title} Pozisyonu İçin Başvuru — {profile.name}"

    skills_line = ", ".join(profile.core_skills) if profile.core_skills else ""
    highlight_lines = "\n".join(f"- {h}" for h in profile.highlights)

    body_lines = [
        f"Merhaba {company.name} Yetkilisi,",
        "",
        f"Ben {profile.name}, {profile.experience_years} deneyime sahip bir "
        f"{profile.title}. Şirketinizin "
        f"{(company.sector or 'faaliyet').lower()} alanındaki çalışmalarını "
        "ilgiyle takip ediyor ve ekibinize katkı sağlayabileceğimi düşünüyorum.",
        "",
    ]

    if skills_line:
        body_lines.append(f"Temel yetkinliklerim: {skills_line}.")
        body_lines.append("")

    if highlight_lines:
        body_lines.append("Öne çıkan deneyimlerimden bazıları:")
        body_lines.append(highlight_lines)
        body_lines.append("")

    body_lines.extend(
        [
            "Ekte/aşağıda yer alan özgeçmişimi incelemenizi rica eder, "
            "uygun bir pozisyon olması durumunda görüşme fırsatı "
            "bulabilmeyi umarım.",
            "",
            "İlginiz için teşekkür ederim.",
            "",
            f"Saygılarımla,\n{profile.name}",
        ]
    )

    return subject, "\n".join(body_lines)

