import asyncio
import random
import time
from datetime import datetime, timezone
from typing import Callable, Optional
from urllib.parse import urljoin

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright
from pydantic import BaseModel

from app.scraping.config_models import NavigationType, SiteConfig
from app.scraping.parser import extract_fields, parse_company, slugify, tag_sectors
from app.scraping.relevance import is_relevant_company
from app.storage.models import Company, ScrapedData
from app.utils.logger import get_logger

logger = get_logger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

STEALTH_SCRIPT = "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"

MAX_GOTO_RETRIES = 3
GOTO_TIMEOUT_MS = 30000
ELEMENT_WAIT_TIMEOUT_MS = 10000
RETRY_BACKOFF_SECONDS = (1, 2, 4)
PAGE_DELAY_RANGE = (1.0, 2.5)


class ScrapingResult(BaseModel):
    """Summary report of a completed (or failed) scraping run."""

    status: str  # "completed" | "completed_with_errors" | "failed"
    total_found: int
    errors: list[dict]  # [{"page": 5, "error": "Timeout"}, ...]
    duration_seconds: float


class ScrapingEngine:
    async def scrape_site(
        self, config: SiteConfig, on_progress: Optional[Callable] = None
    ) -> tuple[ScrapedData, ScrapingResult]:
        started_at = time.monotonic()
        companies: list[Company] = []
        errors: list[dict] = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                context = await browser.new_context(
                    user_agent=USER_AGENT,
                    viewport={"width": 1920, "height": 1080},
                    locale="tr-TR",
                )
                await context.add_init_script(STEALTH_SCRIPT)
                page = await context.new_page()

                ok = await self._goto_with_retry(
                    page, config.site.company_list_url, errors, page_label="list"
                )
                if not ok:
                    # Cannot even load the first listing page: total failure.
                    duration = time.monotonic() - started_at
                    data = ScrapedData(
                        source=config.site.slug,
                        source_name=config.site.name,
                        scraped_at=datetime.now(timezone.utc),
                        total_companies=0,
                        companies=[],
                    )
                    result = ScrapingResult(
                        status="failed",
                        total_found=0,
                        errors=errors,
                        duration_seconds=duration,
                    )
                    return data, result

                await self._wait_for_container(page, config.selectors.company_container, errors, "list")

                companies = await self._collect_companies(page, config, on_progress, errors)

                if config.filters:
                    companies = [
                        tag_sectors(c, config.filters.sector_keywords) for c in companies
                    ]

                if config.selectors.detail_page:
                    companies = await self._enrich_with_detail_pages(
                        context, companies, config, errors
                    )
                    if config.filters:
                        # Bazı sitelerde sektör bilgisi de sadece detay
                        # sayfasında geliyor; enrichment sonrası tekrar etiketle.
                        companies = [
                            tag_sectors(c, config.filters.sector_keywords)
                            for c in companies
                        ]
                    # Bazı sitelerde isim/sektör bilgisi sadece detay
                    # sayfasında ortaya çıkıyor (örn. Kocaeli Teknopark); bu
                    # durumda alaka filtresi ilk geçişte etkisiz kalmış olur,
                    # o yüzden enrichment sonrası tekrar uygulanıyor.
                    companies = [
                        c
                        for c in companies
                        if is_relevant_company(
                            c.name, c.sector, c.description, c.full_description
                        )
                    ]

                # Bazı kartlarda (örn. henüz yayında olmayan bir firma sayfası)
                # isim hiç çekilemez; bu tür kayıtları DB'ye kaydetmeden ele.
                companies = [c for c in companies if c.name and c.name.strip()]
            except Exception as exc:
                logger.error(f"Scraping error for {config.site.slug}: {exc}")
                errors.append({"page": "unknown", "error": str(exc)})
            finally:
                await browser.close()

        duration = time.monotonic() - started_at

        if not companies and errors:
            status = "failed"
        elif errors:
            status = "completed_with_errors"
        else:
            status = "completed"

        data = ScrapedData(
            source=config.site.slug,
            source_name=config.site.name,
            scraped_at=datetime.now(timezone.utc),
            total_companies=len(companies),
            companies=companies,
        )
        result = ScrapingResult(
            status=status,
            total_found=len(companies),
            errors=errors,
            duration_seconds=duration,
        )
        return data, result

    async def _goto_with_retry(
        self, page, url: str, errors: list[dict], page_label
    ) -> bool:
        last_error: Optional[str] = None
        for attempt, delay in enumerate((*RETRY_BACKOFF_SECONDS, None), start=1):
            try:
                await page.goto(url, wait_until="networkidle", timeout=GOTO_TIMEOUT_MS)
                return True
            except PlaywrightTimeoutError as exc:
                last_error = f"Timeout: {exc}"
                logger.warning(
                    f"Timeout loading {url}, attempt {attempt}/{MAX_GOTO_RETRIES}"
                )
            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    f"Error loading {url}, attempt {attempt}/{MAX_GOTO_RETRIES}: {exc}"
                )

            if attempt >= MAX_GOTO_RETRIES:
                break
            await asyncio.sleep(delay)

        errors.append({"page": page_label, "error": last_error or "Unknown navigation error"})
        return False

    async def _wait_for_container(self, page, selector: str, errors: list[dict], page_label) -> bool:
        try:
            await page.wait_for_selector(selector, timeout=ELEMENT_WAIT_TIMEOUT_MS)
            return True
        except PlaywrightTimeoutError:
            logger.warning(f"Container selector '{selector}' not found within timeout")
            errors.append(
                {"page": page_label, "error": f"Element not found: {selector}"}
            )
            return False

    async def _parse_element(
        self, element, config: SiteConfig, errors: list[dict], page_label
    ) -> Optional[Company]:
        try:
            company = await parse_company(
                element, config.selectors.fields, config.site.slug
            )
        except Exception as exc:
            logger.warning(f"Failed to parse company element: {exc}")
            errors.append({"page": page_label, "error": f"Parse error: {exc}"})
            return None

        if not is_relevant_company(
            company.name, company.sector, company.description, company.full_description
        ):
            # Yazılım/teknoloji/finans alanıyla ilgisi olmayan şirket: detay
            # sayfası dahi çekilmeden tamamen elenir.
            return None

        detail_page_config = config.selectors.detail_page
        if detail_page_config:
            try:
                link_el = await element.query_selector(detail_page_config.link_selector)
                if link_el:
                    href = await link_el.get_attribute("href")
                    if href:
                        company = company.model_copy(
                            update={"detail_url": urljoin(config.site.base_url, href)}
                        )
            except Exception as exc:
                logger.debug(f"Detail link extraction failed: {exc}")

        return company

    async def _collect_companies(
        self,
        page,
        config: SiteConfig,
        on_progress: Optional[Callable],
        errors: list[dict],
    ) -> list[Company]:
        nav = config.navigation
        selectors = config.selectors
        companies: list[Company] = []

        async def parse_all_current_elements(page_label) -> list[Company]:
            elements = await page.query_selector_all(selectors.company_container)
            parsed = []
            for element in elements:
                company = await self._parse_element(element, config, errors, page_label)
                if company:
                    parsed.append(company)
            return parsed

        if nav.type == NavigationType.PAGINATION:
            for page_num in range(1, nav.max_pages + 1):
                companies.extend(await parse_all_current_elements(page_num))
                if on_progress:
                    on_progress(len(companies))

                if not nav.next_button:
                    break
                next_btn = await page.query_selector(nav.next_button)
                if not next_btn:
                    break

                await asyncio.sleep(random.uniform(*PAGE_DELAY_RANGE))

                try:
                    await next_btn.click()
                    await page.wait_for_load_state("networkidle", timeout=GOTO_TIMEOUT_MS)
                    await self._wait_for_container(
                        page, selectors.company_container, errors, page_num + 1
                    )
                except Exception as exc:
                    logger.warning(f"Pagination stopped at page {page_num}: {exc}")
                    errors.append(
                        {"page": page_num + 1, "error": f"Pagination failed: {exc}"}
                    )
                    break

        elif nav.type == NavigationType.INFINITE_SCROLL:
            seen_count = 0
            stagnant_rounds = 0
            for _ in range(nav.max_pages):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(nav.scroll_pause_ms / 1000)
                current = await page.query_selector_all(selectors.company_container)
                if len(current) <= seen_count:
                    stagnant_rounds += 1
                    if stagnant_rounds >= 2:
                        break
                else:
                    stagnant_rounds = 0
                seen_count = len(current)
                await asyncio.sleep(random.uniform(*PAGE_DELAY_RANGE))

            companies = await parse_all_current_elements("scroll")
            if on_progress:
                on_progress(len(companies))

        elif nav.type == NavigationType.LOAD_MORE:
            seen_count = 0
            for _ in range(nav.max_pages):
                if not nav.load_more_button:
                    break
                load_more_btn = await page.query_selector(nav.load_more_button)
                if not load_more_btn:
                    break
                try:
                    await load_more_btn.click()
                    await asyncio.sleep(nav.scroll_pause_ms / 1000)
                except Exception as exc:
                    logger.warning(f"Load more stopped: {exc}")
                    errors.append({"page": "load_more", "error": str(exc)})
                    break
                current = await page.query_selector_all(selectors.company_container)
                if len(current) <= seen_count:
                    break
                seen_count = len(current)
                await asyncio.sleep(random.uniform(*PAGE_DELAY_RANGE))

            companies = await parse_all_current_elements("load_more")
            if on_progress:
                on_progress(len(companies))

        return companies

    async def _enrich_with_detail_pages(
        self,
        context,
        companies: list[Company],
        config: SiteConfig,
        errors: list[dict],
    ) -> list[Company]:
        detail_fields = config.selectors.detail_page.fields
        company_model_fields = set(Company.model_fields)
        enriched: list[Company] = []

        detail_page = await context.new_page()
        try:
            for company in companies:
                if not company.detail_url:
                    enriched.append(company)
                    continue
                try:
                    ok = await self._goto_with_retry(
                        detail_page, company.detail_url, errors, page_label=company.id
                    )
                    if not ok:
                        enriched.append(company)
                        continue

                    extra = await extract_fields(detail_page, detail_fields)
                    updates = {
                        key: value
                        for key, value in extra.items()
                        if value is not None and key in company_model_fields
                    }
                    if updates:
                        # Bazı sitelerde (örn. Kocaeli Teknopark) liste kartında
                        # şirket ismi hiç yok, sadece detay sayfasında mevcut.
                        # Bu durumda tüm şirketler aynı boş isimden üretilen
                        # company_id'yi paylaşıp DB'de birbirinin üzerine
                        # yazardı; isim ilk kez detay sayfasından geliyorsa
                        # id'yi yeniden üretiyoruz.
                        new_name = updates.get("name")
                        if new_name and not company.name:
                            updates["id"] = f"{config.site.slug}_{slugify(new_name)}"
                        enriched.append(company.model_copy(update=updates))
                    else:
                        enriched.append(company)
                except Exception as exc:
                    logger.warning(
                        f"Detail page fetch failed for {company.detail_url}: {exc}"
                    )
                    errors.append({"page": company.id, "error": str(exc)})
                    enriched.append(company)

                await asyncio.sleep(random.uniform(*PAGE_DELAY_RANGE))
        finally:
            await detail_page.close()

        return enriched
