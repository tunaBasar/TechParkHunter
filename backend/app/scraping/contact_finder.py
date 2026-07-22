"""Web sitesi üzerinden şirket iletişim e-postası bulma.

Bir şirketin DB kaydında `contact_email` yoksa ama `website` alanı varsa, bu
modül şirketin web sitesini (ana sayfa + yaygın iletişim sayfası yolları)
Playwright ile ziyaret edip `mailto:` linklerinden gerçek bir e-posta adresi
çıkarmaya çalışır. Sonuç bulunamazsa None döner — hiçbir tahminde bulunulmaz.
"""

import re
from typing import Optional
from urllib.parse import urljoin, urlparse

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from app.utils.logger import get_logger

logger = get_logger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

PAGE_TIMEOUT_MS = 15000

# Yaygın iletişim sayfası yolları (TR + EN). Ana sayfada mailto: bulunamazsa
# sırayla bu yollar denenir.
CONTACT_PAGE_PATHS = [
    "/iletisim",
    "/iletisim.html",
    "/iletisime-gecin",
    "/bize-ulasin",
    "/contact",
    "/contact-us",
    "/contact.html",
    "/hakkimizda",
    "/about",
    "/about-us",
]

# Bazı sitelerde şablon/placeholder mail adresleri (örnek@ornek.com gibi)
# ya da webmaster/noreply gibi işe yaramaz adresler geçebilir; bunları ele.
IGNORED_LOCAL_PARTS = {"noreply", "no-reply", "webmaster", "postmaster", "example"}

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


def _is_plausible_email(email: str) -> bool:
    local_part = email.split("@", 1)[0].lower()
    if local_part in IGNORED_LOCAL_PARTS:
        return False
    if "example.com" in email.lower() or "domain.com" in email.lower():
        return False
    return True


async def _extract_mailto_from_page(page) -> Optional[str]:
    try:
        hrefs = await page.eval_on_selector_all(
            "a[href^='mailto:']", "els => els.map(el => el.getAttribute('href'))"
        )
    except Exception as exc:
        logger.debug(f"mailto extraction failed: {exc}")
        return None

    for href in hrefs:
        if not href:
            continue
        # "mailto:info@x.com?subject=..." gibi ekstra parametreleri temizle.
        candidate = href.replace("mailto:", "").split("?")[0].strip()
        match = EMAIL_REGEX.search(candidate)
        if match and _is_plausible_email(match.group(0)):
            return match.group(0)

    # mailto linki yoksa, sayfa metninde geçen bir e-posta adresine bak
    # (bazı siteler mailto: kullanmadan düz metin olarak yazıyor).
    try:
        body_text = await page.inner_text("body")
    except Exception:
        return None

    for match in EMAIL_REGEX.finditer(body_text or ""):
        candidate = match.group(0)
        if _is_plausible_email(candidate):
            return candidate

    return None


async def find_contact_email(website_url: str) -> Optional[str]:
    """Verilen web sitesinde ana sayfa ve yaygın iletişim sayfalarını gezip
    bir e-posta adresi bulmaya çalışır. Bulamazsa None döner."""

    if not website_url:
        return None

    parsed = urlparse(website_url)
    if not parsed.scheme:
        website_url = f"https://{website_url}"
        parsed = urlparse(website_url)

    base = f"{parsed.scheme}://{parsed.netloc}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(user_agent=USER_AGENT)
            page = await context.new_page()

            # 1) Ana sayfa
            try:
                await page.goto(website_url, wait_until="networkidle", timeout=PAGE_TIMEOUT_MS)
                found = await _extract_mailto_from_page(page)
                if found:
                    return found
            except PlaywrightTimeoutError:
                logger.debug(f"Timeout loading homepage: {website_url}")
            except Exception as exc:
                logger.debug(f"Failed to load homepage {website_url}: {exc}")

            # 2) Yaygın iletişim sayfası yolları
            for path in CONTACT_PAGE_PATHS:
                candidate_url = urljoin(base, path)
                try:
                    await page.goto(
                        candidate_url, wait_until="networkidle", timeout=PAGE_TIMEOUT_MS
                    )
                    found = await _extract_mailto_from_page(page)
                    if found:
                        return found
                except PlaywrightTimeoutError:
                    continue
                except Exception:
                    continue

            return None
        finally:
            await browser.close()
