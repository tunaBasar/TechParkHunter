import re
from typing import Optional

from app.scraping.config_models import FieldSelector
from app.storage.models import Company
from app.utils.logger import get_logger

logger = get_logger(__name__)

TURKISH_CHAR_MAP = str.maketrans(
    {
        "ç": "c", "Ç": "c",
        "ğ": "g", "Ğ": "g",
        "ı": "i", "I": "i", "İ": "i",
        "ö": "o", "Ö": "o",
        "ş": "s", "Ş": "s",
        "ü": "u", "Ü": "u",
    }
)

# YAML field names that don't map 1:1 onto Company model field names.
FIELD_ALIASES = {"logo": "logo_url"}


def slugify(text: str) -> str:
    text = text.translate(TURKISH_CHAR_MAP).lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


async def _extract_field(source, field_selector: FieldSelector) -> Optional[str]:
    try:
        target = await source.query_selector(field_selector.selector)
        if target is None:
            return None

        if field_selector.type == "text":
            text = await target.inner_text()
            return text.strip() if text else None
        if field_selector.type == "attribute":
            return await target.get_attribute(field_selector.attribute)
        if field_selector.type == "html":
            return await target.inner_html()
    except Exception as exc:
        logger.debug(f"Field extraction failed for selector '{field_selector.selector}': {exc}")
        return None

    return None


async def extract_fields(source, fields: dict[str, FieldSelector]) -> dict[str, Optional[str]]:
    values: dict[str, Optional[str]] = {}
    for field_name, field_selector in fields.items():
        values[field_name] = await _extract_field(source, field_selector)
    return values


async def parse_company(element, fields: dict[str, FieldSelector], source_slug: str) -> Company:
    values = await extract_fields(element, fields)

    name = values.get("name") or ""
    company_id = f"{source_slug}_{slugify(name)}"

    company_model_fields = set(Company.model_fields)
    kwargs = {"id": company_id, "name": name}
    for field_name, value in values.items():
        if field_name == "name" or value is None:
            continue
        model_field = FIELD_ALIASES.get(field_name, field_name)
        if model_field in company_model_fields:
            kwargs[model_field] = value

    return Company(**kwargs)


def tag_sectors(company: Company, keywords: dict[str, list[str]]) -> Company:
    haystack = " ".join(
        filter(None, [company.sector, company.description, company.full_description])
    ).lower()

    matched = [
        tag
        for tag, kws in keywords.items()
        if any(kw.lower() in haystack for kw in kws)
    ]
    if not matched:
        return company.model_copy()

    merged_tags = list(dict.fromkeys([*company.sector_tags, *matched]))
    return company.model_copy(update={"sector_tags": merged_tags})
