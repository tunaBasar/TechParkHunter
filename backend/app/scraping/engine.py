import asyncio
import random
from datetime import datetime, timezone
from typing import Callable, Optional
from urllib.parse import urljoin

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from app.scraping.config_models import NavigationType, SiteConfig
from app.scraping.parser import extract_fields, parse_company, tag_sectors
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


class ScrapingEngine:
    async def scrape_site(
        self, config: SiteConfig, on_progress: Optional[Callable] = None
    ) -> ScrapedData:
        companies: list[Company] = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                context = await browser.new_context(
                    user_agent=USER_AGENT,
                    viewport={"width": 1920, "height": 1080},
                )
                await context.add_init_script(STEALTH_SCRIPT)
                page = await context.new_page()

                try:
                    await self._goto_with_retry(page, config.site.company_list_url)
                    companies = await self._collect_companies(page, config, on_progress)

                    if config.filters:
                        companies = [
                            tag_sectors(c, config.filters.sector_keywords)
                            for c in companies
                        ]

                    if config.selectors.detail_page:
                        companies = await self._enrich_with_detail_pages(
                            context, companies, config
                        )
                except Exception as exc:
                    logger.error(f"Scraping error for {config.site.slug}: {exc}")
            finally:
                await browser.close()

        return ScrapedData(
            source=config.site.slug,
            source_name=config.site.name,
            scraped_at=datetime.now(timezone.utc),
            total_companies=len(companies),
            companies=companies,
        )

    async def _goto_with_retry(self, page, url: str):
        delay = 2
        for attempt in range(1, MAX_GOTO_RETRIES + 1):
            try:
                await page.goto(url, wait_until="networkidle", timeout=GOTO_TIMEOUT_MS)
                return
            except PlaywrightTimeoutError:
                logger.warning(
                    f"Timeout loading {url}, attempt {attempt}/{MAX_GOTO_RETRIES}"
                )
                if attempt == MAX_GOTO_RETRIES:
                    raise
                await asyncio.sleep(delay)
                delay *= 2

    async def _parse_element(self, element, config: SiteConfig) -> Optional[Company]:
        try:
            company = await parse_company(
                element, config.selectors.fields, config.site.slug
            )
        except Exception as exc:
            logger.warning(f"Failed to parse company element: {exc}")
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
        self, page, config: SiteConfig, on_progress: Optional[Callable]
    ) -> list[Company]:
        nav = config.navigation
        selectors = config.selectors
        companies: list[Company] = []

        async def parse_all_current_elements() -> list[Company]:
            elements = await page.query_selector_all(selectors.company_container)
            parsed = []
            for element in elements:
                company = await self._parse_element(element, config)
                if company:
                    parsed.append(company)
            return parsed

        if nav.type == NavigationType.PAGINATION:
            for page_num in range(1, nav.max_pages + 1):
                companies.extend(await parse_all_current_elements())
                if on_progress:
                    on_progress(len(companies))

                if not nav.next_button:
                    break
                next_btn = await page.query_selector(nav.next_button)
                if not next_btn:
                    break
                try:
                    await next_btn.click()
                    await page.wait_for_load_state("networkidle", timeout=GOTO_TIMEOUT_MS)
                except Exception as exc:
                    logger.warning(f"Pagination stopped at page {page_num}: {exc}")
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

            companies = await parse_all_current_elements()
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
                    break
                current = await page.query_selector_all(selectors.company_container)
                if len(current) <= seen_count:
                    break
                seen_count = len(current)

            companies = await parse_all_current_elements()
            if on_progress:
                on_progress(len(companies))

        return companies

    async def _enrich_with_detail_pages(
        self, context, companies: list[Company], config: SiteConfig
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
                    await self._goto_with_retry(detail_page, company.detail_url)
                    extra = await extract_fields(detail_page, detail_fields)
                    updates = {
                        key: value
                        for key, value in extra.items()
                        if value is not None and key in company_model_fields
                    }
                    enriched.append(
                        company.model_copy(update=updates) if updates else company
                    )
                except Exception as exc:
                    logger.warning(
                        f"Detail page fetch failed for {company.detail_url}: {exc}"
                    )
                    enriched.append(company)

                await asyncio.sleep(random.uniform(1, 2))
        finally:
            await detail_page.close()

        return enriched
